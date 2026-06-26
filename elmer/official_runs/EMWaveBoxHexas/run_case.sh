#!/usr/bin/env bash
set -u

export PATH=/opt/elmer-26.2/bin:$PATH

{
  echo "# EMWaveBoxHexas run started $(date -Is)"
  echo "$ pwd"
  pwd
  echo
  echo "$ command -v ElmerGrid ElmerSolver"
  command -v ElmerGrid
  command -v ElmerSolver
  echo
  echo "$ ElmerGrid 1 2 shoebox_hexas"
  ElmerGrid 1 2 shoebox_hexas
  grid_status=$?
  echo "# grid exit code: ${grid_status}"
  if [ "${grid_status}" -ne 0 ]; then
    exit "${grid_status}"
  fi
  echo
  echo "$ ElmerSolver"
  ElmerSolver
  solver_status=$?
  echo "# solver exit code: ${solver_status}"
  echo "# EMWaveBoxHexas run finished $(date -Is)"
  exit "${solver_status}"
} 2>&1 | tee run.log
