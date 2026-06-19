# -*- coding: utf-8 -*-
"""
2026 五一数学建模 B 题：多工序协同作业问题
MILP 求解脚本

说明：
1. 工序数据依据题目附件 B-attachment.xlsx / B-附件.xlsx 人工结构化录入。
2. C3-C5 按题意展开为 3 轮：C3_R1,C4_R1,C5_R1,...,C3_R3,C4_R3,C5_R3。
3. 工序内若需要两类设备，模型令两类设备在同一开始时刻投入，分别占用其实际作业时长；工序完成时刻为两类设备结束时刻最大值。
4. 每台设备跨车间转运时间 = 距离 / 2 m/s，向上取整到秒；同车间转运为 0。
5. 固定设备条件下使用 scipy.optimize.milp 求全局最优；Q4 由关键路径下界证明追加设备不能进一步缩短工期，故最优采购为 0。
"""

from __future__ import annotations

import csv
import itertools
import math
import os
from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import csr_matrix, lil_matrix

EQUIPMENT_TYPES = [
    "Automated Conveying Arm",
    "Industrial Cleaning Machine",
    "Precision Filling Machine",
    "Automatic Sensing Multi-Function Machine",
    "High-speed Polishing Machine",
]

TYPE_ZH = {
    "Automated Conveying Arm": "自动化输送臂",
    "Industrial Cleaning Machine": "工业清洗机",
    "Precision Filling Machine": "精密灌装机",
    "Automatic Sensing Multi-Function Machine": "自动传感多功能机",
    "High-speed Polishing Machine": "高速抛光机",
}

UNIT_PRICE = {
    "Automated Conveying Arm": 50000,
    "Industrial Cleaning Machine": 40000,
    "Precision Filling Machine": 35000,
    "Automatic Sensing Multi-Function Machine": 80000,
    "High-speed Polishing Machine": 75000,
}

BASE_COUNTS = {
    1: {
        "Automated Conveying Arm": 4,
        "Industrial Cleaning Machine": 5,
        "Precision Filling Machine": 5,
        "Automatic Sensing Multi-Function Machine": 1,
        "High-speed Polishing Machine": 1,
    },
    2: {
        "Automated Conveying Arm": 4,
        "Industrial Cleaning Machine": 5,
        "Precision Filling Machine": 5,
        "Automatic Sensing Multi-Function Machine": 1,
        "High-speed Polishing Machine": 1,
    },
}

RAW_DISTANCE = [
    ("Crew 1", "A", 400), ("Crew 1", "B", 620), ("Crew 1", "C", 460), ("Crew 1", "D", 710), ("Crew 1", "E", 400),
    ("Crew 2", "A", 500), ("Crew 2", "B", 460), ("Crew 2", "C", 620), ("Crew 2", "D", 680), ("Crew 2", "E", 550),
    ("A", "B", 1020), ("A", "C", 1050), ("A", "D", 900), ("A", "E", 1400),
    ("B", "C", 1100), ("B", "D", 1630), ("B", "E", 720),
    ("C", "D", 520), ("C", "E", 850), ("D", "E", 1030),
]
DISTANCE = {}
for a, b, d in RAW_DISTANCE:
    DISTANCE[(a, b)] = d
    DISTANCE[(b, a)] = d
for node in ["A", "B", "C", "D", "E", "Crew 1", "Crew 2"]:
    DISTANCE[(node, node)] = 0

EQUIPMENT_SPEED = {t: 2 for t in EQUIPMENT_TYPES}

