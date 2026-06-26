#!/usr/bin/env bash
set -u

{
  echo "# Environment captured $(date -Is)"
  echo
  echo "$ wsl -d <WSL-distro> -- ElmerSolver --version"
  ElmerSolver --version
  echo
  echo "$ wsl -d <WSL-distro> -- ElmerGrid --version"
  ElmerGrid --version
  echo
  echo "$ export PATH=/opt/elmer-26.2/bin:\$PATH"
  export PATH=/opt/elmer-26.2/bin:$PATH
  echo "$ command -v elmerf90"
  command -v elmerf90 || true
  echo
  echo "$ elmerf90 --help"
  elmerf90 --help 2>&1 | head -80 || true
  echo
  echo "$ gfortran --version"
  gfortran --version 2>&1 | head -5 || true
} 2>&1 | tee logs/environment.log
