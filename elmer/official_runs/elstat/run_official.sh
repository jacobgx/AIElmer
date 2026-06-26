#!/usr/bin/env bash
set +e

echo "# Working directory: $(pwd)"
echo "# Command: ElmerGrid 1 2 elmesh"
ElmerGrid 1 2 elmesh
grid_status=$?
echo "# ElmerGrid exit code: ${grid_status}"
echo

echo "# Command: ElmerSolver"
ElmerSolver
solver_status=$?
echo "# ElmerSolver exit code: ${solver_status}"

if (( grid_status != 0 || solver_status != 0 )); then
  exit 1
fi