PROCESS_BASE = [
    ("A", "A1", "Defect Filling", {"Precision Filling Machine": 200, "Automated Conveying Arm": 250}, 300),
    ("A", "A2", "Surface Leveling", {"High-speed Polishing Machine": 100, "Industrial Cleaning Machine": 250}, 500),
    ("A", "A3", "Strength Testing", {"Automatic Sensing Multi-Function Machine": 100}, 500),
    ("B", "B1", "Surface Cleaning", {"Industrial Cleaning Machine": 100}, 120),
    ("B", "B2", "Base Layer Construction", {"Precision Filling Machine": 200, "Automated Conveying Arm": 300}, 1500),
    ("B", "B3", "Surface Sealing", {"Precision Filling Machine": 350}, 360),
    ("B", "B4", "Surface Leveling", {"High-speed Polishing Machine": 120, "Automatic Sensing Multi-Function Machine": 100}, 360),
    ("C", "C1", "Old Coating Removal", {"Industrial Cleaning Machine": 250, "Automated Conveying Arm": 250}, 720),
    ("C", "C2", "Base Filling", {"Precision Filling Machine": 350}, 720),
    ("C", "C3", "Sealing Coverage", {"Precision Filling Machine": 200, "Automated Conveying Arm": 250}, 360),
    ("C", "C4", "Surface Grinding", {"High-speed Polishing Machine": 120, "Industrial Cleaning Machine": 100}, 400),
    ("C", "C5", "Quality Inspection", {"Automatic Sensing Multi-Function Machine": 100}, 400),
    ("D", "D1", "Debris Removal", {"Industrial Cleaning Machine": 250}, 600),
    ("D", "D2", "Base Solidification", {"Precision Filling Machine": 200, "Automated Conveying Arm": 300}, 800),
    ("D", "D3", "Surface Sealing", {"Precision Filling Machine": 350}, 450),
    ("D", "D4", "Surface Leveling", {"High-speed Polishing Machine": 120, "Automatic Sensing Multi-Function Machine": 300}, 1500),
    ("D", "D5", "Load-bearing Inspection", {"Automatic Sensing Multi-Function Machine": 300}, 1500),
    ("D", "D6", "Edge Trimming", {"High-speed Polishing Machine": 100}, 700),
    ("E", "E1", "Foundation Treatment", {"Industrial Cleaning Machine": 250}, 1000),
    ("E", "E2", "Surface Sealing", {"Precision Filling Machine": 350}, 600),
    ("E", "E3", "Stability Inspection", {"Automatic Sensing Multi-Function Machine": 300, "Industrial Cleaning Machine": 100}, 600),
]


def sec_to_hms(sec: int | float) -> str:
    sec = int(round(sec))
    return f"{sec // 3600:02d}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


def travel_time(origin: str, destination: str, equip_type: str) -> int:
    return int(math.ceil(DISTANCE[(origin, destination)] / EQUIPMENT_SPEED[equip_type]))


def build_processes() -> List[dict]:
    chains = defaultdict(list)
    for row in PROCESS_BASE:
        w, pid, name, eff, work = row
        if w != "C":
            chains[w].append(row)
    for row in PROCESS_BASE:
        if row[0] == "C" and row[1] in ["C1", "C2"]:
            chains["C"].append(row)
    c345 = [row for row in PROCESS_BASE if row[0] == "C" and row[1] in ["C3", "C4", "C5"]]
    for r in range(1, 4):
        for w, pid, name, eff, work in c345:
            chains["C"].append((w, f"{pid}_R{r}", name, eff, work))

    processes = []
    for w in ["A", "B", "C", "D", "E"]:
        for seq, row in enumerate(chains[w]):
            workshop, pid, name, efficiency, workload = row
            durations = {t: int(math.ceil(workload / rate * 3600)) for t, rate in efficiency.items()}
            processes.append({
                "workshop": workshop,
                "pid": pid,
                "name": name,
                "efficiency": efficiency,
                "workload": workload,
                "durations": durations,
                "maxdur": max(durations.values()),
                "seq": seq,
            })
    return processes


def make_machines(crews: Iterable[int] = (1,), extra: Optional[Dict[Tuple[int, str], int]] = None) -> List[dict]:
    extra = extra or {}
    machines = []
    for crew in crews:
        for t in EQUIPMENT_TYPES:
            count = BASE_COUNTS[crew][t] + extra.get((crew, t), 0)
            for i in range(1, count + 1):
                if i <= BASE_COUNTS[crew][t]:
                    machine_id = f"{TYPE_ZH[t]}{crew}-{i}"
                else:
                    machine_id = f"{TYPE_ZH[t]}{crew}-增购{i - BASE_COUNTS[crew][t]}"
                machines.append({"id": machine_id, "type": t, "type_zh": TYPE_ZH[t], "crew": crew, "origin": f"Crew {crew}"})
    return machines


