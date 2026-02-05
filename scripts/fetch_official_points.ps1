param(
  [int[]]$Seasons = @(2023, 2024, 2025),
  [ValidateSet('race','standings','both')] [string]$Mode = 'both'
)

$ErrorActionPreference = 'Stop'

$baseUrls = @(
  'https://api.jolpi.ca/ergast',
  'https://ergast.com/mrd'
)

function Get-Json($path, $params = @{}) {
  $last = $null
  foreach ($base in $baseUrls) {
    $u = ($base.TrimEnd('/') + '/' + $path.TrimStart('/'))
    if ($params.Count -gt 0) {
      $qs = ($params.GetEnumerator() | ForEach-Object { "{0}={1}" -f $_.Key, [uri]::EscapeDataString([string]$_.Value) }) -join '&'
      $u = $u + '?' + $qs
    }
    try {
      # Be gentle: avoid triggering upstream rate limits / WAF behaviour.
      Start-Sleep -Milliseconds 200
      return Invoke-RestMethod -Uri $u -Headers @{
        'Accept'='application/json'
        'User-Agent'='openclaw-f1-fantasy-optimizer/1.0'
      } -TimeoutSec 60
    } catch {
      $last = $_
    }
  }
  throw "Failed to fetch $path : $last"
}

function ConstructorIdToFantasyAbbr([string]$constructorId) {
  switch ($constructorId) {
    'red_bull' { 'RED' }
    'mercedes' { 'MER' }
    'ferrari' { 'FER' }
    'mclaren' { 'MCL' }
    'aston_martin' { 'AST' }
    'alpine' { 'ALP' }
    'haas' { 'HAA' }
    'williams' { 'WIL' }
    'rb' { 'VRB' }
    'toro_rosso' { 'VRB' }
    'alpha_tauri' { 'VRB' }
    'sauber' { 'KCK' }
    'alfa' { 'KCK' }
    'alfa_romeo' { 'KCK' }
    default { '' }
  }
}

function Get-Rounds([int]$season) {
  $j = Get-Json "/f1/$season.json" @{ limit = 1000 }
  $races = $j.MRData.RaceTable.Races
  return $races | ForEach-Object {
    [pscustomobject]@{
      season  = [int]$_.season
      round   = [int]$_.round
      raceName= [string]$_.raceName
    }
  }
}

$root = Split-Path -Parent $PSScriptRoot

foreach ($season in $Seasons) {
  $rawDir = Join-Path $root ("data/seasons/$season/raw")
  New-Item -ItemType Directory -Force -Path $rawDir | Out-Null

  $rounds = Get-Rounds $season

  if ($Mode -in @('race','both')) {
    $driverRows = @()
    $constructorAggRows = @()

    foreach ($rd in $rounds) {
      Write-Host "[$season] race points: round $($rd.round) - $($rd.raceName)"
      $j = Get-Json "/f1/$season/$($rd.round)/results.json" @{ limit = 1000 }
      $races = $j.MRData.RaceTable.Races
      if (-not $races -or $races.Count -eq 0) { continue }
      $results = $races[0].Results

      $cPoints = @{}
      $cName = @{}

      foreach ($res in $results) {
        $pts = [double]($res.points)
        $drv = $res.Driver
        $con = $res.Constructor
        $cid = [string]$con.constructorId

        $driverRows += [pscustomobject]@{
          season = $season
          round = [int]$rd.round
          raceName = $rd.raceName
          position = [string]$res.position
          points = $pts
          driverAbbr = ([string]$drv.code).ToUpper()
          ergast_driver_id = [string]$drv.driverId
          driver_givenName = [string]$drv.givenName
          driver_familyName = [string]$drv.familyName
          constructorCode = $cid
          constructorAbbr = (ConstructorIdToFantasyAbbr $cid)
          constructor_name = [string]$con.name
        }

        if (-not $cPoints.ContainsKey($cid)) { $cPoints[$cid] = 0.0 }
        $cPoints[$cid] += $pts
        $cName[$cid] = [string]$con.name
      }

      foreach ($cid in $cPoints.Keys) {
        $constructorAggRows += [pscustomobject]@{
          season = $season
          round = [int]$rd.round
          raceName = $rd.raceName
          points = [double]$cPoints[$cid]
          constructorCode = $cid
          constructorAbbr = (ConstructorIdToFantasyAbbr $cid)
          constructor_name = $cName[$cid]
        }
      }
    }

    $driverRows | Export-Csv -NoTypeInformation -Encoding utf8 (Join-Path $rawDir 'f1_official_driver_race_points.csv')
    $constructorAggRows | Export-Csv -NoTypeInformation -Encoding utf8 (Join-Path $rawDir 'f1_official_constructor_race_points.csv')
  }

  if ($Mode -in @('standings','both')) {
    $driverStand = @()
    $constructorStand = @()

    foreach ($rd in $rounds) {
      Write-Host "[$season] standings: round $($rd.round) - $($rd.raceName)"
      $d = Get-Json "/f1/$season/$($rd.round)/driverStandings.json" @{ limit = 1000 }
      $c = Get-Json "/f1/$season/$($rd.round)/constructorStandings.json" @{ limit = 1000 }

      $dl = $d.MRData.StandingsTable.StandingsLists
      if ($dl.Count -gt 0) {
        foreach ($row in $dl[0].DriverStandings) {
          $drv = $row.Driver
          $con0 = $row.Constructors[0]
          $cid = [string]$con0.constructorId
          $driverStand += [pscustomobject]@{
            season = $season
            round = [int]$rd.round
            raceName = $rd.raceName
            position = [string]$row.position
            points = [double]$row.points
            wins = [int]$row.wins
            driverAbbr = ([string]$drv.code).ToUpper()
            ergast_driver_id = [string]$drv.driverId
            driver_givenName = [string]$drv.givenName
            driver_familyName = [string]$drv.familyName
            constructorCode = $cid
            constructorAbbr = (ConstructorIdToFantasyAbbr $cid)
            constructor_name = [string]$con0.name
          }
        }
      }

      $cl = $c.MRData.StandingsTable.StandingsLists
      if ($cl.Count -gt 0) {
        foreach ($row in $cl[0].ConstructorStandings) {
          $con = $row.Constructor
          $cid = [string]$con.constructorId
          $constructorStand += [pscustomobject]@{
            season = $season
            round = [int]$rd.round
            raceName = $rd.raceName
            position = [string]$row.position
            points = [double]$row.points
            wins = [int]$row.wins
            constructorCode = $cid
            constructorAbbr = (ConstructorIdToFantasyAbbr $cid)
            constructor_name = [string]$con.name
          }
        }
      }
    }

    $driverStand | Export-Csv -NoTypeInformation -Encoding utf8 (Join-Path $rawDir 'f1_official_driver_standings.csv')
    $constructorStand | Export-Csv -NoTypeInformation -Encoding utf8 (Join-Path $rawDir 'f1_official_constructor_standings.csv')
  }

  Write-Host "Wrote official points for $season to $rawDir"
}
