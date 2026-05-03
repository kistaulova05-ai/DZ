import json
import os

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .wps_detection import (
    load_attempts, analyze, save_failed_attempts,
    get_summary_stats, get_fails_by_mac, get_timeline_data,
    plot_summary, get_vendor, BLOCK_THRESHOLD, run_full_analysis,
)


# ── Кэш результатов анализа (обновляется при каждом запуске сканирования) ──
_cache = {}


def _get_analysis():
    """Возвращает кэшированный результат анализа ЛР_2 или пересчитывает."""
    if not _cache:
        _refresh_cache()
    return _cache


def _refresh_cache():
    attempts    = load_attempts()
    df, fails, blocked = analyze(attempts)
    stats       = get_summary_stats(df, fails, blocked)
    fails_by_mac = get_fails_by_mac(df, fails, blocked)
    timeline    = get_timeline_data(df)

    # Автоматически сохраняем 2.json при каждом обновлении кэша
    if not df.empty:
        save_failed_attempts(df)

    # Таблица для отображения
    table_rows = []
    if not df.empty:
        display = df[["mac", "ssid", "pin_tried", "timestamp", "Статус", "Блок"]].copy()
        for _, row in display.iterrows():
            table_rows.append({
                "mac":       row["mac"],
                "ssid":      row["ssid"],
                "pin":       row["pin_tried"],
                "timestamp": str(row["timestamp"]),
                "status":    row["Статус"],
                "block":     row["Блок"],
                "vendor":    get_vendor(row["mac"]),
            })

    _cache.clear()
    _cache.update({
        "stats":       stats,
        "fails_by_mac": fails_by_mac,
        "timeline":    timeline,
        "table_rows":  table_rows,
        "df":          df,
        "fails":       fails,
        "blocked":     blocked,
    })



# Страница дашборда

def dashboard(request):
    data = _get_analysis()
    stats = data["stats"]

    context = {
        "stats":        stats,
        "table_rows":   data["table_rows"],
        "block_threshold": BLOCK_THRESHOLD,
    }
    return render(request, "wps_detector/index.html", context)



# API endpoints для Chart.js


def chart_status_pie(request):
    """Данные для круговой диаграммы: Заблокировано vs Активен (из ЛР_2)."""
    data  = _get_analysis()
    stats = data["stats"]
    return JsonResponse({
        "labels": ["Заблокировано", "Активен"],
        "data":   [stats["blocked_count"], stats["active_count"]],
        "colors": ["#e74c3c", "#2ecc71"],
    })


def chart_failed_attempts(request):
    """Данные для гистограммы неудачных попыток по MAC-адресам."""
    data = _get_analysis()
    rows = data["fails_by_mac"]
    return JsonResponse({
        "labels":  [r["mac"] for r in rows],
        "fails":   [r["fails"] for r in rows],
        "total":   [r["total"] for r in rows],
        "vendors": [get_vendor(r["mac"]) for r in rows],
        "statuses":[r["status"] for r in rows],
    })


def chart_timeline(request):
    """Данные для временной шкалы атак (успешные / неудачные по часам)."""
    data     = _get_analysis()
    timeline = data["timeline"]
    datasets = [
        {
            "label":           "Неудачные попытки",
            "data":            timeline["failed"],
            "borderColor":     "#dc3545",
            "backgroundColor": "#dc354533",
            "fill":            True,
            "tension":         0.4,
        },
        {
            "label":           "Успешные подключения",
            "data":            timeline["success"],
            "borderColor":     "#28a745",
            "backgroundColor": "#28a74533",
            "fill":            True,
            "tension":         0.4,
        },
    ]
    return JsonResponse({"labels": timeline["labels"], "datasets": datasets})


def chart_event_types(request):
    """Соотношение типов событий (для доп. графика)."""
    data  = _get_analysis()
    rows  = data["fails_by_mac"]
    blocked_count = sum(1 for r in rows if r["status"] == "Заблокирован")
    active_count  = sum(1 for r in rows if r["status"] == "Активен")
    return JsonResponse({
        "labels": ["Заблокированные MAC", "Активные MAC"],
        "data":   [blocked_count, active_count],
    })



# Запуск сканирования 


@require_POST
def run_scan(request):
    """
    Запускает полный анализ из ЛР_2:
    читает 1.json → analyze() → save_failed_attempts() → plot_summary()
    Обновляет кэш дашборда.
    """
    try:
        df, fails, blocked, stats = run_full_analysis()
        _refresh_cache()
        return JsonResponse({
            "message":       "Анализ ЛР_2 выполнен успешно",
            "total_attempts": stats["total_attempts"],
            "unique_macs":   stats["unique_macs"],
            "blocked_count": stats["blocked_count"],
            "active_count":  stats["active_count"],
            "mean_fails":    round(stats["mean_fails"], 1),
            "max_fails":     stats["max_fails"],
            "blocked_macs":  stats["blocked_macs"],
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def report_image(request):
    """Отдаёт сгенерированный report.png (из ЛР_2, plot_summary)."""
    chart_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "report.png"
    )
    if not os.path.exists(chart_path):
        # Генерируем при первом обращении
        attempts = load_attempts()
        df, fails, blocked = analyze(attempts)
        if not df.empty:
            plot_summary(df, fails, blocked)
    if os.path.exists(chart_path):
        with open(chart_path, "rb") as f:
            return HttpResponse(f.read(), content_type="image/png")
    return HttpResponse("Отчёт не сгенерирован", status=404)
