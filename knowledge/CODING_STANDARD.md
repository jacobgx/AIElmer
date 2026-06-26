# 项目编码规范

## 通用

- 源文件 UTF-8；路径、参数、边界、单位必须显式。
- 不覆盖用户原始 `cylinder_flow.java/.class`；派生模型使用新文件名。
- 每次运行保留求解日志，结果必须至少包含模型文件和一张场图。

## Elmer SIF

- 块按 `Header → Simulation → Constants → Body → Equation → Solver → Material → Initial Condition → Boundary Condition` 排列。
- Solver、材料、边界使用连续编号和语义化 `Name`。
- 所有物理量带 SI 单位注释；温度内部统一 K，报告可转换 °C。
- 网格边界编号必须由 `mesh.boundary` 验证并写入案例文档。
- 先建立最小可运行版本，再增加耦合、复杂材料和并行求解。


- 每个 `model.*` API 调用旁写用途注释；新增 API 先在本地 AICOMSOl API/官方模型库检索。
- 参数集中在文件顶部，表达式携带单位；不把物理常数散落在边界条件里。
- 使用明确的物理 tag：`spf`、`ht`、`nitf1`；使用明确的结果 tag：`pgVel`、`pgT`。
- 建模、求解、后处理分层；保存 `.mph` 后再导出图片。
- 调试两轮仍失败时停止盲试，基于求解日志和官方参考定位。

## PowerShell

- 脚本启用 `$ErrorActionPreference = 'Stop'`。
- 路径用 `Join-Path`，外部程序退出码必须检查。
- 不在脚本中硬编码用户凭据、许可证内容或网络令牌。
