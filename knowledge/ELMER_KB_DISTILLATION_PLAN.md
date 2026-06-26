# Elmer 知识库蒸馏方案

版本：1.0  
目标：把 Elmer 官方源码、测试案例、文档、项目内已验证案例蒸馏成 AI 建模时可快速检索、可引用、可验证的本地知识库。

## 1. 蒸馏目标

知识库不追求替代官方文档，而是服务 AI 建模的四个高频动作：

1. 从物理问题快速定位可用 Solver、变量、材料参数和边界条件。
2. 写 SIF 前查到当前版本的关键字证据，避免凭记忆生成过期语法。
3. 从官方测试案例中找到最小可运行模板，并能追溯到原始路径和 commit。
4. 在调试失败时区分语法、网格、线性求解、非线性求解和物理设置问题。

最终产物应做到：每条建议都有证据路径，每个模板都能最小运行，每次引用都记录 Elmer 版本或 commit。

## 2. 原始来源分级

### S0：当前安装版本

- WSL 源码：`/opt/src/elmerfem`
- WSL 运行时：`/opt/elmer-26.2`
- 本地项目已验证案例：`elmer/`

这是实际运行时的最高优先级来源。AI 写 SIF 时优先查这里，而不是只查 GitHub 最新分支。

### S1：官方 GitHub 仓库

- 仓库：`https://github.com/ElmerCSC/elmerfem`
- 主开发分支：`devel`
- 关键目录：
  - `fem/tests/`：官方可运行测试案例。
  - `fem/src/SOLVER.KEYWORDS`：SIF 关键字和类型清单。
  - `fem/src/modules/`：Solver 源码和真实读取的 SIF 参数。
  - `elmerice/Solvers/Documentation/`：Elmer/Ice Solver 文档。
  - `elmerice/UserFunctions/Documentation/`：Elmer/Ice 用户函数文档。
  - `ReleaseNotes/`：版本变化和新增关键字。
  - `compilation_instructions/`：构建和环境证据。

### S2：官方 PDF、论坛和外部资料

- 官方 manuals/tutorials PDF。
- Elmer forum 历史讨论。
- 论文、案例博客、第三方教程。

这一级只作补充。进入知识库前必须记录来源、日期、适用版本和可信度，不能覆盖 S0/S1 证据。

## 3. 蒸馏产物结构

建议在 `knowledge/distilled/` 下建立机器可读与人可读并存的结构：

```text
knowledge/distilled/
├── manifest.yaml
├── source_snapshots/
│   ├── elmer_runtime.yaml
│   ├── github_devel.yaml
│   └── local_project.yaml
├── keyword_index/
│   ├── solver_keywords.json
│   ├── keyword_aliases.yaml
│   └── keyword_evidence.md
├── solver_index/
│   ├── FlowSolver.yaml
│   ├── HeatSolver.yaml
│   ├── AdvectionDiffusionSolver.yaml
│   ├── ElasticSolver.yaml
│   └── ...
├── test_case_index/
│   ├── cases.jsonl
│   ├── by_solver/
│   ├── by_physics/
│   └── minimal_templates/
├── physics_cards/
│   ├── navier_stokes.md
│   ├── heat_equation.md
│   ├── advection_diffusion.md
│   ├── linear_elasticity.md
│   └── fsi.md
├── coupling_cards/
│   ├── flow_heat.md
│   ├── flow_species.md
│   ├── fsi_partitioned.md
│   └── thermo_elastic.md
├── troubleshooting/
│   ├── keyword_warnings.md
│   ├── mesh_boundary_mapping.md
│   ├── linear_solver_failures.md
│   ├── nonlinear_failures.md
│   └── conservation_checks.md
└── prompts/
    ├── sif_generation_guardrail.md
    ├── syntax_evidence_checklist.md
    └── case_review_checklist.md
```

## 4. 核心索引字段

### Solver 卡片

每个 Solver 生成一份 `solver_index/<Solver>.yaml`：

```yaml
solver: FlowSolver
module_candidates:
  - FlowSolve
procedure_candidates:
  - FlowSolver
equations:
  - Navier-Stokes
variables:
  - name: Flow Solution
    dofs: "Velocity:dim Pressure:1"
materials:
  required:
    - Density
    - Viscosity
  optional: []
boundary_conditions:
  common:
    - Velocity 1
    - Velocity 2
    - Pressure
    - No Slip Condition
keywords:
  solver: []
  material: []
  body_force: []
  bc: []
evidence:
  keywords:
    - path: fem/src/SOLVER.KEYWORDS
      commit: TODO
  tests:
    - path: fem/tests/CavityLid/case.sif
      commit: TODO
  source:
    - path: fem/src/modules/FlowSolve.F90
      commit: TODO
status: DRAFT
notes: []
```

### 测试案例索引

每个 `.sif` 生成一行 JSONL，便于 `rg`、脚本和向量检索共同使用：

```json
{"case_id":"CavityLid","sif":"fem/tests/CavityLid/case.sif","equations":["Navier-Stokes"],"procedures":["FlowSolve/FlowSolver"],"variables":["Flow Solution"],"dimension":"2D","study_type":"Transient","has_mesh":true,"has_reference":true,"commit":"TODO"}
```

### 物理卡片

每张 `physics_cards/*.md` 面向 AI 快速阅读，固定包含：

- 适用物理问题。
- 控制方程和变量。
- 推荐 Solver 与 SIF 最小骨架。
- 必要材料参数和单位。
- 常见边界条件。
- 最小官方测试案例。
- 易错关键字。
- 验证量：守恒、极值、参考解、网格/时间步敏感性。
- 证据路径和版本。

## 5. 蒸馏流水线

### P0：快照

记录所有来源版本：

