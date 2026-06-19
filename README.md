# 2026 五一数模 · B 题 多工序协同作业问题 —— 解题项目

> 本仓库为「2026 年第二十三届五一数学建模竞赛 · 校赛模拟 2」B 题（多工序协同作业 / 柔性作业车间调度 FJSP）的解题工作区。
> 选题分析见 [`docs/analysis/选题可行性分析.md`](docs/analysis/选题可行性分析.md)。

## 选题决策

经 A/B/C 三题四维度评估 + **夺奖策略修正**（详见分析文档），**选定 B 题**：
- 夺奖核心逻辑：在可完成前提下优先选择**区分度更高**的题。B 题以 makespan、调度表、设备利用率和关键路径为核心产出，结果更便于比较，但必须保证约束完整和解质量可验证。
- 难度 9/10（NP-hard，但题目实例规模有限，可用精确求解基准 + 启发式优化覆盖主要难点），论文丰富度 8/10（甘特图 + 算法对比 + 敏感性分析）。

## 项目结构

```
solve/
├── README.md                     # 本文件（项目索引）
├── .gitignore
├── requirements.txt              # Python 依赖（调度优化栈）
├── docs/                         # 文档
│   ├── analysis/                 # 选题与可行性分析
│   │   └── 选题可行性分析.md
│   ├── paper/                    # 最终论文 (Typst/LaTeX 源码与 PDF)
│   └── figures/                  # 论文配图（甘特图等）
├── data/                         # 数据
│   ├── raw/                      # 原始附件 B-附件.xlsx（需手动放入）
│   └── processed/                # 中间数据（git 忽略）
├── code/                         # 解题代码与验证脚本
│   ├── analysis/                 # Q2 下界与 Q4 显式采购 CP-SAT 验证
│   ├── plot/                     # 论文图件重生成脚本
│   ├── Q1_单车间调度/            # 早期模块规划（当前非主复现入口）
│   ├── Q2_多车间调度/            # 早期模块规划（当前非主复现入口）
│   ├── Q3_双班组调度/            # 早期模块规划（当前非主复现入口）
│   ├── Q4_预算购置优化/          # 早期模块规划（当前非主复现入口）
│   ├── common/                   # 后续扩展公共工具规划
│   └── solvers/                  # 后续扩展求解器规划
├── baseline_v1/                  # 【v1 基线参考】初版分析报告（已复审）
│   ├── code/model_solver.py      #   单体 MILP 求解脚本（scipy.optimize.milp / HiGHS）
│   ├── code/create_report.py     #   报告生成脚本（python-docx）
│   ├── data/                     #   结构化工序/设备/距离 CSV
│   ├── docs/                     #   研究报告（md/docx/pdf）+ 文献调研
│   ├── figures/                  #   Q1~Q4 甘特图 + 总时长对比图
│   └── results/                  #   表1~表5 结果 CSV（可由脚本重新生成）
├── models/                       # 求解日志/参数（git 忽略大文件）
└── results/                      # 表1~表5 结果输出（git 忽略中间产物）
```

## 当前正式方法路线

当前论文与可复现代码统一采用以下路线：

| 层次 | 作用 | 入口 |
|:-----|:-----|:-----|
| 主调度模型 | MILP / HiGHS 生成 Q1-Q4 数值结果与 CSV 调度表 | `baseline_v1/code/model_solver.py` |
| 独立验证模型 | CP-SAT 验证 Q2 双瓶颈松弛下界与 Q4 显式采购模型 | `code/analysis/verify_optimality_chain.py` |
| 论文图件 | 从 CSV 结果表重生成甘特图与 makespan 对比图 | `code/plot/plot_gantt.py` |

遗传算法、模拟退火、DEAP 等启发式方法仅作为**大规模推广方向**保留，不作为本文 Q1-Q4 结果来源。

## 题目关键约束备忘

