#!/usr/bin/env bash
set -u

export PATH=/opt/elmer-26.2/bin:$PATH

{
  echo "# fsi_beam run started $(date -Is)"
  echo "$ pwd"
  pwd
  echo
  echo "$ command -v elmerf90 ElmerGrid ElmerSolver"
  command -v elmerf90
  command -v ElmerGrid
  command -v ElmerSolver
  echo
  echo "$ elmerf90 FsiStuff.f90 -o FsiStuff"
  elmerf90 FsiStuff.f90 -o FsiStuff
  compile_status=$?
  echo "# compile exit code: ${compile_status}"
  if [ "${compile_status}" -ne 0 ]; then
    exit "${compile_status}"
  fi
  echo
  echo "$ ElmerGrid 1 2 fsi"
  ElmerGrid 1 2 fsi
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
  echo "# fsi_beam run finished $(date -Is)"
  exit "${solver_status}"
} 2>&1 | tee run.log
