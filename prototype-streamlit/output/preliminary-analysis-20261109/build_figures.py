"""Figures from the team's supplied notebook results; does not modify the app."""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".matplotlib"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, FixedFormatter
import numpy as np

plt.rcParams.update({
    "font.family": "Malgun Gothic",
    "axes.unicode_minus": False,
    "svg.fonttype": "path",
    "font.size": 12,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "axes.edgecolor": "#D9E1E6",
    "text.color": "#142F42",
    "axes.labelcolor": "#526573",
    "xtick.color": "#526573",
    "ytick.color": "#142F42",
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
})

BLUE = "#185DAC"
TEAL = "#187A72"
INK = "#142F42"
MUTED = "#526573"
OTHER = "#A7B5C2"


def seconds(days=0, hours=0, minutes=0, secs=0):
    return days * 86400 + hours * 3600 + minutes * 60 + secs


ROUTES = [
    {
        "name": "DGT ODT", "total_n": 122, "stage_n": 122,
        "mean_h": 203.43, "median_h": 152.95,
        "stages": [
            ("반입 → 야드 장치", seconds(minutes=13, secs=19), "other"),
            ("야드 장치 → 온샤시", seconds(days=8, hours=10, minutes=34, secs=24), "yard1"),
            ("온샤시 → 반출", seconds(minutes=37, secs=58), "other"),
        ],
    },
    {
        "name": "HJNC ODT", "total_n": 1490, "stage_n": 1490,
        "mean_h": 196.18, "median_h": 169.23,
        "stages": [
            ("반입 → 야드 장치", seconds(minutes=6, secs=34), "other"),
            ("야드 장치 → 온샤시", seconds(days=8, hours=3, minutes=53, secs=51), "yard1"),
            ("온샤시 → 반출", seconds(minutes=10, secs=22), "other"),
        ],
    },
    {
        "name": "DGT → HJNC ITT", "total_n": 17389, "stage_n": 17389,
        "mean_h": 217.40, "median_h": 175.45,
        "stages": [
            ("DGT 반입 → 장치", seconds(minutes=13, secs=24), "other"),
            ("DGT 장치 → 온샤시", seconds(days=6, hours=15, minutes=28, secs=22), "yard1"),
            ("DGT 온샤시 → 반출", seconds(minutes=5, secs=37), "other"),
            ("터미널 간 이동", seconds(minutes=9, secs=27), "other"),
            ("HJNC 반입 → 장치", seconds(minutes=7, secs=28), "other"),
            ("HJNC 장치 → 온샤시", seconds(days=2, hours=9, minutes=7, secs=53), "yard2"),
            ("HJNC 온샤시 → 반출", seconds(minutes=11, secs=29), "other"),
        ],
    },
    {
        "name": "HJNC → DGT ITT", "total_n": 20143, "stage_n": 20143,
        "mean_h": 178.96, "median_h": 144.17,
        "stages": [
            ("HJNC 반입 → 장치", seconds(minutes=7, secs=17), "other"),
            ("HJNC 장치 → 온샤시", seconds(days=4, hours=19, minutes=27, secs=31), "yard1"),
            ("HJNC 온샤시 → 반출", seconds(minutes=4, secs=31), "other"),
            ("터미널 간 이동", seconds(minutes=10, secs=36), "other"),
            ("DGT 반입 → 장치", seconds(minutes=22, secs=47), "other"),
            ("DGT 장치 → 온샤시", seconds(days=2, hours=14, minutes=10, secs=49), "yard2"),
            ("DGT 온샤시 → 반출", seconds(minutes=33, secs=58), "other"),
        ],
    },
]


