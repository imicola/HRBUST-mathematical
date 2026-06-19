# -*- coding: utf-8 -*-
"""Independent verification models for the B problem solution chain.

This script intentionally does not call the baseline MILP solver.  It reuses the
structured instance data, then builds two smaller CP-SAT models:

1. Q2 bottleneck relaxation: keep only the two single-copy bottleneck resources
   of crew 1 (high-speed polishing machine and automatic sensing machine), plus
   all workshop precedence chains.  Since all other resource conflicts are
   relaxed, its optimum is a valid lower bound for Q2.
2. Q4 explicit purchase model: introduce purchase variables for every candidate
   extra machine allowed by the 500000 yuan budget, solve the integrated
   purchase-and-scheduling model, then minimize purchase cost at the optimal
   makespan.
"""

from __future__ import annotations

import sys
import csv
from collections import defaultdict
from pathlib import Path

from ortools.sat.python import cp_model

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from baseline_v1.code.model_solver import (  # noqa: E402
    BASE_COUNTS,
    EQUIPMENT_TYPES,
    TYPE_ZH,
    UNIT_PRICE,
    build_processes,
    travel_time,
)

BUDGET = 500_000
HORIZON = 300_000
SUMMARY_PATH = PROJECT_ROOT / "baseline_v1" / "results" / "summary.csv"
BOTTLENECK_TYPES = [
    "High-speed Polishing Machine",
    "Automatic Sensing Multi-Function Machine",
]


def sec_to_hms(sec: int | float) -> str:
    sec = int(round(sec))
    return f"{sec // 3600:02d}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


def load_baseline_results() -> dict[str, int]:
    with SUMMARY_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        rows = csv.DictReader(f)
        return {row["问题"]: int(row["最短时长(s)"]) for row in rows}


def add_workshop_chains(model: cp_model.CpModel, starts, processes) -> None:
    by_workshop = defaultdict(list)
    for j, process in enumerate(processes):
        by_workshop[process["workshop"]].append((process["seq"], j))

    for job_list in by_workshop.values():
        for (_, a), (_, b) in zip(sorted(job_list), sorted(job_list)[1:]):
            model.Add(starts[b] >= starts[a] + processes[a]["maxdur"])


def solve_q2_bottleneck_lower_bound():
    """Solve a relaxed Q2 model to produce a machine bottleneck lower bound."""
    processes = build_processes()
    model = cp_model.CpModel()
    starts = [model.NewIntVar(0, HORIZON, f"S_{p['pid']}") for p in processes]
    makespan = model.NewIntVar(0, HORIZON, "makespan")

    for j, process in enumerate(processes):
        # Every required crew-1 machine must at least reach the workshop.
        any_type = next(iter(process["durations"]))
        model.Add(starts[j] >= travel_time("Crew 1", process["workshop"], any_type))
        model.Add(makespan >= starts[j] + process["maxdur"])

    add_workshop_chains(model, starts, processes)

    for equipment_type in BOTTLENECK_TYPES:
        jobs = [j for j, p in enumerate(processes) if equipment_type in p["durations"]]
        for idx, a in enumerate(jobs):
            for b in jobs[idx + 1 :]:
                before = model.NewBoolVar(
                    f"{equipment_type}_{processes[a]['pid']}_before_{processes[b]['pid']}"
                )
                pa, pb = processes[a], processes[b]
                model.Add(
                    starts[b]
                    >= starts[a]
                    + pa["durations"][equipment_type]
                    + travel_time(pa["workshop"], pb["workshop"], equipment_type)
                ).OnlyEnforceIf(before)
                model.Add(
                    starts[a]
                    >= starts[b]
                    + pb["durations"][equipment_type]
                    + travel_time(pb["workshop"], pa["workshop"], equipment_type)
                ).OnlyEnforceIf(before.Not())

    model.Minimize(makespan)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 1
    status = solver.Solve(model)
    if status != cp_model.OPTIMAL:
        raise RuntimeError(f"Q2 bottleneck relaxation was not proven optimal: {solver.StatusName(status)}")

    sequences = {}
    for equipment_type in BOTTLENECK_TYPES:
        jobs = [j for j, p in enumerate(processes) if equipment_type in p["durations"]]
        sequences[equipment_type] = [
            {
                "pid": processes[j]["pid"],
                "workshop": processes[j]["workshop"],
                "start": solver.Value(starts[j]),
                "end": solver.Value(starts[j]) + processes[j]["durations"][equipment_type],
                "duration": processes[j]["durations"][equipment_type],
                "job_maxdur": processes[j]["maxdur"],
            }
            for j in sorted(jobs, key=lambda k: solver.Value(starts[k]))
        ]

    return {
        "status": solver.StatusName(status),
        "objective": int(round(solver.ObjectiveValue())),
        "best_bound": int(round(solver.BestObjectiveBound())),
        "sequences": sequences,
    }


