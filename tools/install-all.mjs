// One-time convenience installer: installs frontend node_modules and
// backend pip packages (into the existing venv). Does NOT create the
// venv itself -- that's a one-time step tied to a specific Python
// version (see docs/SETUP.md), not something safe to guess at
// automatically on someone else's machine.
//
// Run via `npm run install:all` from the project root.
import { spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const winPython = path.join(root, 'backend', 'venv', 'Scripts', 'python.exe')
const nixPython = path.join(root, 'backend', 'venv', 'bin', 'python')
const python = existsSync(winPython) ? winPython : existsSync(nixPython) ? nixPython : null

function run(command, args, cwd) {
  console.log(`\n> ${command} ${args.join(' ')}  (in ${cwd})`)
  const result = spawnSync(command, args, { cwd, stdio: 'inherit', shell: process.platform === 'win32' })
  if (result.status !== 0) {
    console.error(`\nCommand failed: ${command} ${args.join(' ')}`)
    process.exit(result.status ?? 1)
  }
}

if (!python) {
  console.error(
    '\nNo virtual environment found at backend/venv yet.\n' +
    'Create it first (one-time, see docs/SETUP.md "PHASE 3 - Backend server", step 1):\n\n' +
    '    cd backend\n' +
    '    <your Python 3.11 path> -m venv venv\n' +
    '    cd ..\n\n' +
    'Then run `npm run install:all` again.\n'
  )
  process.exit(1)
}

run('npm', ['install'], root)
run('npm', ['install', '--prefix', 'frontend'], root)
run(python, ['-m', 'pip', 'install', '-r', path.join('backend', 'requirements.txt')], root)

console.log(
  '\nAll dependencies installed.\n' +
  'If you have not already, copy backend/.env.example to backend/.env and set HANS_DB_PASSWORD.\n' +
  'Then run `npm run dev`.\n'
)
