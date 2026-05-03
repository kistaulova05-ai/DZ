"""
Модуль обнаружения WPS-атак

"""

import json
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

# Константы

BLOCK_THRESHOLD = int(os.environ.get("BLOCK_THRESHOLD", "5"))
LOG_FILE        = "1.json"
FAILED_LOG_FILE = "2.json"
CHART_FILE      = os.path.join(os.path.dirname(os.path.dirname(__file__)), "report.png")


# Функции 


def load_attempts(path: str = None) -> list:
    """Загрузка списка попыток подключения из JSON-файла."""
    filepath = path or os.path.join(os.path.dirname(os.path.dirname(__file__)), LOG_FILE)
    try:
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def _resettable_fails(success_series):
    """Счётчик неудачных попыток с обнулением после успешного подключения."""
    counts, count = [], 0
    for s in success_series:
        if s:
            count = 0
        else:
            count += 1
        counts.append(count)
    return counts


def analyze(attempts: list):
    """
    Анализ попыток подключения.

    Возвращает (df, fails, blocked):
      df      – DataFrame с колонками mac, ssid, pin_tried, timestamp, Статус, Блок
      fails   – Series: mac → число неудач
      blocked – set MAC-адресов, превысивших порог
    """
    if not attempts:
        empty = pd.DataFrame(columns=["mac", "ssid", "pin_tried", "timestamp", "success"])
        return empty, pd.Series(dtype=int), set()

    df = pd.DataFrame(attempts)
    df["Статус"] = df["success"].map({True: "УСПЕШНО", False: "НЕУДАЧА"})
    df = df.sort_values("timestamp").reset_index(drop=True)

    df["fail_so_far"] = df.groupby("mac", group_keys=False).apply(
        lambda g: pd.Series(_resettable_fails(g["success"]), index=g.index),
        include_groups=False
    )

    df["Блок"] = df["fail_so_far"].apply(
        lambda x: "ЗАБЛОКИРОВАН" if x >= BLOCK_THRESHOLD else "-"
    )

    fails = (
        df[df["success"] == False]
        .groupby("mac")
        .size()
        .rename("fail_count")
    )

    blocked = set(
        df.groupby("mac")["fail_so_far"]
        .max()
        .pipe(lambda s: s[s >= BLOCK_THRESHOLD])
        .index
    )

    return df, fails, blocked


def save_failed_attempts(df: pd.DataFrame, path: str = None):
    """Сохранение неудачных попыток подключения в JSON-файл."""
    out_path = path or os.path.join(os.path.dirname(os.path.dirname(__file__)), FAILED_LOG_FILE)
    failed = df[df["success"] == False][["mac", "ssid", "pin_tried", "timestamp"]].copy()
    records = failed.to_dict(orient="records")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def get_summary_stats(df: pd.DataFrame, fails: pd.Series, blocked: set) -> dict:
    """
    Формирует сводную статистику для дашборда.

    """
    if df.empty:
        return {
            "total_attempts": 0,
            "unique_macs": 0,
            "blocked_count": 0,
            "active_count": 0,
            "mean_fails": 0.0,
            "max_fails": 0,
            "blocked_macs": [],
        }

    macs = df["mac"].unique().tolist()
    fail_vals = np.array([fails.get(m, 0) for m in macs])

    blocked_list = [
        {"mac": mac, "fails": int(fails.get(mac, 0))}
        for mac in blocked
    ]

    return {
        "total_attempts": len(df),
        "unique_macs": df["mac"].nunique(),
        "blocked_count": len(blocked),
        "active_count": len(macs) - len(blocked),
        "mean_fails": float(np.mean(fail_vals)) if len(fail_vals) else 0.0,
        "max_fails": int(np.max(fail_vals)) if len(fail_vals) else 0,
        "blocked_macs": blocked_list,
    }


def get_fails_by_mac(df: pd.DataFrame, fails: pd.Series, blocked: set) -> list:
    """
    Возвращает список устройств с числом неудач и статусом.
    Используется для гистограммы дашборда.
    """
    if df.empty:
        return []

    total = df.groupby("mac").size().rename("total")
    result = []
    for mac in df["mac"].unique():
        result.append({
            "mac": mac,
            "total": int(total.get(mac, 0)),
            "fails": int(fails.get(mac, 0)),
            "status": "Заблокирован" if mac in blocked else "Активен",
        })
    return sorted(result, key=lambda x: x["fails"], reverse=True)