def build_q4_purchase_machines():
    machines = []
    for crew in (1, 2):
        for equipment_type in EQUIPMENT_TYPES:
            base_count = BASE_COUNTS[crew][equipment_type]
            for i in range(1, base_count + 1):
                machines.append(
                    {
                        "id": f"{TYPE_ZH[equipment_type]}{crew}-{i}",
                        "type": equipment_type,
                        "crew": crew,
                        "origin": f"Crew {crew}",
                        "base": True,
                        "price": 0,
                    }
                )

            max_extra = BUDGET // UNIT_PRICE[equipment_type]
            for i in range(1, max_extra + 1):
                machines.append(
                    {
                        "id": f"{TYPE_ZH[equipment_type]}{crew}-增购{i}",
                        "type": equipment_type,
                        "crew": crew,
                        "origin": f"Crew {crew}",
                        "base": False,
                        "price": UNIT_PRICE[equipment_type],
                    }
                )
    return machines


def build_q4_purchase_model():
    processes = build_processes()
    machines = build_q4_purchase_machines()

    machines_by_type = defaultdict(list)
    for mi, machine in enumerate(machines):
        machines_by_type[machine["type"]].append(mi)

    operations = []
    for j, process in enumerate(processes):
        for equipment_type, duration in process["durations"].items():
            operations.append(
                {
                    "job": j,
                    "pid": process["pid"],
                    "workshop": process["workshop"],
                    "type": equipment_type,
                    "duration": duration,
                }
            )

    model = cp_model.CpModel()
    starts = [model.NewIntVar(0, HORIZON, f"S_{p['pid']}") for p in processes]
    makespan = model.NewIntVar(0, HORIZON, "makespan")

    purchase = {}
    for mi, machine in enumerate(machines):
        if not machine["base"]:
            purchase[mi] = model.NewBoolVar(f"buy_{machine['id']}")

    assign = {}
    operations_by_type = defaultdict(list)
    for oi, operation in enumerate(operations):
        operations_by_type[operation["type"]].append(oi)
        choices = []
        for mi in machines_by_type[operation["type"]]:
            chosen = model.NewBoolVar(f"x_{oi}_{mi}")
            assign[(oi, mi)] = chosen
            choices.append(chosen)

            machine = machines[mi]
            if mi in purchase:
                model.AddImplication(chosen, purchase[mi])

            model.Add(
                starts[operation["job"]]
                >= travel_time(machine["origin"], operation["workshop"], operation["type"])
            ).OnlyEnforceIf(chosen)

        model.AddExactlyOne(choices)

    model.Add(sum(machines[mi]["price"] * z for mi, z in purchase.items()) <= BUDGET)
    add_workshop_chains(model, starts, processes)

    for j, process in enumerate(processes):
        model.Add(makespan >= starts[j] + process["maxdur"])

    pairwise_count = 0
    for equipment_type, op_list in operations_by_type.items():
        for mi in machines_by_type[equipment_type]:
            for idx, a in enumerate(op_list):
                for b in op_list[idx + 1 :]:
                    both = model.NewBoolVar(f"both_{a}_{b}_{mi}")
                    before = model.NewBoolVar(f"before_{a}_{b}_{mi}")
                    model.AddBoolAnd([assign[(a, mi)], assign[(b, mi)]]).OnlyEnforceIf(both)
                    model.AddBoolOr([assign[(a, mi)].Not(), assign[(b, mi)].Not(), both])

                    oa, ob = operations[a], operations[b]
                    model.Add(
                        starts[ob["job"]]
                        >= starts[oa["job"]]
                        + oa["duration"]
                        + travel_time(oa["workshop"], ob["workshop"], equipment_type)
                    ).OnlyEnforceIf([both, before])
                    model.Add(
                        starts[oa["job"]]
                        >= starts[ob["job"]]
                        + ob["duration"]
                        + travel_time(ob["workshop"], oa["workshop"], equipment_type)
                    ).OnlyEnforceIf([both, before.Not()])
                    pairwise_count += 1

    purchase_cost = model.NewIntVar(0, BUDGET, "purchase_cost")
    model.Add(purchase_cost == sum(machines[mi]["price"] * z for mi, z in purchase.items()))

    return {
        "model": model,
        "machines": machines,
        "purchase": purchase,
        "makespan": makespan,
        "purchase_cost": purchase_cost,
        "stats": {
            "candidate_machines": len(machines),
            "candidate_extra_machines": len(purchase),
            "assignment_variables": len(assign),
            "pairwise_order_variables": pairwise_count,
        },
    }


