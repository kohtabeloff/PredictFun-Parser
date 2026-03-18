import json
import os
import sys
from pathlib import Path

from pipeline_runner import run_pipeline

BASE_URL = "https://api.predict.fun"
SETTINGS_FILE = Path(__file__).parent / ".settings.json"


def _load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text("utf-8"))
        except Exception:
            pass
    return {}


def cli_main() -> None:
    settings = _load_settings()

    # API-ключ: из переменной окружения или settings.json
    api_key = os.environ.get("PREDICT_FUN_API_KEY") or settings.get("api_key") or ""
    if not api_key:
        print("Ошибка: API-ключ не найден.")
        print("Добавьте в .settings.json поле api_key или задайте PREDICT_FUN_API_KEY.")
        return

    # Флаги из аргументов командной строки
    use_all    = "--all"    in sys.argv  # загрузить все маркеты с Predict.fun
    use_kalshi = "--kalshi" in sys.argv  # включить фильтр Polymarket/Kalshi

    # Параметры из settings.json
    market_file   = settings.get("market_ids_file") or "last_market_ids.txt"
    exclude_ids   = settings.get("exclude_tag_ids") or []
    exclude_names = settings.get("exclude_tag_names") or exclude_ids
    min_days      = settings.get("min_days_until_end")
    require_status= settings.get("require_status") or None
    output_file   = settings.get("output_file") or "result.txt"

    print("=" * 50)
    print("Predict.fun — фильтр маркетов (CLI)")
    print("=" * 50)
    if use_all:
        print("Источник: все маркеты с Predict.fun")
    else:
        print(f"Источник: файл {market_file}")
    if exclude_ids:
        print(f"Исключить теги: {', '.join(map(str, exclude_ids))}")
    if require_status:
        print(f"Статус: {require_status}")
    if min_days:
        print(f"Мин. дней до конца: {min_days}")
    if use_kalshi:
        print("Фильтр: Polymarket / Kalshi — включён")
    print("-" * 50)

    def on_step(idx: int, status: str, detail: str):
        if status == "running":
            pass  # не спамим "запускаем..."
        elif status == "done":
            print(f"  ✓ Шаг {idx}: {detail}")
        elif status == "skip":
            print(f"  — Шаг {idx}: пропущен ({detail})")
        elif status == "error":
            print(f"  ✗ Шаг {idx}: ошибка — {detail}")

    result, err = run_pipeline(
        api_key=api_key,
        base_url=BASE_URL,
        market_ids_file=None if use_all else market_file,
        use_all_markets=use_all,
        exclude_tag_ids=exclude_ids,
        exclude_tag_names=exclude_names,
        min_days_until_end=min_days,
        require_status=require_status,
        use_kalshi_filter=use_kalshi,
        output_file=output_file,
        date_field_order=None,
        step_callback=on_step,
    )

    print("-" * 50)
    if err:
        print(f"Ошибка: {err}")
    else:
        print(f"Готово. Осталось маркетов: {len(result)}")
        print(f"Сохранено в: {output_file}")


if __name__ == "__main__":
    if "--cli" in sys.argv:
        cli_main()
    else:
        try:
            from gui_main import main as gui_main
            gui_main()
        except Exception as e:
            print("Не удалось запустить окно:", e)
            print("Установите PySide6: pip install PySide6")
            print("Консольный режим: python3 main.py --cli")
