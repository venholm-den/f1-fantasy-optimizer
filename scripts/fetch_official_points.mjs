#!/usr/bin/env node
/**
 * Fetch official F1 points (drivers + constructors) from Ergast/Jolpica and
 * emit CSVs under data/seasons/<season>/raw/.
 *
 * This is a Node implementation so the repo can generate the files even when
 * Python isn't available on PATH.
 *
 * Usage:
 *   node scripts/fetch_official_points.mjs --season 2025
 *   node scripts/fetch_official_points.mjs --season 2023 --mode race
 *   node scripts/fetch_official_points.mjs --seasons 2023,2024,2025
 */

import fs from 'node:fs/promises';
import path from 'node:path';

const BASE_URLS = [
  'https://api.jolpi.ca/ergast',
  'https://ergast.com/mrd',
];

function parseArgs(argv) {
  const out = { mode: 'both' };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--season') out.season = Number(argv[++i]);
    else if (a === '--seasons') out.seasons = String(argv[++i]).split(',').map(s => Number(s.trim())).filter(Boolean);
    else if (a === '--mode') out.mode = String(argv[++i]);
    else if (a === '--help' || a === '-h') out.help = true;
  }
  return out;
}

async function fetchJson(relPath, params = {}) {
  let lastErr;
  for (const base of BASE_URLS) {
    const url = new URL(base.replace(/\/$/, '') + '/' + relPath.replace(/^\//, ''));
    for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
    try {
      const res = await fetch(url, { method: 'GET' });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      return await res.json();
    } catch (e) {
      lastErr = e;
    }
  }
  throw new Error(`Failed to fetch ${relPath}: ${lastErr}`);
}

function csvEscape(v) {
  if (v === null || v === undefined) return '';
  const s = String(v);
  if (/[",\n\r]/.test(s)) return '"' + s.replace(/"/g, '""') + '"';
  return s;
}

async function writeCsv(filePath, rows, fieldnames) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  const lines = [];
  lines.push(fieldnames.join(','));
  for (const r of rows) {
    lines.push(fieldnames.map(f => csvEscape(r[f])).join(','));
  }
  await fs.writeFile(filePath, lines.join('\n') + '\n', 'utf8');
}

function constructorIdToFantasyAbbr(constructorId) {
  const m = {
    red_bull: 'RED',
    mercedes: 'MER',
    ferrari: 'FER',
    mclaren: 'MCL',
    aston_martin: 'AST',
    alpine: 'ALP',
    haas: 'HAA',
    williams: 'WIL',
    rb: 'VRB',
    toro_rosso: 'VRB',
    alpha_tauri: 'VRB',
    sauber: 'KCK',
    alfa: 'KCK',
    alfa_romeo: 'KCK',
  };
  return m[String(constructorId || '').trim()] || '';
}

async function getRounds(season) {
  const data = await fetchJson(`/f1/${season}.json`, { limit: 1000 });
  const races = data?.MRData?.RaceTable?.Races || [];
  return races.map(r => ({
    season: Number(r.season),
    round: Number(r.round),
    raceName: r.raceName || '',
  }));
}

async function fetchRacePoints(season) {
  const rounds = await getRounds(season);
  const driverRows = [];
  const constructorRows = [];

  for (const rd of rounds) {
    const data = await fetchJson(`/f1/${season}/${rd.round}/results.json`, { limit: 1000 });
    const races = data?.MRData?.RaceTable?.Races || [];
    if (!races.length) continue;
    const results = races[0].Results || [];

    const cPoints = new Map();
    const cMeta = new Map();

    for (const res of results) {
      const drv = res.Driver || {};
      const con = res.Constructor || {};
      const pts = Number(res.points || 0);
      const constructorCode = (con.constructorId || '').trim();

      driverRows.push({
        season,
        round: rd.round,
        raceName: rd.raceName,
        position: res.position || '',
        points: pts,
        driverAbbr: (drv.code || '').trim().toUpperCase(),
        ergast_driver_id: (drv.driverId || '').trim(),
        driver_givenName: drv.givenName || '',
        driver_familyName: drv.familyName || '',
        constructorCode,
        constructorAbbr: constructorIdToFantasyAbbr(constructorCode),
        constructor_name: con.name || '',
      });

      if (constructorCode) {
        cPoints.set(constructorCode, (cPoints.get(constructorCode) || 0) + pts);
        cMeta.set(constructorCode, { constructor_name: con.name || '' });
      }
    }

    for (const [constructorCode, pts] of [...cPoints.entries()].sort((a, b) => b[1] - a[1])) {
      const meta = cMeta.get(constructorCode) || {};
      constructorRows.push({
        season,
        round: rd.round,
        raceName: rd.raceName,
        points: pts,
        constructorCode,
        constructorAbbr: constructorIdToFantasyAbbr(constructorCode),
        constructor_name: meta.constructor_name || '',
      });
    }
  }

  return { driverRows, constructorRows };
}

async function fetchStandings(season) {
  const rounds = await getRounds(season);
  const driverRows = [];
  const constructorRows = [];

  for (const rd of rounds) {
    const d = await fetchJson(`/f1/${season}/${rd.round}/driverStandings.json`, { limit: 1000 });
    const c = await fetchJson(`/f1/${season}/${rd.round}/constructorStandings.json`, { limit: 1000 });

    const dlists = d?.MRData?.StandingsTable?.StandingsLists || [];
    const clists = c?.MRData?.StandingsTable?.StandingsLists || [];

    if (dlists.length) {
      for (const row of (dlists[0].DriverStandings || [])) {
        const drv = row.Driver || {};
        const cons = row.Constructors || [];
        const con0 = cons[0] || {};
        const constructorCode = (con0.constructorId || '').trim();
        driverRows.push({
          season,
          round: rd.round,
          raceName: rd.raceName,
          position: row.position || '',
          points: Number(row.points || 0),
          wins: Number(row.wins || 0),
          driverAbbr: (drv.code || '').trim().toUpperCase(),
          ergast_driver_id: (drv.driverId || '').trim(),
          driver_givenName: drv.givenName || '',
          driver_familyName: drv.familyName || '',
          constructorCode,
          constructorAbbr: constructorIdToFantasyAbbr(constructorCode),
          constructor_name: con0.name || '',
        });
      }
    }

    if (clists.length) {
      for (const row of (clists[0].ConstructorStandings || [])) {
        const con = row.Constructor || {};
        const constructorCode = (con.constructorId || '').trim();
        constructorRows.push({
          season,
          round: rd.round,
          raceName: rd.raceName,
          position: row.position || '',
          points: Number(row.points || 0),
          wins: Number(row.wins || 0),
          constructorCode,
          constructorAbbr: constructorIdToFantasyAbbr(constructorCode),
          constructor_name: con.name || '',
        });
      }
    }
  }

  return { driverRows, constructorRows };
}

async function runSeason(season, mode) {
  const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
  const rawDir = path.join(root, 'data', 'seasons', String(season), 'raw');

  if (mode === 'race' || mode === 'both') {
    const { driverRows, constructorRows } = await fetchRacePoints(season);
    await writeCsv(
      path.join(rawDir, 'f1_official_driver_race_points.csv'),
      driverRows,
      ['season','round','raceName','position','points','driverAbbr','ergast_driver_id','driver_givenName','driver_familyName','constructorCode','constructorAbbr','constructor_name']
    );
    await writeCsv(
      path.join(rawDir, 'f1_official_constructor_race_points.csv'),
      constructorRows,
      ['season','round','raceName','points','constructorCode','constructorAbbr','constructor_name']
    );
  }

  if (mode === 'standings' || mode === 'both') {
    const { driverRows, constructorRows } = await fetchStandings(season);
    await writeCsv(
      path.join(rawDir, 'f1_official_driver_standings.csv'),
      driverRows,
      ['season','round','raceName','position','points','wins','driverAbbr','ergast_driver_id','driver_givenName','driver_familyName','constructorCode','constructorAbbr','constructor_name']
    );
    await writeCsv(
      path.join(rawDir, 'f1_official_constructor_standings.csv'),
      constructorRows,
      ['season','round','raceName','position','points','wins','constructorCode','constructorAbbr','constructor_name']
    );
  }

  return rawDir;
}

async function main() {
  const args = parseArgs(process.argv);
  if (args.help || (!args.season && !args.seasons)) {
    console.log('Usage: node scripts/fetch_official_points.mjs --season 2025 [--mode race|standings|both]');
    console.log('       node scripts/fetch_official_points.mjs --seasons 2023,2024,2025 [--mode race|standings|both]');
    process.exit(0);
  }

  const seasons = args.seasons?.length ? args.seasons : [args.season];
  for (const s of seasons) {
    const outDir = await runSeason(s, args.mode);
    console.log(`Wrote official points CSVs for ${s} to ${outDir}`);
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
