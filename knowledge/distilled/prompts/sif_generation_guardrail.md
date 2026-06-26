# SIF Generation Guardrail Prompt

Before writing a SIF file, follow this checklist:

1. State the physical equations and assumptions.
2. Identify the Elmer Solver, Procedure, variable names, and DOFs.
3. Cite at least one official or validated local case for syntax.
4. Cite `SOLVER.KEYWORDS` or solver source evidence for non-obvious keywords.
5. Confirm mesh dimension and boundary IDs.
6. Generate the smallest runnable SIF first.
7. Mark the case `NOT VALIDATED` until validation checks pass.
