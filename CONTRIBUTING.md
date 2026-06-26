# Contributing

Contributions are welcome — case additions, knowledge-base expansions, script improvements, and bug fixes.

## Scope

This repository is a knowledge-base framework, not a solver distribution. Good contributions include:

- New Elmer case directories with auditable documentation
- Distilled knowledge cards (physics, solver, keyword)
- Improved scripts for case creation, checking, and postprocessing
- Corrections to existing SIF files, formulations, or evidence

## Workflow

1. **Fork** the repository and create a feature branch.
2. **For new cases:** use `scripts/new_elmer_case.ps1` to scaffold, then follow the 8-gate workflow in `knowledge/ELMER_AI_MODELING_STANDARD.md`.
3. **For knowledge additions:** place distilled cards under `knowledge/distilled/` and update the relevant index.
4. **Run `scripts/check_elmer_case.ps1`** on your case directory before committing.
5. **Open a pull request** with a description of what was changed and why.

## Style

- SIF files: follow `knowledge/CODING_STANDARD.md`.
- Commit messages: use present tense ("Add cylinder-flow species case", not "Added …").
- Do not commit solver outputs (`*.vtu`, `*.result`, `*.log`, `*.mph`, `*.gif`, raw result archives).

## AI-Assisted Contributions

Contributions created with AI assistance must include:

- `formulation.md` — physical equations, assumptions, and boundary conditions
- `syntax_evidence.md` — SIF keyword sources with upstream commit references
- A validation plan with pass/fail criteria

See `docs/AI_AGENT_GUIDE.md` for the full AI modeling protocol.

## License

By contributing, you agree that your work will be licensed under the same MIT License that covers the framework. Upstream Elmer-derived content retains its original license.
