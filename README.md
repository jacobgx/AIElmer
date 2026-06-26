# AIElmer — ElmerFEM AI 建模知识库

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE.md)
[![ElmerFEM 26.2](https://img.shields.io/badge/ElmerFEM-26.2-green)](https://github.com/ElmerCSC/elmerfem)

[**English**](#english) · [**中文**](#中文)

一套面向 **AI 辅助建模** 的 ElmerFEM 知识框架。提供结构化的八阶段建模工作流、可复用的案例模板、以及可搜索的 ElmerFEM 知识层（方程/求解器/物理/关键词索引），帮助 AI 代理和工程师系统性地构建、审计、验证和分享 ElmerFEM 多物理场模型。

> An **AI-ready** ElmerFEM modeling knowledge framework with structured workflows, reusable templates, and a searchable knowledge layer.

---

# 中文

## 目录概览

| 目录 | 内容 |
|------|------|
| `knowledge/` | 可搜索知识库：ElmerFEM 快速参考、AI 建模标准（八阶段闸门）、关键词/求解器/物理卡片、蒸馏官方案例索引 |
| `templates/elmer_case/` | 可复用的案例合约模板：`model_spec.yaml`、`formulation.md`、`syntax_evidence.md`、`validation_plan.md`、`uncertainties.md` |
| `scripts/` | PowerShell/Python 工具：知识库搜索、案例创建、完整性检查、Elmer 运行与后处理、GitHub 导出 |
| `elmer/` | 完整案例：圆柱绕流基准（Navier–Stokes/传热/组分输运）、振荡FSI（Turek-Hron FSI3）、官方Elmer测试复现 |
| `docs/` | 环境部署指南、AI 代理使用指南、仓库结构说明 |

## 环境搭建

新环境？详见 **[docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md)** —— 涵盖 ElmerFEM、Gmsh、WSL、OpenMPI 的安装配置。

## 快速开始

```powershell
# 一次性配置：指定 WSL 发行版
. .\scripts\elmer_env.ps1

# 搜索知识库
.\scripts\query_kb.ps1 'Navier-Stokes'
.\scripts\query_kb.ps1 'TemperatureBoundary'

# 验证 ElmerFEM
wsl -d $env:ELMER_WSL_DISTRO -- ElmerSolver --version

# 创建新的 AI 审计级 Elmer 案例
.\scripts\new_elmer_case.ps1 -Name heat_exchanger
.\scripts\check_elmer_case.ps1 .\elmer\heat_exchanger

# 蒸馏官方 Elmer 测试案例为可搜索索引
python .\scripts\distill_sif_tests.py
```

## AI 代理使用规范

让 AI 在生成或修改任何 Elmer 模型**之前**先阅读以下文件：

1. `docs/AI_AGENT_GUIDE.md` — 首次读取协议
2. `knowledge/ELMER_AI_MODELING_STANDARD.md` — 八阶段建模闸门
3. `knowledge/ELMER_KB_DISTILLATION_PLAN.md` — 证据优先级规则
4. `templates/elmer_case/README.md` — 案例合约

AI **禁止**在记录物理假设、语法证据、网格边界映射和验证计划之前编写最终 SIF 文件。

## 案例展示

### 圆柱绕流基准

Re=100 的圆柱绕流，含传热与组分输运扩展。

```powershell
.\scripts\run_elmer_cylinder.ps1 -Case baseline   # Navier–Stokes
.\scripts\run_elmer_cylinder.ps1 -Case thermal     # + 传热
.\scripts\run_elmer_cylinder.ps1 -Case species     # + 对流扩散
python .\scripts\postprocess_elmer_cylinder.py
```

详见 `elmer/cylinder_flow/README.md`。

### 振荡 FSI（Turek-Hron FSI3）

圆柱后方柔性梁的流固耦合，包含固定流场、纯固体、完整 FSI 求解器变体，以及稳定化与离散化筛选。

详见 `elmer/oscillating_fsi/README.md`。

### 官方 Elmer 测试复现

在 `elmer/official_runs/` 下已验证的上游 Elmer 测试案例：
- `fsi_beam` — FSI 梁基准
- `EMWaveBoxHexas` — 电磁波腔体
- `elstat` — 静电分析

## 仓库结构

```text
.
├── README.md
├── LICENSE.md
├── .gitignore / .gitattributes
├── docs/                    # 部署指南、AI代理指南、仓库说明
├── knowledge/               # 可搜索知识库 + 蒸馏索引
│   └── distilled/           #   求解器/物理卡片、关键词索引
├── templates/elmer_case/    # 新案例合约模板
├── scripts/                 # PowerShell + Python 工具链
├── elmer/                   # Elmer 案例
│   ├── cylinder_flow/       #   圆柱绕流基准
│   ├── oscillating_fsi/     #   Turek-Hron FSI3 复现
│   └── official_runs/       #   官方测试复现
```

## 许可证

知识库框架文件基于 [MIT License](LICENSE.md) 发布。ElmerFEM 本身、上游 Elmer 示例及本地仿真输出不受本仓库的许可约束。

---

# English

## Overview

An **AI-ready framework** for building, auditing, validating, and sharing ElmerFEM multiphysics models. It enforces a structured eight-gate modeling workflow, provides reusable case templates, and maintains a searchable knowledge layer of ElmerFEM modeling patterns (equations, solvers, physics, keywords).

## Setup

See **[docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md)** for step-by-step installation of ElmerFEM, Gmsh, WSL, and OpenMPI.

## Quick Start

```powershell
. .\scripts\elmer_env.ps1                      # configure WSL distro
.\scripts\query_kb.ps1 'Navier-Stokes'          # search the KB
.\scripts\new_elmer_case.ps1 -Name my_case      # create a new case
.\scripts\check_elmer_case.ps1 .\elmer\my_case  # validate
```

## For AI Agents

Read before generating any Elmer model:

1. `docs/AI_AGENT_GUIDE.md`
2. `knowledge/ELMER_AI_MODELING_STANDARD.md`
3. `knowledge/ELMER_KB_DISTILLATION_PLAN.md`
4. `templates/elmer_case/README.md`

Never write a final SIF before recording assumptions, evidence, mesh mapping, and a validation plan.

## Worked Examples

| Case | Description |
|------|-------------|
| `elmer/cylinder_flow/` | Cylinder-flow benchmark at Re=100 (flow, thermal, species) |
| `elmer/oscillating_fsi/` | Turek-Hron FSI3 — 22 solver variants, discretization/stabilization screening |
| `elmer/official_runs/` | Verified upstream test reproductions (fsi_beam, EMWaveBoxHexas, elstat) |

## License

Framework files: [MIT](LICENSE.md). ElmerFEM itself and upstream examples retain their original licenses.

---

# 👤 作者 / Author

**能动李老师** — 全网同名

| 平台 | 内容 |
|------|------|
| 🎬 **B站** | [能动李老师](https://space.bilibili.com/) — 长视频教程 |
| 📱 **小红书** | [能动李老师](https://www.xiaohongshu.com/) — 短视频知识分享 |
| 📚 **公众号** | **通天达灵** — COMSOL 多物理场建模知识分享 |
| 📧 **邮箱** | `Jacobgx@163.com` — 项目合作与技术交流 |

> 🔗 Follow for more COMSOL multiphysics modeling tutorials and AI-assisted simulation workflows.

---

Built with [ElmerFEM](https://github.com/ElmerCSC/elmerfem) — open-source multiphysics FEM.