- **工序顺序**：各车间内工序严格按编号由小到大执行。
- **双设备协同**：需两类设备的工序，两类各自独立完成全部工程量，取较晚完成时刻为工序完成时刻。
- **C 车间循环**：C3→C4→C5 三工序需重复 3 遍（展开为 9 个工序实例）。
- **设备互斥**：同一时刻每台设备只能服务一道工序；同设备同车间内换工序无运输时间。
- **跨车间运输**：同设备跨车间作业，运输时间 = 距离 / 移动速度(2 m/s)，向上取整到秒。
- **时间精度**：从 00:00:00 起，持续工作时间精确到秒且向上取整。

## 快速开始

```bash
# 1. 创建虚拟环境（推荐 uv）
uv venv .venv && source .venv/bin/activate
# 或: python3 -m venv .venv && source .venv/bin/activate

# 2. 安装依赖
uv pip install -r requirements.txt   # 或 pip install -r requirements.txt

# 3. 放入数据：将 B 题附件 B-附件.xlsx 复制到 data/raw/

# 4. 复现正式结果
python baseline_v1/code/model_solver.py
python code/analysis/verify_optimality_chain.py
python code/plot/plot_gantt.py
```

## v1 基线参考（`baseline_v1/`）

[`baseline_v1/`](baseline_v1/) 是首个初版分析报告的完整交付包，作为**一个解题方向参考**纳入项目。其内部保留原始扁平布局（`code/`+`data/`+`docs/`+`figures/`+`results/`），脚本相对路径未改动，可一键复现。

> **已完成复审**：见 [`docs/analysis/baseline_v1复审与算法方向决策.md`](docs/analysis/baseline_v1复审与算法方向决策.md)。
> **完整分析链**：见 [`docs/analysis/B题完整分析链与最优性验证.md`](docs/analysis/B题完整分析链与最优性验证.md)，已补 Q2 双瓶颈资源松弛下界与 Q4 显式采购 CP-SAT 验证。
> 复审结论：v1 模型正确、结果可信（4.73s 全局最优复现），Q1/Q2/Q3/Q4 均已有下界或显式模型背书。**当前正式路线：以 MILP/HiGHS 作为完整调度主模型，使用 CP-SAT 构造独立下界与采购验证模型；GA 仅作为后续大规模推广方向。**

- **方法**：混合整数线性规划（`scipy.optimize.milp` / HiGHS），Q1~Q3 求全局最优，Q4 由 C 车间关键路径下界证明最优采购为 0 台。
- **核心结论**：Q1 = 41600s（11:33:20）、Q2 = 163764s（45:29:24）、Q3 = 123844s（34:24:04）、Q4 = 123844s（采购 0 台）。
- **栈说明**：完整调度主模型使用 `scipy.optimize.milp` / HiGHS；验证模型使用 OR-Tools CP-SAT；论文图件使用 matplotlib。

复现 v1：

```bash
source .venv/bin/activate
cd baseline_v1
python code/model_solver.py        # 重新生成 results/*.csv 并打印 Q1~Q4 最短时长
python code/create_report.py       # 重新生成 docs/研究报告.{md,docx}（引用现有图件）
```

复现 Q2/Q4 独立验证：

```bash
source .venv/bin/activate
python code/analysis/verify_optimality_chain.py
```

重生成论文图件：

```bash
source .venv/bin/activate
python code/plot/plot_gantt.py
```

> 注：v1 的 `source/`（竞赛题目原文件）未入库——属版权材料，且数据已硬编码于 `model_solver.py`，复现无需原附件。

## 约定

- **代码标识符用英文**，注释/论文/文档用中文。
- 原始数据（`data/raw/`）需手动放入，不入库竞赛题目版权材料。
- 中间产物（`data/processed/`、`models/`、`results/`）默认 git 忽略，仅保留 `.gitkeep`。
- 甘特图统一放 `docs/figures/`，风格走科研级（matplotlib）。

## 仓库

- 默认分支：`main`（初始骨架：C题分析稿）。
- 开发分支：`dev`（**当前**：B题方向重构与各子问题推进）。