- `ElmerSolver --version`
- `ElmerGrid --version`
- `/opt/src/elmerfem` 的 git commit
- GitHub `devel` 的 commit
- 本项目 commit 或文件时间戳

产物：`source_snapshots/*.yaml`。

### P1：关键字抽取

从 `SOLVER.KEYWORDS` 抽取：

- 块类型：`Simulation`、`Solver`、`Material`、`Body Force`、`IC`、`BC` 等。
- 值类型：`Real`、`Integer`、`Logical`、`String`。
- 原始关键字名、大小写形式、别名。

产物：`keyword_index/solver_keywords.json`。

### P2：源码参数抽取

扫描 `fem/src/modules/*.F90` 中的参数读取调用：

- `ListGetReal`
- `ListGetConstReal`
- `ListGetInteger`
- `ListGetLogical`
- `ListGetString`
- `GetSolverParams`

产物：每个 Solver 的候选关键字、默认值、读取位置。  
注意：源码抽取只能作为候选证据，必须再用测试案例或最小运行确认。

### P3：测试案例抽取

扫描 `fem/tests/**/*.sif`：

- `Equation`、`Solver`、`Procedure`、`Variable`
- `Material`、`Body Force`、`Initial Condition`、`Boundary Condition`
- `Simulation Type`、时间步、坐标系
- 是否有 `mesh/`、`README`、参考输出、CTest 配置

产物：`test_case_index/cases.jsonl` 和按 solver/physics 分类的索引。

### P4：模板筛选

从测试案例中筛出最小模板：

标准：

- 文件短、依赖少、边界清楚。
- 使用内置 Solver，不依赖复杂外部用户函数。
- 能在当前本地版本单核运行。
- 结果有简单可检查的标量、极值或参考场。

产物：`test_case_index/minimal_templates/`。

### P5：物理卡片生成

按高频建模主题生成卡片：

优先级：

1. Poisson / Laplace
2. Heat Equation
3. Navier-Stokes
4. Advection-Diffusion
5. Linear Elasticity
6. Flow + Heat
7. Flow + Species
8. FSI
9. Electrostatics / EM
10. Phase change / porous / specialized solvers

每张卡片必须引用至少：

- 1 个关键字证据；
- 1 个官方测试案例；
- 1 个源码或官方文档路径；
- 1 个最小验收检查。

### P6：验证

对每个最小模板执行：

- `CHECK KEYWORDS Warn` 无未知关键字。
- 单核运行完成。
- 无 NaN/Inf。
- 日志、命令、版本保存。
- 若有参考输出，误差在预设容差内。

通过后状态设为 `VALIDATED_TEMPLATE`；未运行只能是 `DRAFT_TEMPLATE`。

## 6. AI 使用规程

AI 未来建模时按下面顺序查证：

1. 读 `model_spec.yaml`，明确物理目标、维度、材料、IC/BC、输出量。
2. 查 `physics_cards/` 确定控制方程和候选 Solver。
3. 查 `solver_index/` 获取变量、材料和边界关键字。
4. 查 `test_case_index/` 找最接近的官方最小案例。
5. 查 `keyword_index/` 确认关键字类型和块位置。
6. 必要时查 `fem/src/modules/*.F90` 读取逻辑。
7. 写入 `syntax_evidence.md` 后再生成 SIF。
8. 运行 MVP，失败时查 `troubleshooting/`。

AI 输出 SIF 前必须回答：

- 使用了哪个 Solver 和 Procedure？
- 关键变量名和 DOF 是什么？
- 每个非显然关键字的证据路径是什么？
- 边界编号是否来自已验证 mesh？
- 当前状态是 `DRAFT`、`SYNTAX_VERIFIED` 还是 `MVP_PASSED`？

## 7. 质量等级

- `RAW`：只抓取，未解析。
- `INDEXED`：已结构化索引，但未人工审查。
- `EVIDENCED`：有关键字、测试案例、源码/文档三类证据。
- `RUNNABLE`：本地最小案例可运行。
- `VALIDATED_TEMPLATE`：本地运行并通过预设检查。
- `DEPRECATED`：版本变化或测试失败，不再默认推荐。

AI 只能默认使用 `RUNNABLE` 或 `VALIDATED_TEMPLATE`。低等级内容可用于提示检索方向，但不能直接生成正式模型结论。

## 8. 第一阶段交付范围

第一阶段只覆盖通用建模高频主题，不追求全量：

- `SOLVER.KEYWORDS` 结构化解析。
- `fem/tests` 的 SIF 案例总索引。
- 5 张物理卡片：Poisson、Heat、Navier-Stokes、Advection-Diffusion、Linear Elasticity。
- 3 张耦合卡片：Flow-Heat、Flow-Species、FSI。
- 10 个最小可运行模板。
- 1 套 AI 生成 SIF 前的证据检查清单。

完成第一阶段后，再扩展到电磁、声学、Elmer/Ice、并行/HPC 和特殊材料模型。

## 9. 不做什么

- 不把 GitHub `devel` 最新语法直接当成本地运行版本语法。
- 不把论坛答案直接升级为默认推荐。
- 不从案例名称反推物理方程。
- 不生成没有证据路径的 SIF 片段。
- 不把“求解器能跑完”视为“模型已验证”。

## 10. 推荐后续脚本

建议新增以下脚本：

```text
scripts/update_elmer_upstream_snapshot.ps1
scripts/distill_solver_keywords.py
scripts/distill_sif_tests.py
scripts/extract_solver_source_keywords.py
scripts/build_elmer_kb_cards.py
scripts/check_distilled_template.ps1
scripts/query_elmer_kb.ps1
```

这些脚本应只生成 `knowledge/distilled/` 下的派生产物，不修改原始官方源码和已验证案例。
