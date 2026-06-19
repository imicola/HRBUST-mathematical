# 2026五一数学建模B题交付包

本交付包包含完整研究报告、建模代码、结构化数据、求解结果表与研究过程记录。

## 文件结构

- `docs/研究报告.docx`：完整研究报告，含模型、假设、求解结果、Q4关键路径证明与附录结果表。
- `docs/研究报告.md`：Markdown版报告。
- `code/model_solver.py`：核心MILP建模与求解脚本。
- `code/create_report.py`：生成报告文档的脚本。
- `data/processes_expanded.csv`：展开后的工序与设备子任务数据。
- `data/equipment_base.csv`：基础设备配置。
- `data/distances.csv`：车间/班组距离与转运时间。
- `results/summary.csv`：Q1-Q4最短时长汇总。
- `results/table1_question1.csv` 到 `results/table5_purchase_plan.csv`：题目表1至表5结果。
- `figures/`：Q1-Q4甘特图与总时长对比图。
- `research_process.md`：研究过程记录与关键建模决策。

## 复现实验

在已安装 `numpy`、`scipy` 的Python环境下运行：

```bash
python code/model_solver.py
```

脚本将重新生成 `results/` 下的结果表，并打印Q1-Q4最短时长。

## 核心结论

- Q1最短时长：41600s = 11:33:20
- Q2最短时长：163764s = 45:29:24
- Q3最短时长：123844s = 34:24:04
- Q4最短时长：123844s = 34:24:04；最优采购为0台，原因是Q3已达到C车间固定工序链关键路径下界。
