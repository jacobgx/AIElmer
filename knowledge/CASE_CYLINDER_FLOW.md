# 圆柱绕流案例

## 几何与流动

- 二维通道：`L = 2.2 m`，`H = 0.41 m`。
- 圆柱：半径 `R = 0.05 m`，圆心 `(0.2 m, 0.2 m)`。
- 流体：`rho = 1 kg/m³`，`mu = 1e-3 Pa·s`，平均入口速度 `1 m/s`。
- 雷诺数：`Re = rho U (2R) / mu = 100`。
- 左侧抛物线入口，右侧零表压出口，壁面与圆柱无滑移。
- ElmerFEM 时间离散：BDF2，`dt = 0.02 s`，350 步，终止时间 `7 s`。

## 温度场扩展

- Elmer 求解器：`FlowSolver`（Navier–Stokes）与 `HeatSolver`（Heat Equation）。
- 在 `Equation` 中设置 `Convection = Computed`，温度方程使用 Elmer 求得的速度场进行对流输运。
- 初始/入口温度：`25 °C`。
- 圆柱表面温度：`100 °C`。
- 出口：对流流出；上下壁面：默认绝热。
- 为保留原参考流动，热物性取常数 `Cp = 1000 J/(kg·K)`、`k = 0.6 W/(m·K)`，密度和黏度不随温度变化，即无浮力反馈。

## 复现

```powershell
.\scripts\run_elmer_cylinder.ps1 -Case baseline
.\scripts\run_elmer_cylinder.ps1 -Case thermal
.\scripts\run_elmer_cylinder.ps1 -Case species
python .\scripts\postprocess_elmer_cylinder.py
```

## 菲克定律稀物质传递

- 使用 Elmer `AdvectionDiffusionSolver`，变量为 `Concentration`，`Concentration Units = Absolute Mass`。
- `Concentration Diffusivity = 1e-3 m²/s`；`Equation` 中使用 `Convection = Computed` 与 Elmer 速度场耦合。
- 初始及入口浓度为 `0 mol/m³`；圆柱边界使用 `Concentration Flux = 100 mol/(m²·s)`。
- 上下壁面默认无通量，出口采用自然对流流出。

SIF、网格、VTU 和日志位于 `elmer/cylinder_flow/`，审核后的图与摘要位于 `results/elmer/`。原始 `cylinder_flow.java/.class` 只作为 COMSOL 基准定义，保持不变。
