# Elmer 语法证据：{{CASE_ID}}

环境版本：待记录。

| ID | 建模目的 | 最终SIF关键字 | 证据路径/行号 | 版本 | 最小测试 | 状态 |
|---|---|---|---|---|---|---|
| S-001 | TODO | TODO | `/opt/src/elmerfem/...` | TODO | TODO | UNVERIFIED |

```powershell
.\scripts\query_kb.ps1 'Linear System Solver'
wsl -d $env:ELMER_WSL_DISTRO -- bash -lc "rg -n -i 'keyword' /opt/src/elmerfem/fem/tests /opt/src/elmerfem/doc | head -80"
```

