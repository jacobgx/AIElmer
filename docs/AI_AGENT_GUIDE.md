# AI Agent Guide

Use this guide when an AI agent opens the repository for the first time.

## First Read

Read these files before editing or generating an Elmer model:

1. `knowledge/ELMER_AI_MODELING_STANDARD.md`
2. `knowledge/ELMER_KB_DISTILLATION_PLAN.md`
3. `knowledge/ELMER_QUICKREF.md`
4. `templates/elmer_case/README.md`

## Modeling Protocol

1. Restate the physical objective, known inputs, unknown inputs, and requested outputs.
2. Create a case scaffold with `scripts/new_elmer_case.ps1`.
3. Treat `model_spec.yaml` as the source of truth for parameters.
4. Fill `formulation.md` before writing the final SIF.
5. Record non-obvious SIF syntax in `syntax_evidence.md`.
6. Verify mesh boundary IDs before using `Target Boundaries`.
7. Run a minimal single-core MVP before adding coupled physics or large meshes.
8. Do not label a result `VALIDATED` until the validation plan passes.

## Evidence Priority

Use evidence in this order:

1. The installed Elmer source and tests for the same runtime version.
2. Official Elmer GitHub test cases and source code with commit IDs.
3. This repository's validated local cases.
4. Official manuals and release notes.
5. Forum or web material only as supplemental evidence.

## Required Answer Before Writing SIF

Before generating or modifying a SIF file, answer:

- Which physical equations are being solved?
- Which Solver and Procedure names will be used?
- Which variables and DOFs are expected?
- Which material and boundary keywords are required?
- Which official or local case proves the syntax?
- Which mesh boundary IDs have been verified?
- What is the current validation state?

## Forbidden Shortcuts

- Do not infer equations from GUI module names alone.
- Do not silently invent missing material values.
- Do not use convergence as proof of correctness.
- Do not tune material, boundary, or stabilization parameters merely to match a target plot.
- Do not use postprocessing clipping to hide numerical instability.
