"""
跨境算力调度仿真实验脚本（增强版）

更新点：
1. 增加“加权平均”多目标调度实验；
2. 增加组件消融实验：无能耗、无负载、无成本、无延迟；
3. 输出多指标结果表和高级可视化图表；
4. 支持生成可复现实验数据和图表文件。
"""

from __future__ import annotations

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
from matplotlib import font_manager as fm

OUT = "outputs"
os.makedirs(OUT, exist_ok=True)

FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT = fm.FontProperties(fname=FONT_PATH) if os.path.exists(FONT_PATH) else None
matplotlib.rcParams["axes.unicode_minus"] = False

NODES = [
    {"name": "重庆", "gpu": 10, "gpu_cost": 2.0, "green": 0.60, "rtt": {"中国": 20, "东南亚": 50, "中亚": 80}},
    {"name": "海南", "gpu": 6, "gpu_cost": 2.5, "green": 0.80, "rtt": {"中国": 15, "东南亚": 20, "中亚": 100}},
    {"name": "香港", "gpu": 8, "gpu_cost": 3.0, "green": 0.70, "rtt": {"中国": 15, "东南亚": 30, "中亚": 90}},
    {"name": "新加坡", "gpu": 12, "gpu_cost": 3.5, "green": 0.50, "rtt": {"中国": 25, "东南亚": 10, "中亚": 120}},
    {"name": "新疆", "gpu": 4, "gpu_cost": 1.5, "green": 0.90, "rtt": {"中国": 30, "东南亚": 80, "中亚": 60}},
]

LATENCY_WEIGHT = {"高": 1.0, "中": 0.55, "低": 0.25}


def build_tasks(seed: int = 7, n: int = 30) -> list[dict]:
    rng = np.random.default_rng(seed)
    tasks: list[dict] = []
    for i in range(n):
        task_type = rng.choice(["训练", "推理", "渲染", "仿真"], p=[0.25, 0.35, 0.25, 0.15])
        gpu_req = int(rng.choice([1, 2, 4], p=[0.55, 0.35, 0.10]))
        region = str(rng.choice(["中国", "东南亚", "中亚"], p=[0.45, 0.40, 0.15]))
        sensitivity = str(rng.choice(["高", "中", "低"], p=[0.35, 0.45, 0.20]))
        runtime = float(rng.uniform(8, 45) if task_type in ["训练", "仿真"] else rng.uniform(3, 18))
        budget = float(rng.uniform(35, 220))
        deadline = float(rng.uniform(60, 230) if sensitivity == "高" else rng.uniform(120, 330))
        tasks.append({
            "id": i + 1,
            "type": task_type,
            "gpu_required": gpu_req,
            "region": region,
            "sensitivity": sensitivity,
            "runtime": runtime,
            "budget": budget,
            "deadline": deadline,
        })
    return tasks


def estimate(task: dict, node: dict) -> tuple[float, float, float]:
    latency = node["rtt"][task["region"]] + task["runtime"]
    cost = task["gpu_required"] * node["gpu_cost"] * task["runtime"]
    energy = task["gpu_required"] * task["runtime"] * (1 - node["green"])
    return latency, cost, energy


def feasible(task: dict, node: dict, state: dict) -> bool:
    if state[node["name"]]["gpu"] < task["gpu_required"]:
        return False
    latency, cost, _ = estimate(task, node)
    return latency <= task["deadline"] and cost <= task["budget"]


def score_weighted(task: dict, candidate: tuple, mode: str) -> float:
    _, latency, cost, energy, load = candidate
    weights = {
        "latency": LATENCY_WEIGHT[task["sensitivity"]],
        "cost": 0.025,
        "energy": 0.12,
        "load": 20.0,
    }
    if mode == "加权平均":
        weights = {"latency": 0.50, "cost": 0.30, "energy": 0.15, "load": 0.05}
    elif mode == "权重调度-无能耗":
        weights["energy"] = 0
    elif mode == "权重调度-无负载":
        weights["load"] = 0
    elif mode == "权重调度-无成本":
        weights["cost"] = 0
    elif mode == "权重调度-无延迟":
        weights["latency"] = 0

    return (
        weights["latency"] * latency
        + weights["cost"] * cost
        + weights["energy"] * energy
        + weights["load"] * load
    )


def run_scheduler(tasks: list[dict], mode: str) -> tuple[list[dict], list[dict], dict]:
    state = {n["name"]: {"gpu": n["gpu"], "tasks": []} for n in NODES}
    assignments: list[dict] = []
    unscheduled: list[dict] = []

    for task in tasks:
        if mode == "静态本地":
            fixed = {"中国": "重庆", "东南亚": "新加坡", "中亚": "新疆"}[task["region"]]
            candidate_nodes = [n for n in NODES if n["name"] == fixed]
        else:
            candidate_nodes = NODES

        candidates = []
        for node in candidate_nodes:
            if feasible(task, node, state):
                latency, cost, energy = estimate(task, node)
                load = (node["gpu"] - state[node["name"]]["gpu"]) / node["gpu"]
                candidates.append((node, latency, cost, energy, load))

        if not candidates:
            unscheduled.append(task)
            continue

        if mode == "先到先服务":
            selected = candidates[0]
        elif mode == "最小延迟":
            selected = min(candidates, key=lambda x: x[1])
        elif mode in ["最小成本", "静态本地"]:
            selected = min(candidates, key=lambda x: x[2])
        else:
            selected = min(candidates, key=lambda x: score_weighted(task, x, mode))

        node, latency, cost, energy, load = selected
        state[node["name"]]["gpu"] -= task["gpu_required"]
        state[node["name"]]["tasks"].append(task["id"])
        assignments.append({
            "task_id": task["id"],
            "node": node["name"],
            "region": task["region"],
            "type": task["type"],
            "gpu": task["gpu_required"],
            "latency": latency,
            "cost": cost,
            "energy": energy,
        })

    return assignments, unscheduled, state


