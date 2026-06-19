# -*- coding: utf-8 -*-
"""Regenerate paper figures from baseline CSV result tables.

Outputs:
- docs/figures/gantt_q1.png ... docs/figures/gantt_q4.png
- docs/figures/makespan_summary.png
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib.pyplot as plt
from matplotlib.patches import Patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULT_DIR = PROJECT_ROOT / "baseline_v1" / "results"
FIGURE_DIR = PROJECT_ROOT / "docs" / "figures"

WORKSHOP_COLORS = {
    "A": "#4C78A8",
    "B": "#F58518",
    "C": "#54A24B",
    "D": "#E45756",
    "E": "#72B7B2",
    "?": "#9D9DA1",
}


def hms_to_seconds(value: str) -> int:
    hour, minute, second = (int(part) for part in value.split(":"))
    return hour * 3600 + minute * 60 + second


def seconds_to_hm(value: int | float) -> str:
    value = int(round(value))
    return f"{value // 3600:02d}:{(value % 3600) // 60:02d}"


def workshop_of(pid: str) -> str:
    return pid[0] if pid else "?"


def read_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def plot_gantt(csv_name: str, output_name: str, title: str) -> None:
    rows = read_rows(RESULT_DIR / csv_name)
    rows = sorted(rows, key=lambda row: (row["设备编号"], hms_to_seconds(row["起始时间"])))
    machines = sorted({row["设备编号"] for row in rows})
    y_index = {machine: idx for idx, machine in enumerate(machines)}
    machine_labels = {machine: f"M{idx + 1}" for idx, machine in enumerate(machines)}

    height = max(4.5, 0.34 * len(machines) + 1.8)
    fig, ax = plt.subplots(figsize=(13, height))

    for row in rows:
        start = hms_to_seconds(row["起始时间"])
        duration = int(row["持续工作时间(s)"])
        pid = row["工序编号"]
        workshop = workshop_of(pid)
        y = y_index[row["设备编号"]]
        ax.barh(
            y,
            duration,
            left=start,
            height=0.72,
            color=WORKSHOP_COLORS.get(workshop, WORKSHOP_COLORS["?"]),
            edgecolor="black",
            linewidth=0.4,
        )
        if duration >= 3000:
            ax.text(
                start + duration / 2,
                y,
                pid,
                ha="center",
                va="center",
                fontsize=7,
                color="white",
            )

    ax.set_yticks(range(len(machines)))
    ax.set_yticklabels([machine_labels[machine] for machine in machines], fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel("Time (HH:MM)")
    ax.set_title(title)
    max_end = max(hms_to_seconds(row["结束时间"]) for row in rows)
    ticks = list(range(0, max_end + 1, 4 * 3600))
    if max_end not in ticks:
        ticks.append(max_end)
    ax.set_xticks(ticks)
    ax.set_xticklabels([seconds_to_hm(tick) for tick in ticks], rotation=30, ha="right")
    ax.grid(axis="x", linestyle="--", alpha=0.35)
    legend = [
        Patch(facecolor=color, edgecolor="black", label=f"Workshop {workshop}")
        for workshop, color in WORKSHOP_COLORS.items()
        if workshop != "?"
    ]
    ax.legend(handles=legend, loc="upper right", fontsize=8)
    fig.tight_layout()
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE_DIR / output_name, dpi=220)
    plt.close(fig)


def plot_makespan_summary() -> None:
    rows = read_rows(RESULT_DIR / "summary.csv")
    labels = [row["问题"] for row in rows]
    values = [int(row["最短时长(s)"]) for row in rows]

    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    colors = ["#4C78A8", "#F58518", "#54A24B", "#E45756"]
    bars = ax.bar(labels, values, color=colors, edgecolor="black", linewidth=0.5)
    ax.set_ylabel("Makespan (s)")
    ax.set_title("Makespan comparison")
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value,
            f"{value}\n{seconds_to_hm(value)}",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    fig.tight_layout()
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE_DIR / "makespan_summary.png", dpi=220)
    plt.close(fig)


def main() -> None:
    plot_gantt("table1_question1.csv", "gantt_q1.png", "Q1 schedule")
    plot_gantt("table2_question2.csv", "gantt_q2.png", "Q2 schedule")
    plot_gantt("table3_question3.csv", "gantt_q3.png", "Q3 schedule")
    plot_gantt("table4_question4.csv", "gantt_q4.png", "Q4 schedule")
    plot_makespan_summary()
    print(f"Figures regenerated in {FIGURE_DIR}")


if __name__ == "__main__":
    main()
