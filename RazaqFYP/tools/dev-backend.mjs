// Launches the backend dev server (uvicorn, with --reload) using the
// project's own virtual environment interpreter directly -- e.g.
// backend/venv/Scripts/python.exe on Windows, backend/venv/bin/python
// on macOS/Linux. This sidesteps `venv\Scripts\activate`, which only
// affects the current shell and does not reliably carry into a child
// process spawned by `concurrently` (this was a real source of
// confusion in earlier manual two-terminal setup).
//
// Run via `npm run dev` (from the project root) -- not meant to be run
// directly.
import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const winPython = path.join(root, 'backend', 'venv', 'Scripts', 'python.exe')
const nixPython = path.join(root, 'backend', 'venv', 'bin', 'python')
const python = existsSync(winPython) ? winPython : existsSync(nixPython) ? nixPython : null

if (!python) {
  console.error(
    '\n[dev:backend] No virtual environment found at backend/venv.\n' +
    'One-time setup needed first -- see docs/SETUP.md "PHASE 3 - Backend server", ' +
    'step 1, then run `npm run dev` again.\n'
  )
  process.exit(1)
}

const child = spawn(
  python,
  ['-m', 'uvicorn', 'main:app', '--reload', '--port', '8000', '--app-dir', 'backend/app'],
  { cwd: root, stdio: 'inherit' }
)

child.on('exit', (code) => process.exit(code ?? 1))
