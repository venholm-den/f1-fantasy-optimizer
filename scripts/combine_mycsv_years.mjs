#!/usr/bin/env node
/**
 * Combine year-suffixed CSV exports in mycsv/ into single files.
 *
 * Example input:
 *   mycsv/f1_official_driver_standings/f1_official_driver_standings2023.csv
 *   mycsv/f1_official_driver_standings/f1_official_driver_standings2024.csv
 *   mycsv/f1_official_driver_standings/f1_official_driver_standings2025.csv
 *
 * Output:
 *   mycsv/f1_official_driver_standings/f1_official_driver_standings.csv
 *
 * Keeps per-year files and writes/overwrites the combined file.
 *
 * Usage:
 *   node scripts/combine_mycsv_years.mjs
 *   node scripts/combine_mycsv_years.mjs --dry-run
 *   node scripts/combine_mycsv_years.mjs --table f1_official_driver_standings
 */

import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const YEAR_SUFFIX_RE = /^(?<base>.+?)(?<year>20\d\d)\.csv$/i;

function parseArgs(argv) {
  const out = { dryRun: false, table: null };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--dry-run') out.dryRun = true;
    else if (a === '--table') out.table = argv[++i];
  }
  return out;
}

function stripBom(s) {
  return s.charCodeAt(0) === 0xfeff ? s.slice(1) : s;
}

function splitLines(s) {
  // We assume these CSVs don't contain embedded newlines inside quoted fields.
  // (true for our generated exports)
  return s.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n');
}

async function listYearFiles(tableDir) {
  const entries = await fs.readdir(tableDir, { withFileTypes: true });
  const files = [];
  for (const e of entries) {
    if (!e.isFile()) continue;
    if (!e.name.toLowerCase().endsWith('.csv')) continue;
    const m = e.name.match(YEAR_SUFFIX_RE);
    if (!m) continue;
    files.push({ year: Number(m.groups.year), name: e.name, base: m.groups.base });
  }
  files.sort((a, b) => a.year - b.year);
  return files;
}

async function combineTable(tableDir, files, { dryRun }) {
  const base = files[0].base;
  const outPath = path.join(tableDir, `${base}.csv`);

  const contents = [];
  for (const f of files) {
    const p = path.join(tableDir, f.name);
    const raw = await fs.readFile(p, 'utf8');
    const text = stripBom(raw);
    const lines = splitLines(text).filter((l) => l.length > 0);
    if (lines.length === 0) continue;
    contents.push({ name: f.name, header: lines[0], rows: lines.slice(1) });
  }

  if (contents.length === 0) return;

  const header0 = contents[0].header;
  for (const c of contents.slice(1)) {
    if (c.header !== header0) {
      throw new Error(
        `Header mismatch while combining ${path.basename(tableDir)}\n` +
          `  - ${contents[0].name}: ${header0}\n` +
          `  - ${c.name}: ${c.header}`
      );
    }
  }

  const outLines = [header0];
  for (const c of contents) outLines.push(...c.rows);
  const outText = outLines.join('\n') + '\n';

  if (dryRun) {
    console.log(`[dry-run] Would write ${outPath} from ${contents.length} files`);
    for (const c of contents) console.log(`  - ${c.name}`);
    return;
  }

  await fs.writeFile(outPath, outText, 'utf8');
  console.log(`Wrote ${outPath} (${contents.length} inputs)`);
}

async function main() {
  const args = parseArgs(process.argv);
  const __filename = fileURLToPath(import.meta.url);
  const __dirname = path.dirname(__filename);
  const repoRoot = path.resolve(__dirname, '..');
  const mycsvDir = path.join(repoRoot, 'mycsv');

  const tableDirs = [];
  if (args.table) {
    tableDirs.push(path.join(mycsvDir, args.table));
  } else {
    const entries = await fs.readdir(mycsvDir, { withFileTypes: true });
    for (const e of entries) {
      if (e.isDirectory()) tableDirs.push(path.join(mycsvDir, e.name));
    }
  }

  tableDirs.sort();
  for (const td of tableDirs) {
    const files = await listYearFiles(td);
    if (files.length === 0) continue;
    await combineTable(td, files, { dryRun: args.dryRun });
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
