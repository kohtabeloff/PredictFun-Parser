# PredictFun Parser

Инструмент для выгрузки актуального списка маркетов с [predict.fun](https://predict.fun?ref=1DD58). Результат сохраняется в файл и используется для настройки [PredictFun Liquidity Farming Bot](https://github.com/kohtabeloff/PredictFun_bot_pabloversion).

---

## Установка

Открой терминал на своём компьютере:

**Mac / Linux:**
```bash
cd ~
git clone https://github.com/kohtabeloff/PredictFun-Parser.git
cd PredictFun-Parser
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows** (PowerShell):
```powershell
cd ~
git clone https://github.com/kohtabeloff/PredictFun-Parser.git
cd PredictFun-Parser
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---

## Запуск

**Mac / Linux:**
```bash
python3 main.py
```

**Windows:**
```powershell
python main.py
```

При первом запуске появится окно с запросом API ключа — введи его и нажми **Сохранить**. Ключ сохранится автоматически, при следующих запусках вводить не нужно.

> API ключ получается в Discord predict.fun: зайди в [Discord](https://discord.gg/predictdotfun), создай тикет в канале **#support-ticket** и запроси ключ, указав адрес своего кошелька.

---

## Настройки в интерфейсе

**Источник маркетов**
- *Все маркеты Predict.fun* — загружает полный список с платформы (рекомендуется)
- *Мой список (файл с id)* — берёт ID из локального файла, если ты уже сохранял список раньше

**Исключить маркеты с тегами**
Галочки по категориям — отмечай те, которые хочешь **убрать** из результата. Например, если не хочешь фармить спортивные маркеты — поставь галочку *Sports*. Доступные категории: Sports, Politics, Crypto, Culture, Economy, NBA, Soccer, NFL, NHL, Esports, CS2, LoL, Cricket, Dota 2, Olympics, Finance, Oscars и др.

**Дополнительные фильтры**
- *Статус маркета* — по умолчанию стоит `REGISTERED` (активные маркеты). Обычно менять не нужно.
- *Фильтр Polymarket / Kalshi* — оставляет только маркеты, которые одновременно есть на других крупных платформах (Polymarket, Kalshi). Такие маркеты обычно популярнее и ликвиднее.
- *Мин. дней до конца* — доступно только вместе с фильтром Polymarket/Kalshi. Отсекает маркеты, которые закрываются слишком скоро.

---

## Результат

Нажми кнопку **Извлечь** — парсер загрузит маркеты с учётом всех настроек и сохранит список ID в файл **`result.txt`** в той же папке.

Этот файл используется в [PredictFun Liquidity Farming Bot](https://github.com/kohtabeloff/PredictFun_bot_pabloversion) — скопируй ID из него и вставь в интерфейс бота через **Добавить маркеты**.

> Запускай парсер раз в несколько дней — маркеты на predict.fun постоянно появляются и закрываются.

---

## Вопросы и обновления

Канал автора: [@hubcryptocis](https://t.me/hubcryptocis)
