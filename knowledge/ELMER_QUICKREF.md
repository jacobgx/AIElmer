# ElmerFEM 快速参考

## 环境验证

```powershell
# Set your WSL distro (see scripts/elmer_env.ps1)
wsl -d $env:ELMER_WSL_DISTRO -- ElmerSolver --version
```

## 标准案例目录

```text
case/
├── case.sif
├── mesh/                 # ElmerGrid 生成
│   ├── mesh.header
│   ├── mesh.nodes
│   ├── mesh.elements
│   └── mesh.boundary
└── results/
```

## 求解

```bash
cd case
ElmerSolver case.sif
mpirun -np 4 ElmerSolver_mpi case.sif
```

## SIF 主结构

```text
Header
  CHECK KEYWORDS Warn
  Mesh DB "." "mesh"
End

Simulation
  Coordinate System = Cartesian 2D
  Simulation Type = Transient
  Timestepping Method = BDF
  BDF Order = 2
  Timestep Sizes = 0.02
  Timestep Intervals = 350
  Output Intervals = 10
End

Body 1
  Equation = 1
  Material = 1
  Initial Condition = 1
End
```

关键块还包括 `Constants`、`Equation`、`Solver`、`Material`、`Body Force`、`Initial Condition` 与 `Boundary Condition`。名称可读、编号稳定；每个边界编号必须来自 `mesh.boundary`，禁止猜测。

## 常用方程

- 不可压流：`Equation = Navier-Stokes`
- 传热：`Equation = Heat Equation`
- 流热耦合：在同一 `Equation` 中激活对应两个 Solver，温度方程使用速度场对流。
- 稳态先验：高雷诺数瞬态可先跑稳态/低入口速度，再用结果作为瞬态初值。

## 排错顺序

1. `ElmerGrid` 后核对边界编号与元素维度。
2. `CHECK KEYWORDS Warn` 检查拼写和失效关键字。
3. 先用粗网格、短时间、单核运行。
4. 检查每个 Solver 的 `Linear System Converged` 和非线性残差。
5. 只有单核收敛后再启用 MPI；保持同一 SIF 与网格作对照。
