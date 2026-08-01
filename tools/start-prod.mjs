// Single-server mode: builds the frontend, then starts ONE backend
// process (no --reload) that serves the API and the built frontend
// together on http://localhost:8000. Fewer moving parts than `npm run
// dev` -- recommended for defense day, not for active editing (no hot
// reload; re-run this after any frontend change).
//
// Run via `npm start` from the project root.
import { spawn, spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const winPython = path.join(root, 'backend', 'venv', 'Scripts', 'python.exe')
const nixPython = path.join(root, 'backend', 'venv', 'bin', 'python')
const python = existsSync(winPython) ? winPython : existsSync(nixPython) ? nixPython : null

if (!python) {
  console.error(
    '\nNo virtual environment found at backend/venv.\n' +
    'Run `npm run install:all` first (see docs/SETUP.md), then `npm start` again.\n'
  )
  process.exit(1)
}

console.log('\n> Building frontend (frontend/dist)...')
const build = spawnSync('npm', ['run', 'build', '--prefix', 'frontend'], {
  cwd: root,
  stdio: 'inherit',
  shell: process.platform === 'win32',
})
if (build.status !== 0) {
  console.error('\nFrontend build failed -- fix the error above, then run `npm start` again.')
  process.exit(build.status ?? 1)
}

console.log('\n> Starting server on http://localhost:8000 ...')
const server = spawn(
  python,
  ['-m', 'uvicorn', 'main:app', '--port', '8000', '--app-dir', 'backend/app'],
  { cwd: root, stdio: 'inherit' }
)
server.on('exit', (code) => process.exit(code ?? 1))