def duration(value):
    days, remainder = divmod(value, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, secs = divmod(remainder, 60)
    units = [(days, "일"), (hours, "시간"), (minutes, "분"), (secs, "초")]
    return " ".join(f"{number}{unit}" for number, unit in units if number)


def save(fig, name):
    fig.savefig(ROOT / f"{name}.png", dpi=180, bbox_inches="tight", pad_inches=.04)
    fig.savefig(ROOT / f"{name}.svg", bbox_inches="tight", pad_inches=.04)
    plt.close(fig)


def align_category_labels(fig, axes, left_edges, right_edges):
    """Reserve only the measured label width, rather than a large fixed gutter."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    offsets = []
    for ax in axes:
        label_left = min(label.get_window_extent(renderer).x0 for label in ax.get_yticklabels())
        offsets.append((ax.get_window_extent(renderer).x0 - label_left) / fig.bbox.width)
    label_offset = max(offsets)
    for ax, left_edge, right_edge in zip(axes, left_edges, right_edges):
        position = ax.get_position()
        left = left_edge + label_offset
        ax.set_position([left, position.y0, right_edge - left, position.height])


def overall():
    fig, ax = plt.subplots(figsize=(12.8, 5.2))
    fig.subplots_adjust(left=.20, right=.96, top=.825, bottom=.16)
    fig.text(.035, .98, "환적 전체 소요시간", fontsize=24, weight="bold", va="top")
    fig.text(.035, .86, "최초 반입부터 최종 반출까지 · 타부두 환적은 터미널 간 이동 포함", color=MUTED)
    positions = np.arange(len(ROUTES))
    means = [route["mean_h"] for route in ROUTES]
    medians = [route["median_h"] for route in ROUTES]
    ax.barh(positions, means, height=.48, color=BLUE, zorder=2)
    ax.scatter(medians, positions, marker="D", s=68, color="white", edgecolor=INK,
               linewidth=1.5, zorder=3)
    for y, route in zip(positions, ROUTES):
        ax.text(route["mean_h"] + 3, y, f'{route["mean_h"]:.2f}', va="center", weight="bold")
        ax.annotate(f'{route["median_h"]:.2f}', (route["median_h"], y),
                    xytext=(0, 17), textcoords="offset points", ha="center", fontsize=10,
                    color=MUTED)
    ax.set_yticks(positions, [r["name"] for r in ROUTES])
    ax.tick_params(axis="both", length=0, pad=12)
    ax.invert_yaxis()
    ax.set_ylim(3.33, -.33)
    ax.set_xlim(0, 245)
    ax.set_xticks([0, 50, 100, 150, 200])
    ax.set_xlabel("소요시간 (시간)", labelpad=12)
    ax.set_axisbelow(True)
    ax.grid(axis="x", color="#E6ECF1", linewidth=.8)
    fig.legend(handles=[Line2D([0], [0], color=BLUE, linewidth=7, label="평균"),
                        Line2D([0], [0], marker="D", color="none", markerfacecolor="white",
                               markeredgecolor=INK, markersize=7, label="중앙값")],
               loc="upper right", bbox_to_anchor=(.97, .98), ncol=2, frameon=False)
    align_category_labels(fig, [ax], [.035], [.96])
    save(fig, "01-total-duration-v4")


def stage_detail():
    colors = {"yard1": BLUE, "yard2": TEAL, "other": OTHER}
    for routes, title, filename in [
        (ROUTES[:2], "자부두 환적(ODT)의 공정별 평균 소요시간", "02a-odt-stage-duration-v6"),
        (ROUTES[2:], "타부두 환적(ITT)의 공정별 평균 소요시간", "02b-itt-stage-duration-v6"),
    ]:
        fig, axes = plt.subplots(1, 2, figsize=(14, 6.4))
        fig.subplots_adjust(left=.17, right=.97, bottom=.20, top=.76, wspace=.68)
        fig.text(.035, .96, title, fontsize=24, weight="bold", va="top")
        fig.text(.035, .875, "가로축: 로그 눈금",
                 fontsize=12, color=MUTED)
        for ax, route in zip(axes, routes):
            ax.set_title(route["name"], loc="left", fontsize=17, weight="bold", pad=18)
            ax.set_xscale("log")
            ax.set_xlim(1, 30000)
            positions = np.arange(len(route["stages"]))
            for y, (label, value, kind) in zip(positions, route["stages"]):
                is_yard = kind != "other"
                ax.scatter(value / 60, y, color=colors[kind], s=115 if is_yard else 75, zorder=3)
                ax.annotate(duration(value), (value / 60, y),
                            xytext=(-11 if is_yard else 10, 0), textcoords="offset points",
                            ha="right" if is_yard else "left", va="center", fontsize=12,
                            weight="bold" if is_yard else "normal", color=INK)
            ax.set_yticks(positions, [s[0] for s in route["stages"]], fontsize=12)
            ax.set_ylim(len(positions) - .5, -.5)
            for tick, (_, _, kind) in zip(ax.get_yticklabels(), route["stages"]):
                if kind != "other":
                    tick.set_color(colors[kind])
                    tick.set_weight("bold")
            ax.xaxis.set_major_locator(FixedLocator([1, 10, 60, 1440, 14400]))
            ax.xaxis.set_major_formatter(FixedFormatter(["1분", "10분", "1시간", "1일", "10일"]))
            ax.xaxis.set_minor_locator(FixedLocator([]))
            ax.tick_params(axis="both", length=0, pad=9, labelsize=12)
            ax.set_axisbelow(True)
            ax.grid(axis="x", color="#E6ECF1", linewidth=.8)
        legend_items = [(BLUE, "야드 장치 구간"), (OTHER, "그 외 공정")]
        if len(routes[0]["stages"]) > 3:
            legend_items = [(BLUE, "출발 터미널 야드 장치"), (TEAL, "도착 터미널 야드 장치"),
                            (OTHER, "그 외 공정")]
        fig.legend(handles=[Line2D([0], [0], marker="o", color="none", markerfacecolor=color,
                                   markeredgecolor=color, markersize=8, label=label)
                            for color, label in legend_items],
                   loc="lower left", bbox_to_anchor=(.03, .065), frameon=False,
                   ncol=len(legend_items), fontsize=12)
        align_category_labels(fig, axes, [.035, .535], [.48, .98])
        save(fig, filename)


def yard_share():
    fig, ax = plt.subplots(figsize=(12.8, 5.2))
    fig.subplots_adjust(left=.20, right=.82, top=.825, bottom=.18)
    fig.text(.035, .98, "야드 장치 구간이 차지하는 시간 비중", fontsize=24, weight="bold", va="top")
    fig.text(.035, .86, "평균 공정시간 합계 대비 야드 장치 구간 평균시간 합계의 비중", color=MUTED)
    labels = []
    results = []
    for y, route in enumerate(ROUTES):
        total = sum(s[1] for s in route["stages"])
        first = sum(s[1] for s in route["stages"] if s[2] == "yard1")
        second = sum(s[1] for s in route["stages"] if s[2] == "yard2")
        other = total - first - second
        segments = [(first, BLUE), (second, TEAL), (other, OTHER)]
        left = 0
        for value, color in segments:
            share = value / total * 100
            if share:
                ax.barh(y, share, left=left, height=.48, color=color, zorder=2)
                if share > 10:
                    ax.text(left + share / 2, y, f'{share:.1f}%', ha="center", va="center",
                            color="white", fontsize=12, weight="bold")
            left += share
        yard_pct = (first + second) / total * 100
        ax.text(102.5, y, f'야드 합계 약 {yard_pct:.2f}%', va="center", fontsize=12, weight="bold")
        labels.append(route["name"])
        results.append({"route": route["name"], "total_n": route["total_n"], "stage_n": route["stage_n"],
                        "reported_total_mean_h": route["mean_h"], "reported_total_median_h": route["median_h"],
                        "stage_mean_sum_h": total / 3600, "yard_mean_sum_h": (first + second) / 3600,
                        "yard_share_pct": yard_pct, "other_share_pct": other / total * 100})
    ax.set_yticks(range(4), labels)
    ax.invert_yaxis()
    ax.set_ylim(3.33, -.33)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
    ax.tick_params(axis="both", length=0, pad=12)
    ax.set_xlabel("평균 공정시간 합계 대비 비중", labelpad=12)
    ax.set_axisbelow(True)
    ax.grid(axis="x", color="#E6ECF1", linewidth=.8, zorder=0)
    fig.legend(handles=[Line2D([0], [0], color=color, linewidth=7, label=label)
                        for color, label in [(BLUE, "첫 번째 터미널 야드 장치"),
                                             (TEAL, "두 번째 터미널 야드 장치"),
                                             (OTHER, "그 외 공정")]],
               loc="upper right", bbox_to_anchor=(.97, .995), frameon=False, ncol=3, fontsize=10,
               handlelength=1.5, handletextpad=.6, columnspacing=1.0)
    fig.text(.035, .015, "초 단위로 절삭된 공정 평균을 합산한 근사 비중이며, 컨테이너별 비중의 평균과는 구분됩니다.", fontsize=9, color=MUTED)
    align_category_labels(fig, [ax], [.035], [.82])
    save(fig, "03-yard-share-v5")
    (ROOT / "figure-data.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return results


if __name__ == "__main__":
    overall()
    stage_detail()
    results = yard_share()
    for result in results:
        print(json.dumps(result, ensure_ascii=False))
