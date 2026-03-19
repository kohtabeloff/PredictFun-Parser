"""
Фильтрация маркетов по наличию на Polymarket или Kalshi.

Логика для каждого маркета:
  1. Проверяем polymarketConditionIds в данных Predict.fun — если непусто,
     значит рынок напрямую связан с Polymarket → оставляем сразу (без запросов).
  2. Если Polymarket-ссылки нет — делаем текстовый поиск на Kalshi.
     Ищем по ключевым словам из заголовка маркета.
  3. Если ничего не нашли → убираем.

При любой ошибке запроса к Kalshi — маркет оставляем (не теряем лишнего).
"""
from __future__ import annotations

import re
import time
from datetime import date as date_type
from typing import Any

import requests

# Кэш дат с Polymarket: conditionId → date или None
_poly_date_cache: dict[str, date_type | None] = {}

KALSHI_BASE = "https://api.elections.kalshi.com/trade-api/v2"

# Слова, которые не несут смысла при поиске
_STOP_WORDS = {
    "will", "the", "a", "an", "in", "on", "by", "to", "of", "for",
    "is", "be", "or", "and", "at", "this", "that", "with", "from",
    "it", "its", "are", "was", "were", "has", "have", "had", "not",
    "any", "all", "more", "than", "before", "after", "when", "if",
    "can", "could", "would", "should", "may", "get", "out", "over",
    "new", "year", "month", "day", "end", "first", "last", "ever",
    "who", "what", "which", "how", "their", "they", "them", "his",
    "her", "our", "your", "win", "lose", "make", "take", "come",
}


def _is_on_polymarket(market_data: dict[str, Any]) -> bool:
    """True если маркет напрямую связан с Polymarket (поле уже есть в данных Predict.fun)."""
    ids = market_data.get("polymarketConditionIds")
    return bool(ids)


def _check_polymarket_date(condition_ids: list[str], min_days: int, today: date_type) -> bool:
    """
    True если до окончания маркета на Polymarket осталось >= min_days дней.
    При ошибке или отсутствии даты — True (не фильтруем).
    """
    from api_client import fetch_polymarket_end_date  # импорт здесь, чтобы избежать кольца

    for cid in condition_ids:
        if cid in _poly_date_cache:
            end = _poly_date_cache[cid]
        else:
            end = fetch_polymarket_end_date(cid)
            _poly_date_cache[cid] = end

        if end is not None:
            return (end - today).days >= min_days

    return True  # дата не найдена — не фильтруем


def _extract_keywords(title: str) -> list[str]:
    """Извлекает значимые слова из заголовка."""
    words = re.findall(r"\b[a-zA-Z]{3,}\b", title)
    return [w.lower() for w in words if w.lower() not in _STOP_WORDS]


def _is_on_kalshi(title: str, min_keyword_matches: int = 2) -> bool:
    """
    Возвращает True если на Kalshi найдено похожее событие по заголовку.
    При ошибке запроса — True (не фильтруем).
    """
    keywords = _extract_keywords(title)
    if len(keywords) < 2:
        return True  # слишком мало слов — не фильтруем

    query = " ".join(keywords[:4])
    try:
        resp = requests.get(
            f"{KALSHI_BASE}/events",
            params={"title": query, "status": "open", "limit": 10},
            timeout=15,
        )
        if resp.status_code != 200:
            return True  # ошибка API — не фильтруем
        events: list[dict[str, Any]] = resp.json().get("events") or []
        if not events:
            return False

        kw_set = set(keywords)
        for event in events:
            ev_title = (event.get("title") or event.get("sub_title") or "").lower()
            ev_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", ev_title))
            if len(kw_set & ev_words) >= min_keyword_matches:
                return True
        return False
    except Exception:
        return True  # сеть/таймаут — не фильтруем


def filter_by_cross_platform(
    market_ids: list[int],
    market_data: dict[int, dict[str, Any]],
    min_keyword_matches: int = 2,
    delay: float = 0.2,
    min_days: int | None = None,
    today: date_type | None = None,
) -> tuple[list[int], int]:
    """
    Оставляет только маркеты, которые есть на Polymarket или Kalshi.
    Если min_days задан — дополнительно проверяет срок до окончания через Polymarket API.

    Порядок проверки:
      1. polymarketConditionIds непусто → маркет на Polymarket
         - если min_days задан → проверяем дату окончания
         → оставляем если дата ок (или неизвестна)
      2. Иначе → текстовый поиск на Kalshi (дату не проверяем)
      3. Не нашли нигде → убираем

    market_data: {market_id: полный объект маркета из Predict.fun API}
    Возвращает (отфильтрованный список, сколько убрали).
    """
    result: list[int] = []
    kalshi_checked = 0
    _today = today or date_type.today()

    for i, mid in enumerate(market_ids):
        mdata = market_data.get(mid) or {}

        # Быстрая проверка: есть ли прямая ссылка на Polymarket
        if _is_on_polymarket(mdata):
            # Если задан фильтр по дате — проверяем через Polymarket API
            if min_days and min_days > 0:
                condition_ids = mdata.get("polymarketConditionIds") or []
                if not _check_polymarket_date(condition_ids, min_days, _today):
                    continue  # слишком мало дней — убираем
            result.append(mid)
            continue

        # Иначе — ищем на Kalshi по заголовку
        # question предпочтительнее title — он всегда полный
        title = mdata.get("question") or mdata.get("title") or ""
        if not title:
            result.append(mid)  # нет заголовка — не фильтруем
            continue

        if kalshi_checked > 0:
            time.sleep(delay)
        kalshi_checked += 1

        if _is_on_kalshi(title, min_keyword_matches):
            result.append(mid)

    return result, len(market_ids) - len(result)
