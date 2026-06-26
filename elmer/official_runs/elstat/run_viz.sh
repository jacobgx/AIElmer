#!/usr/bin/env bash
set +e

echo "# Working directory: $(pwd)"
echo "# Command: ElmerSolver elstatics_viz.sif"
ElmerSolver elstatics_viz.sif
solver_status=$?
echo "# ElmerSolver exit code: ${solver_status}"
exit "${solver_status}"
