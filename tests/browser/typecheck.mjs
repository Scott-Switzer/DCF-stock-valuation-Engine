// Compile the one tracked experimental TS module in isolation. This is a type
// check, not numerical parity or evidence that the module ships in production.
import { readFile, writeFile, mkdtemp, rm } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const directory = await mkdtemp(new URL('./.typecheck-', import.meta.url));
try {
  const source = await readFile(new URL('../../frontend/src/lib/dcf-engine.ts', import.meta.url));
  const path = `${directory}/dcf-engine.ts`;
  await writeFile(path, source);
  const result = spawnSync(process.execPath, [fileURLToPath(new URL('./node_modules/typescript/bin/tsc', import.meta.url)), '--noEmit', '--strict', '--esModuleInterop', '--target', 'ES2020', '--module', 'commonjs', '--moduleResolution', 'node', path], {stdio:'inherit'});
  process.exitCode = result.status ?? 1;
} finally { await rm(directory, {recursive:true, force:true}); }
