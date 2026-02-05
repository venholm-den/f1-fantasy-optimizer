/* global Papa, Plotly */

function byNumericDesc(key) {
  return (a, b) => (Number(b[key]) || 0) - (Number(a[key]) || 0);
}

function pickColumn(rows, candidates) {
  if (!rows?.length) return null;
  const cols = Object.keys(rows[0]);
  for (const c of candidates) {
    const hit = cols.find(k => k.toLowerCase() === c.toLowerCase());
    if (hit) return hit;
  }
  return null;
}

async function fetchCsv(path) {
  const res = await fetch(path, { cache: 'no-store' });
  if (!res.ok) throw new Error(`Failed to fetch ${path}: ${res.status}`);
  const text = await res.text();
  const parsed = Papa.parse(text, { header: true, skipEmptyLines: true });
  if (parsed.errors?.length) {
    // Keep going but surface the first error.
    console.warn('CSV parse warnings:', parsed.errors.slice(0, 3));
  }
  return parsed.data;
}

function renderTable(el, rows, columns) {
  const thead = `<thead><tr>${columns.map(c => `<th>${c}</th>`).join('')}</tr></thead>`;
  const tbody = `<tbody>${rows.map(r => `<tr>${columns.map(c => `<td>${r[c] ?? ''}</td>`).join('')}</tr>`).join('')}</tbody>`;
  el.innerHTML = thead + tbody;
}

function renderBarChart(elId, rows, nameCol, pointsCol, title) {
  const top = [...rows].sort(byNumericDesc(pointsCol)).slice(0, 10);
  const x = top.map(r => r[nameCol]);
  const y = top.map(r => Number(r[pointsCol]) || 0);

  const data = [{
    type: 'bar',
    x,
    y,
    marker: { color: '#7aa2ff' },
    hovertemplate: `%{x}<br>${pointsCol}: %{y}<extra></extra>`,
  }];

  const layout = {
    title: { text: title, font: { color: '#eaf0ff', size: 13 } },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: { l: 40, r: 10, t: 40, b: 90 },
    xaxis: { tickangle: -35, color: '#a8b3d6' },
    yaxis: { color: '#a8b3d6', gridcolor: 'rgba(36,48,88,.4)' },
    font: { color: '#eaf0ff' },
  };

  Plotly.newPlot(elId, data, layout, { displayModeBar: false, responsive: true });
}

async function loadSeason(season) {
  const metaEl = document.getElementById('dataMeta');
  metaEl.textContent = 'Loading…';

  // Public-site data source: read directly from the repo's mycsv/ folder.
  // This avoids copying CSVs into docs/ for manual refresh.
  const RAW_BASE = 'https://raw.githubusercontent.com/venholm-den/f1-fantasy-optimizer/main/mycsv';

  const driverPath = `${RAW_BASE}/f1_official_driver_standings/f1_official_driver_standings${season}.csv`;
  const constructorPath = `${RAW_BASE}/f1_official_constructor_standings/f1_official_constructor_standings${season}.csv`;

  const [drivers, constructors] = await Promise.all([
    fetchCsv(driverPath),
    fetchCsv(constructorPath),
  ]);

  const driverNameCol = pickColumn(drivers, ['driver_name', 'driver', 'name', 'driverName', 'full_name']);
  const driverPointsCol = pickColumn(drivers, ['points', 'pts', 'total_points']);
  const constructorNameCol = pickColumn(constructors, ['constructor_name', 'constructor', 'team', 'name']);
  const constructorPointsCol = pickColumn(constructors, ['points', 'pts', 'total_points']);

  if (!driverNameCol || !driverPointsCol) {
    throw new Error(`Unexpected driver standings columns. Found: ${drivers.length ? Object.keys(drivers[0]).join(', ') : '(none)'}`);
  }
  if (!constructorNameCol || !constructorPointsCol) {
    throw new Error(`Unexpected constructor standings columns. Found: ${constructors.length ? Object.keys(constructors[0]).join(', ') : '(none)'}`);
  }

  // Charts
  renderBarChart('driverChart', drivers, driverNameCol, driverPointsCol, 'Top 10 drivers');
  renderBarChart('constructorChart', constructors, constructorNameCol, constructorPointsCol, 'Top 10 constructors');

  // Tables
  const driverTable = document.getElementById('driverTable');
  const constructorTable = document.getElementById('constructorTable');

  const driverCols = [driverNameCol, driverPointsCol, ...Object.keys(drivers[0]).filter(c => ![driverNameCol, driverPointsCol].includes(c))];
  const constructorCols = [constructorNameCol, constructorPointsCol, ...Object.keys(constructors[0]).filter(c => ![constructorNameCol, constructorPointsCol].includes(c))];

  renderTable(driverTable, drivers.sort(byNumericDesc(driverPointsCol)), driverCols);
  renderTable(constructorTable, constructors.sort(byNumericDesc(constructorPointsCol)), constructorCols);

  const now = new Date();
  metaEl.textContent = `Season ${season} • Loaded ${drivers.length} drivers, ${constructors.length} constructors • ${now.toISOString()}`;
}

function init() {
  const seasonSelect = document.getElementById('seasonSelect');
  const reloadBtn = document.getElementById('reloadBtn');

  async function go() {
    try {
      await loadSeason(seasonSelect.value);
    } catch (err) {
      console.error(err);
      document.getElementById('dataMeta').textContent = `Error: ${err.message}`;
    }
  }

  reloadBtn.addEventListener('click', go);
  seasonSelect.addEventListener('change', go);
  go();
}

document.addEventListener('DOMContentLoaded', init);
