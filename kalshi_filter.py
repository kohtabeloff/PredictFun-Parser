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
import re
import time
from typing import Any

import requests

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
) -> tuple[list[int], int]:
    """
    Оставляет только маркеты, которые есть на Polymarket или Kalshi.

    Порядок проверки:
      1. polymarketConditionIds непусто → оставляем сразу (нет доп. запросов)
      2. Иначе → текстовый поиск на Kalshi
      3. Не нашли нигде → убираем

    market_data: {market_id: полный объект маркета из Predict.fun API}
    Возвращает (отфильтрованный список, сколько убрали).
    """
    result: list[int] = []
    kalshi_checked = 0

    for i, mid in enumerate(market_ids):
        mdata = market_data.get(mid) or {}

        # Быстрая проверка: есть ли прямая ссылка на Polymarket
        if _is_on_polymarket(mdata):
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
