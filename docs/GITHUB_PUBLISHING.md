# GitHub Publishing Guide

This project contains local experiments and large solver outputs. Publish the clean framework, not the whole working directory.

## Option A: Publish From This Root

1. Review `.gitignore`.
2. Confirm large files are ignored:

   ```powershell
   git status --ignored
   ```

3. Commit only framework files:

   ```powershell
   git add README.md LICENSE.md .gitignore .gitattributes docs knowledge templates scripts/query_kb.ps1 scripts/new_elmer_case.ps1 scripts/check_elmer_case.ps1 scripts/distill_sif_tests.py scripts/prepare_github_share.ps1 elmer/README.md
   git commit -m "Publish Elmer AI modeling knowledge-base framework"
   ```

## Option B: Export A Clean Share Directory

Run:

```powershell
.\scripts\prepare_github_share.ps1
```

This creates:

```text
dist/github/ElmerFEM-AI-KB/
```

Then initialize Git inside that exported directory.

## Do Not Publish By Default

- COMSOL `.mph` files
- Generated Elmer meshes and VTU fields
- Logs and raw result folders
- `tmp/elmerfem_remote_tree/`
- Personal remote-run scripts or machine-specific paths

## Suggested Repository Description

AI-ready ElmerFEM modeling knowledge-base framework with case contracts, syntax evidence workflow, official-example distillation plan, and reusable model scaffolds.
