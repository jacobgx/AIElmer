# Distilled Elmer Knowledge

This directory is reserved for AI-ready distilled knowledge extracted from official Elmer sources, local validated cases, and project-specific evidence.

The files here should be small, structured, and traceable. Do not place raw VTU fields, solver logs, large meshes, or full upstream source trees here.

## Planned Structure

```text
distilled/
├── manifest.example.yaml
├── source_snapshots/
├── keyword_index/
├── solver_index/
├── test_case_index/
├── physics_cards/
├── coupling_cards/
├── troubleshooting/
└── prompts/
```

## Quality States

- `RAW`: collected but not parsed.
- `INDEXED`: machine-readable index exists.
- `EVIDENCED`: source paths and version/commit evidence are recorded.
- `RUNNABLE`: a minimal local run has completed.
- `VALIDATED_TEMPLATE`: run completed and checks passed.
- `DEPRECATED`: no longer recommended for new modeling.

See `knowledge/ELMER_KB_DISTILLATION_PLAN.md` for the full distillation workflow.
