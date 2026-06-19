# solvers 求解器封装

封装不同求解范式，供 Q1~Q4 按规模与精度需求调用：

- `cpsat_solver.py`：Google OR-Tools CP-SAT 约束规划求解器
  - 建模：OptionalIntervalVar 表达工序-设备分配、叠加运输 setup time、双设备协同（两 interval 取 max 完成时刻）、工序优先约束、设备互斥（NoOverlap）。
  - 适用：Q1 精确求解、Q2~Q3 带时限的基准对照。
- `ga_solver.py`：遗传算法
  - 编码：工序排序染色体（GS 编码）+ 设备分配染色体；Q3/Q4 扩展班组选择基因。
  - 算子：锦标赛选择、POX 交叉、插入变异；解码含运输时间与双设备协同。
- `sa_solver.py`：模拟退火（备选元启发式，邻域 = 交换/插入工序 + 重分配设备）。
- `decode.py`：统一解码器（染色体 → 可行调度 → makespan），保证各算法评估口径一致。