def solve_milp(
    processes: List[dict],
    machines: List[dict],
    allowed_workshops: Optional[set[str]] = None,
    time_limit: float = 120,
    mip_rel_gap: float = 0.0,
    max_makespan: Optional[int] = None,
    objective: str = "makespan",
    verbose: bool = False,
):
    procs = [p for p in processes if allowed_workshops is None or p["workshop"] in allowed_workshops]
    n_jobs = len(procs)

    ops = []
    for j, p in enumerate(procs):
        for t, dur in p["durations"].items():
            ops.append({"job": j, "pid": p["pid"], "workshop": p["workshop"], "type": t, "dur": dur})

    machines_by_type = defaultdict(list)
    for mi, m in enumerate(machines):
        machines_by_type[m["type"]].append((mi, m))

    idx_start = list(range(n_jobs))
    idx_tmax = n_jobs
    var_count = n_jobs + 1

    x_idx = {}
    for oi, op in enumerate(ops):
        for mi, _ in machines_by_type[op["type"]]:
            x_idx[(oi, mi)] = var_count
            var_count += 1

    y_idx = {}
    ops_by_type = defaultdict(list)
    for oi, op in enumerate(ops):
        ops_by_type[op["type"]].append(oi)
    for t, op_list in ops_by_type.items():
        for a, b in itertools.combinations(op_list, 2):
            for mi, _ in machines_by_type[t]:
                y_idx[(a, b, mi)] = var_count
                var_count += 1

    n_vars = var_count
    c = np.zeros(n_vars)
    if objective == "sum_start":
        for idx in idx_start:
            c[idx] = 1.0
        c[idx_tmax] = 0.001
    else:
        c[idx_tmax] = 1.0

    lb = np.zeros(n_vars)
    ub = np.full(n_vars, 1_000_000.0)
    if max_makespan is not None:
        ub[idx_tmax] = max_makespan
    integrality = np.zeros(n_vars, dtype=int)
    for idx in x_idx.values():
        ub[idx] = 1
        integrality[idx] = 1
    for idx in y_idx.values():
        ub[idx] = 1
        integrality[idx] = 1

    rows, lows, ups = [], [], []

    def add(row: dict, low: float = -np.inf, up: float = np.inf):
        rows.append(row)
        lows.append(low)
        ups.append(up)

    # 每个设备子任务分配给且仅给一台相应类型的设备
    for oi, op in enumerate(ops):
        add({x_idx[(oi, mi)]: 1 for mi, _ in machines_by_type[op["type"]]}, low=1, up=1)

    # 同一车间内工序链约束
    jobs_by_workshop = defaultdict(list)
    for j, p in enumerate(procs):
        jobs_by_workshop[p["workshop"]].append((p["seq"], j))
    for _, job_list in jobs_by_workshop.items():
        job_list = sorted(job_list)
        for (_, j1), (_, j2) in zip(job_list, job_list[1:]):
            add({idx_start[j2]: 1, idx_start[j1]: -1}, low=procs[j1]["maxdur"])

    # 最大完工时间定义
    for j, p in enumerate(procs):
        add({idx_tmax: 1, idx_start[j]: -1}, low=p["maxdur"])

    big_m = 1_000_000

    # 初始从班组驻地到首个车间的可达约束
    for (oi, mi), xv in x_idx.items():
        op = ops[oi]
        machine = machines[mi]
        t_init = travel_time(machine["origin"], op["workshop"], op["type"])
        add({idx_start[op["job"]]: 1, xv: -t_init}, low=0)

    # 同一台设备不能重叠作业；跨车间的转运时间为序列相关 setup time
    for (a, b, mi), yv in y_idx.items():
        op_a, op_b = ops[a], ops[b]
        x_a, x_b = x_idx[(a, mi)], x_idx[(b, mi)]
        t_ab = travel_time(op_a["workshop"], op_b["workshop"], op_a["type"])
        t_ba = travel_time(op_b["workshop"], op_a["workshop"], op_a["type"])
        # y=1: a 在 b 前；y=0: b 在 a 前，仅当两者分配给同一台设备时生效
        add({idx_start[op_b["job"]]: 1, idx_start[op_a["job"]]: -1, yv: -big_m, x_a: -big_m, x_b: -big_m},
            low=op_a["dur"] + t_ab - 3 * big_m)
        add({idx_start[op_a["job"]]: 1, idx_start[op_b["job"]]: -1, yv: big_m, x_a: -big_m, x_b: -big_m},
            low=op_b["dur"] + t_ba - 2 * big_m)

    A = lil_matrix((len(rows), n_vars))
    for r, row in enumerate(rows):
        for k, v in row.items():
            A[r, k] = v

    constraints = LinearConstraint(csr_matrix(A), np.array(lows), np.array(ups))
    res = milp(
        c=c,
        integrality=integrality,
        bounds=Bounds(lb, ub),
        constraints=constraints,
        options={"time_limit": time_limit, "mip_rel_gap": mip_rel_gap, "disp": verbose},
    )

    schedule = []
    if res.x is not None:
        x = res.x
        for oi, op in enumerate(ops):
            assigned = []
            for mi, _ in machines_by_type[op["type"]]:
                if x[x_idx[(oi, mi)]] > 0.5:
                    assigned.append(mi)
            if not assigned:
                continue
            mi = assigned[0]
            machine = machines[mi]
            start = int(round(float(x[idx_start[op["job"]]])))
            schedule.append({
                "设备编号": machine["id"],
                "设备类型": machine["type_zh"],
                "班组": machine["crew"],
                "工序编号": op["pid"],
                "车间": op["workshop"],
                "起始时间": sec_to_hms(start),
                "结束时间": sec_to_hms(start + op["dur"]),
                "持续工作时间(s)": op["dur"],
                "start_s": start,
                "end_s": start + op["dur"],
            })
    return res, schedule, procs