def solve_q4_explicit_purchase():
    built = build_q4_purchase_model()
    model = built["model"]

    model.Minimize(built["makespan"])
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 1
    status = solver.Solve(model)
    if status != cp_model.OPTIMAL:
        raise RuntimeError(f"Q4 purchase stage 1 was not proven optimal: {solver.StatusName(status)}")

    first_stage = {
        "status": solver.StatusName(status),
        "objective": int(round(solver.ObjectiveValue())),
        "best_bound": int(round(solver.BestObjectiveBound())),
        "wall_time": solver.WallTime(),
    }

    optimal_makespan = int(round(solver.ObjectiveValue()))
    model.Add(built["makespan"] <= optimal_makespan)
    model.Minimize(built["purchase_cost"])

    solver2 = cp_model.CpSolver()
    solver2.parameters.max_time_in_seconds = 60
    solver2.parameters.num_search_workers = 1
    solver2.parameters.random_seed = 1
    status2 = solver2.Solve(model)
    if status2 != cp_model.OPTIMAL:
        raise RuntimeError(f"Q4 purchase stage 2 was not proven optimal: {solver2.StatusName(status2)}")
    purchased = [
        built["machines"][mi]["id"]
        for mi, z in built["purchase"].items()
        if solver2.Value(z)
    ]
    second_stage = {
        "status": solver2.StatusName(status2),
        "purchase_cost": int(round(solver2.ObjectiveValue())),
        "best_bound": int(round(solver2.BestObjectiveBound())),
        "makespan": solver2.Value(built["makespan"]),
        "wall_time": solver2.WallTime(),
        "purchased": purchased,
    }

    return {
        "first_stage": first_stage,
        "second_stage": second_stage,
        "stats": built["stats"],
    }


def print_q2(result, baseline_results: dict[str, int]) -> None:
    print("Q2 bottleneck relaxation lower bound")
    print(f"status: {result['status']}")
    print(f"objective: {result['objective']} s = {sec_to_hms(result['objective'])}")
    print(f"best_bound: {result['best_bound']} s")
    print(f"baseline_q2: {baseline_results['Q2']} s")
    print(f"matches_baseline: {result['objective'] == baseline_results['Q2']}")
    for equipment_type, sequence in result["sequences"].items():
        print(f"\n{TYPE_ZH[equipment_type]} bottleneck sequence")
        for item in sequence:
            print(
                f"  {item['pid']:6s} {item['workshop']} "
                f"{sec_to_hms(item['start'])}-{sec_to_hms(item['end'])} "
                f"dur={item['duration']} job_max={item['job_maxdur']}"
            )


def print_q4(result, baseline_results: dict[str, int]) -> None:
    print("\nQ4 explicit purchase-and-scheduling CP-SAT model")
    print("model_stats:")
    for key, value in result["stats"].items():
        print(f"  {key}: {value}")

    first = result["first_stage"]
    print("stage_1_min_makespan:")
    print(f"  status: {first['status']}")
    print(f"  objective: {first['objective']} s = {sec_to_hms(first['objective'])}")
    print(f"  best_bound: {first['best_bound']} s")
    print(f"  baseline_q3_q4: {baseline_results['Q3']} s / {baseline_results['Q4']} s")
    print(f"  matches_q3_q4_baseline: {first['objective'] == baseline_results['Q3'] == baseline_results['Q4']}")

    second = result["second_stage"]
    if second is not None:
        print("stage_2_min_purchase_cost_at_optimal_makespan:")
        print(f"  status: {second['status']}")
        print(f"  makespan: {second['makespan']} s = {sec_to_hms(second['makespan'])}")
        print(f"  purchase_cost: {second['purchase_cost']} yuan")
        print(f"  purchased_count: {len(second['purchased'])}")
        print(f"  purchased: {second['purchased']}")


def main() -> None:
    baseline_results = load_baseline_results()
    q2 = solve_q2_bottleneck_lower_bound()
    q4 = solve_q4_explicit_purchase()
    print_q2(q2, baseline_results)
    print_q4(q4, baseline_results)


if __name__ == "__main__":
    main()