def get_timeline_data(df: pd.DataFrame) -> dict:
    """
    Возвращает данные для временной шкалы (по часам).
    Группирует успешные и неудачные попытки по времени.
    """
    if df.empty:
        return {"labels": [], "success": [], "failed": []}

    df = df.copy()
    df["hour"] = pd.to_datetime(df["timestamp"]).dt.strftime("%d.%m %H:00")

    grouped = df.groupby(["hour", "success"]).size().unstack(fill_value=0)
    grouped.columns = [str(c) for c in grouped.columns]

    labels = grouped.index.tolist()
    success_data = grouped.get("True", pd.Series(0, index=grouped.index)).tolist()
    failed_data  = grouped.get("False", pd.Series(0, index=grouped.index)).tolist()

    return {"labels": labels, "success": success_data, "failed": failed_data}


def plot_summary(df: pd.DataFrame, fails: pd.Series, blocked: set, out_path: str = None):
    """
    Круговая диаграмма статуса устройств
    Сохраняет PNG.
    """
    if df.empty:
        return

    macs        = df["mac"].unique().tolist()
    fail_vals   = np.array([fails.get(m, 0) for m in macs])
    mean_fail   = np.mean(fail_vals)

    block_count  = len(blocked)
    active_count = len(macs) - block_count

    if block_count == 0 and active_count == 0:
        return

    fig, ax = plt.subplots(figsize=(6, 6))
    fig.suptitle("Статус устройств", fontsize=14, fontweight="bold")

    wedge_colors = ["#e74c3c", "#2ecc71"]
    wedge_labels = [f"Заблокировано\n({block_count})", f"Активен\n({active_count})"]
    explode      = [0.05, 0]

    wedges, texts, autotexts = ax.pie(
        [block_count, active_count],
        labels    = wedge_labels,
        colors    = wedge_colors,
        autopct   = "%1.0f%%",
        startangle= 90,
        explode   = explode,
        textprops = {"fontsize": 11},
        wedgeprops= {"edgecolor": "white", "linewidth": 1.5}
    )
    for at in autotexts:
        at.set_fontweight("bold")

    stats_text = f"Среднее неудачных попыток : {mean_fail:.1f}\n"
    ax.text(0, -1.45, stats_text, ha="center", va="center", fontsize=9,
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#f8f9fa", edgecolor="#bdc3c7"))

    blocked_patch = mpatches.Patch(color="#e74c3c", label="Заблокирован")
    active_patch  = mpatches.Patch(color="#2ecc71", label="Активен")
    ax.legend(handles=[blocked_patch, active_patch], fontsize=9, loc="upper right")

    plt.tight_layout()
    save_to = out_path or CHART_FILE
    plt.savefig(save_to, dpi=130, bbox_inches="tight")
    plt.close()


# Вспомогательные функции

def is_valid_mac(mac: str) -> bool:
    """Проверяет формат MAC-адреса."""
    return bool(re.match(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$", mac))


VENDOR_TABLE = {
    "A4:C3:F0": "Apple Inc.",
    "B8:27:EB": "Raspberry Pi Foundation",
    "D8:BB:C1": "ASUSTek Computer",
    "FC:FB:FB": "Cisco Systems",
    "AA:BB:CC": "TP-Link Technologies",
    "44:55:66": "D-Link Corporation",
}


def get_vendor(mac: str) -> str:
    """Возвращает производителя по OUI-части MAC-адреса.."""
    return VENDOR_TABLE.get(mac[:8].upper(), "Неизвестный производитель")


def run_full_analysis():
    """
    Запускает полный анализ:
    загружает 1.json → анализирует → сохраняет 2.json → строит report.png.
    Возвращает (df, fails, blocked, stats).
    """
    attempts = load_attempts()
    df, fails, blocked = analyze(attempts)
    if not df.empty:
        save_failed_attempts(df)
        plot_summary(df, fails, blocked)
    stats = get_summary_stats(df, fails, blocked)
    return df, fails, blocked, stats