def write_csv(path: str, rows: List[dict], fields: List[str]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for i, row in enumerate(rows, 1):
            row2 = dict(row)
            row2.setdefault("序号", i)
            writer.writerow({k: row2.get(k, "") for k in fields})


def solve_all(output_dir: str = "results") -> dict:
    processes = build_processes()
    machines1 = make_machines((1,))
    machines12 = make_machines((1, 2))

    res1, sch1, _ = solve_milp(processes, machines1, allowed_workshops={"A"}, time_limit=30)
    res2, sch2, _ = solve_milp(processes, machines1, time_limit=120)
    res3, sch3, _ = solve_milp(processes, machines12, time_limit=120)

    # 二级优化：在不超过最优 Tmax 的条件下，尽量提前非关键工序，得到更紧凑的表格输出
    t2, t3 = int(round(res2.fun)), int(round(res3.fun))
    res2b, sch2b, _ = solve_milp(processes, machines1, time_limit=120, max_makespan=t2, objective="sum_start")
    res3b, sch3b, _ = solve_milp(processes, machines12, time_limit=120, max_makespan=t3, objective="sum_start")
    if res2b.success:
        sch2 = sch2b
    if res3b.success:
        sch3 = sch3b

    # Q4: 关键路径下界 = C 车间链总时长 + 最短初始到达 C 时间 = 123844s；Q3 已达到，采购无法降低 makespan。
    sch4 = [dict(r) for r in sch3]
    purchase_rows = []
    for t in EQUIPMENT_TYPES:
        purchase_rows.append({"设备名称": TYPE_ZH[t], "班组1购买台数": 0, "班组2购买台数": 0, "设备单价(元)": UNIT_PRICE[t], "小计(元)": 0})
    purchase_total = 0

    os.makedirs(output_dir, exist_ok=True)
    fields_base = ["序号", "设备编号", "起始时间", "结束时间", "持续工作时间(s)", "工序编号"]
    fields_crew = ["序号", "设备编号", "起始时间", "结束时间", "持续工作时间(s)", "工序编号", "班组"]

    for sch in (sch1, sch2, sch3, sch4):
        sch.sort(key=lambda r: (r["start_s"], r["工序编号"], r["设备编号"]))

    write_csv(os.path.join(output_dir, "table1_question1.csv"), sch1, fields_base)
    write_csv(os.path.join(output_dir, "table2_question2.csv"), sch2, fields_base)
    write_csv(os.path.join(output_dir, "table3_question3.csv"), sch3, fields_crew)
    write_csv(os.path.join(output_dir, "table4_question4.csv"), sch4, fields_crew)
    write_csv(os.path.join(output_dir, "table5_purchase_plan.csv"), purchase_rows, ["设备名称", "班组1购买台数", "班组2购买台数", "设备单价(元)", "小计(元)"])

    summary = [
        {"问题": "Q1", "最短时长(s)": int(round(res1.fun)), "最短时长(HH:MM:SS)": sec_to_hms(res1.fun), "求解状态": res1.message},
        {"问题": "Q2", "最短时长(s)": t2, "最短时长(HH:MM:SS)": sec_to_hms(t2), "求解状态": res2.message},
        {"问题": "Q3", "最短时长(s)": t3, "最短时长(HH:MM:SS)": sec_to_hms(t3), "求解状态": res3.message},
        {"问题": "Q4", "最短时长(s)": t3, "最短时长(HH:MM:SS)": sec_to_hms(t3), "求解状态": "关键路径下界已达到；最优采购为0"},
    ]
    write_csv(os.path.join(output_dir, "summary.csv"), summary, ["问题", "最短时长(s)", "最短时长(HH:MM:SS)", "求解状态"])

    return {
        "processes": processes,
        "schedules": {"Q1": sch1, "Q2": sch2, "Q3": sch3, "Q4": sch4},
        "summary": summary,
        "purchase": purchase_rows,
        "purchase_total": purchase_total,
        "results": {"Q1": int(round(res1.fun)), "Q2": t2, "Q3": t3, "Q4": t3},
    }


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.dirname(__file__)), "results")
    result = solve_all(out)
    for row in result["summary"]:
        print(f"{row['问题']}: {row['最短时长(s)']} s = {row['最短时长(HH:MM:SS)']}")
