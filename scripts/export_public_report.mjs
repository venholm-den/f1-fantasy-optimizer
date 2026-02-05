#!/usr/bin/env node
/**
 * Copy season exports into docs/ so GitHub Pages can serve them.
 *
 * Usage:
 *   node scripts/export_public_report.mjs --season 2025
 */

import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '..');

const FILES = [
  'f1_official_driver_standings.csv',
  'f1_official_constructor_standings.csv',
  'f1_official_driver_race_points.csv',
  'f1_official_constructor_race_points.csv',
  'dim_round.csv',
  'dim_round_dates.csv',
];

function argValue(name, fallback) {
  const idx = process.argv.indexOf(name);
  if (idx === -1) return fallback;
  const v = process.argv[idx + 1];
  if (!v || v.startsWith('--')) return fallback;
  return v;
}

const season = argValue('--season', '2025');
const srcDir = path.join(repoRoot, 'data', 'seasons', String(season), 'raw');
const outDir = path.join(repoRoot, 'docs', 'data', String(season));

async function exists(p) {
  try {
    await fs.access(p);
    return true;
  } catch {
    return false;
  }
}

if (!(await exists(srcDir))) {
  console.error(`Source directory not found: ${srcDir}`);
  process.exit(1);
}

await fs.mkdir(outDir, { recursive: true });

const copied = [];
const missing = [];

for (const name of FILES) {
  const src = path.join(srcDir, name);
  const dst = path.join(outDir, name);
  if (!(await exists(src))) {
    missing.push(name);
    continue;
  }
  await fs.copyFile(src, dst);
  copied.push(name);
}

console.log(`Exported season ${season} to ${outDir}`);
if (copied.length) {
  console.log('Copied:');
  for (const n of copied) console.log(`  - ${n}`);
}
if (missing.length) {
  console.log('Missing (skipped):');
  for (const n of missing) console.log(`  - ${n}`);
}