def calc_metrics(tasks: list[dict], mode: str) -> dict:
    assignments, unscheduled, _ = run_scheduler(tasks, mode)
    n = len(assignments)
    total = len(tasks)
    total_gpu = sum(node["gpu"] for node in NODES)
    used_gpu = sum(a["gpu"] for a in assignments)
    return {
        "算法": mode,
        "总任务数": total,
        "成功任务数": n,
        "未调度任务数": len(unscheduled),
        "调度成功率(%)": round(n / total * 100, 2),
        "平均延迟(ms)": round(sum(a["latency"] for a in assignments) / n, 2) if n else 0,
        "平均成本": round(sum(a["cost"] for a in assignments) / n, 2) if n else 0,
        "总成本": round(sum(a["cost"] for a in assignments), 2),
        "平均能耗指标": round(sum(a["energy"] for a in assignments) / n, 2) if n else 0,
        "GPU利用率(%)": round(used_gpu / total_gpu * 100, 2),
        "SLA满足率(%)": round(n / total * 100, 2),
    }


def draw_bar(df: pd.DataFrame, y: str, title: str, path: str) -> None:
    fig = Figure(figsize=(9, 4.8), dpi=160)
    ax = fig.add_subplot(111)
    x = np.arange(len(df))
    colors = [
        (0.984, 0.705, 0.682), (0.702, 0.803, 0.890), (0.800, 0.922, 0.773),
        (1.000, 0.847, 0.651), (0.992, 0.752, 0.812), (0.870, 0.796, 0.894),
        (1.000, 0.929, 0.631), (0.945, 0.867, 0.710), (0.792, 0.698, 0.839),
        (0.753, 0.745, 0.851),
    ]
    bars = ax.bar(x, df[y], color=colors[:len(df)])
    ax.set_title(title, fontproperties=FONT, fontsize=15)
    ax.set_ylabel(y, fontproperties=FONT)
    ax.set_xticks(x)
    ax.set_xticklabels(df["算法"], rotation=25, ha="right", fontproperties=FONT)
    ax.grid(axis="y", alpha=0.25, linestyle="--")
    for bar in bars:
        val = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.3, f"{val:.1f}", ha="center", fontsize=8, fontproperties=FONT)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")


def draw_radar(df: pd.DataFrame, path: str) -> None:
    metrics = ["调度成功率(%)", "GPU利用率(%)", "平均延迟(ms)", "平均成本", "未调度任务数"]
    view = df.copy()
    for m in metrics:
        max_value = view[m].max()
        if m in ["平均延迟(ms)", "平均成本", "未调度任务数"]:
            view[m + "_norm"] = 1 - view[m] / max_value if max_value else 0
        else:
            view[m + "_norm"] = view[m] / max_value if max_value else 0

    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]
    fig = Figure(figsize=(6, 6), dpi=160)
    ax = fig.add_subplot(111, projection="polar")
    colors = [
        (0.12, 0.47, 0.71), (1.00, 0.50, 0.05), (0.17, 0.63, 0.17),
        (0.84, 0.15, 0.16), (0.58, 0.40, 0.74), (0.55, 0.34, 0.29),
        (0.89, 0.47, 0.76), (0.50, 0.50, 0.50), (0.74, 0.74, 0.13),
        (0.09, 0.75, 0.81),
    ]
    for i, (_, row) in enumerate(view.iterrows()):
        values = [row[m + "_norm"] for m in metrics]
        values += values[:1]
        ax.plot(angles, values, color=colors[i % len(colors)], linewidth=1.8, label=row["算法"])
        ax.fill(angles, values, color=colors[i % len(colors)], alpha=0.15)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics, fontproperties=FONT)
    ax.set_title("多指标综合对比雷达图", fontproperties=FONT, fontsize=14, pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1), prop=FONT)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")


def main() -> None:
    tasks = build_tasks()
    modes = [
        "静态本地", "先到先服务", "最小延迟", "最小成本", "权重调度", "加权平均",
        "权重调度-无能耗", "权重调度-无负载", "权重调度-无成本", "权重调度-无延迟",
    ]
    df = pd.DataFrame([calc_metrics(tasks, mode) for mode in modes])
    df.to_csv(os.path.join(OUT, "scheduler_metrics_enhanced.csv"), index=False, encoding="utf-8-sig")
    pd.DataFrame(tasks).to_csv(os.path.join(OUT, "scheduler_tasks.csv"), index=False, encoding="utf-8-sig")

    for mode in modes:
        assignments, _, _ = run_scheduler(tasks, mode)
        pd.DataFrame(assignments).to_csv(os.path.join(OUT, f"assignments_{mode}.csv"), index=False, encoding="utf-8-sig")

    draw_bar(df, "调度成功率(%)", "不同调度算法：调度成功率比较", os.path.join(OUT, "chart_success_rate.png"))
    draw_bar(df, "平均延迟(ms)", "不同调度算法：平均延迟比较", os.path.join(OUT, "chart_latency.png"))
    draw_bar(df, "平均成本", "不同调度算法：平均成本比较", os.path.join(OUT, "chart_cost.png"))
    draw_bar(df, "GPU利用率(%)", "不同调度算法：GPU利用率比较", os.path.join(OUT, "chart_gpu_util.png"))
    draw_bar(df, "未调度任务数", "不同调度算法：未调度任务数比较", os.path.join(OUT, "chart_unscheduled.png"))
    draw_radar(df, os.path.join(OUT, "chart_radar.png"))

    print(df)
    print(f"Outputs saved to: {os.path.abspath(OUT)}")


if __name__ == "__main__":
    main()
