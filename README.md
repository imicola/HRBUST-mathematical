# 2026 五一数模 · C 题 边坡预警问题 —— 解题项目

> 本仓库为「2026 年第二十三届五一数学建模竞赛 · 校赛模拟 2」C 题（边坡预警问题）的解题工作区。
> 选题分析见 [`docs/analysis/选题可行性分析.md`](docs/analysis/选题可行性分析.md)。

## 选题决策

经 A/B/C 三题四维度（难度 / 可行性 / 论文丰富度 / 得分难度）评估，**选定 C 题**：
- 可行性 9/10、论文丰富度 10/10、得分难度 5/10（最易拿分）、难度 6/10。
- 5 个子问题覆盖完整数据科学闭环，方法栈成熟（ruptures / scipy / xgboost / shap / sklearn），可 100% 完整交付。

## 项目结构

```
solve/
├── README.md                     # 本文件（项目索引）
├── .gitignore
├── requirements.txt              # Python 依赖
├── docs/                         # 文档
│   ├── analysis/                 # 选题与可行性分析
│   │   └── 选题可行性分析.md
│   ├── paper/                    # 最终论文 (Typst/LaTeX 源码与 PDF)
│   └── figures/                  # 论文配图
├── data/                         # 数据
│   ├── raw/                      # 原始附件数据（xlsx，需手动放入）
│   └── processed/                # 清洗/中间数据（git 忽略）
├── code/                         # 解题代码（按子问题分目录）
│   ├── Q1_数据校正/              # Q1 位移数据校正（A→B 标定）
│   ├── Q2_阶段识别/              # Q2 三段式形变转换点识别
│   ├── Q3_去噪异常检测/          # Q3 去噪/填补/异常检测/关联分析
│   ├── Q4_分阶段预测/            # Q4 分阶段位移预测
│   ├── Q5_特征选择预警/          # Q5 特征选择 + 滑坡预警阈值
│   └── common/                   # 公共工具（数据加载、绘图、指标）
├── models/                       # 训练好的模型（git 忽略大文件）
└── results/                      # 输出结果表格（git 忽略中间产物）
```

## 子问题与方法栈速查

| 子问题 | 目标 | 主流方法 | 关键库 |
|:------|:-----|:--------|:-------|
| Q1 | 位移数据 A（含零漂）校正到基准 B | 回归标定 / Kalman 滤波 | sklearn, pykalman |
| Q2 | 三段式形变阶段转换节点识别 | 变点检测 PELT/BinSeg + 速度突变法 | ruptures |
| Q3 | 去噪 / 缺失填补 / 异常检测 / 关联分析 | SG·小波·Kalman / KNN·MICE / 孤立森林 / XGBoost+SHAP | scipy, sklearn, xgboost, shap |
| Q4 | 分阶段多特征位移预测 | 分阶段回归（XGB/LGBM），可选 LSTM | xgboost, lightgbm |
| Q5 | 特征选择最优组合 + 预警阈值机制 | RFE / 组合枚举 + 位移速度·切线角法 | sklearn, numpy |

## 快速开始

```bash
# 1. 创建虚拟环境（推荐 uv）
uv venv .venv && source .venv/bin/activate
# 或: python3 -m venv .venv && source .venv/bin/activate

# 2. 安装依赖
uv pip install -r requirements.txt   # 或 pip install -r requirements.txt

# 3. 放入数据：将 C 题附件 xlsx 复制到 data/raw/

# 4. 运行某子问题代码
python code/Q1_数据校正/main.py
```

## 约定

- **代码标识符用英文**，注释/论文/文档用中文。
- 原始数据（`data/raw/`）需手动放入，不入库竞赛题目版权材料。
- 中间产物（`data/processed/`、`models/`、`results/`）默认 git 忽略，仅保留 `.gitkeep`。
- 论文配图统一放 `docs/figures/`，绘图风格走科研级（matplotlib + seaborn）。

## 仓库

- 默认分支：`main`（初始项目骨架）。
- 开发分支：`dev`（各子问题在此推进）。
