# SolarBot SEACE

SolarBot SEACE detecta, clasifica, guarda, alerta y ayuda a gestionar oportunidades públicas del SEACE relacionadas con energía solar.

> El bot consulta solo fuentes públicas. No evade captchas y no automatiza acciones privadas con certificado SEACE.

## 1) ¿Cómo funciona la alerta de Telegram?

La alerta usa `python-telegram-bot` en `app/notifications/telegram_bot.py`.

Flujo:
1. Se procesan oportunidades en `app/main.py` (`run_once`).
2. El clasificador marca prioridad (`alta`, `media`, `baja`, `descartada`).
3. Si ejecutas con `--send-telegram`:
   - Envía alerta inmediata por cada oportunidad **alta**.
   - Envía resumen diario con todas las oportunidades procesadas.
4. Los mensajes incluyen botones: ver en SEACE, revisar, postular, descartar, asignar técnico.

Variables necesarias en `.env`:

```env
TELEGRAM_BOT_TOKEN=xxxxxxxxxx:yyyyyyyyyyyyyyyyyyyy
TELEGRAM_CHAT_ID=123456789
```

Cómo probar solo Telegram:

```bash
python -m app.main --mode telegram-test
```

Si llega el mensaje “✅ SolarBot SEACE conectado…”, quedó configurado correctamente.

---

## 2) ¿Cómo lo ejecuto?

### Requisitos

- Python 3.11+
- pip
- (Opcional para scraper real) Playwright Chromium

### Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
```

### Ejecutar una corrida única

```bash
python -m app.main --mode once
```

### Ejecutar corrida única + alertas Telegram

```bash
python -m app.main --mode once --send-telegram
```

### Ejecutar scheduler

```bash
python -m app.main --mode scheduler
```

Scheduler configurado:
- Diario: 06:00 (America/Lima)
- Periódico: cada 3 horas

### Dashboard Streamlit

```bash
streamlit run app/dashboard/streamlit_app.py
```

El dashboard ya no depende de subir CSV manualmente.
- Carga automáticamente `data/processed/latest_opportunities.csv` si existe.
- Incluye botón **"Ejecutar búsqueda SEACE ahora"** para disparar la captura y procesamiento desde la interfaz.

### Tests

```bash
pytest -q
```

## Estructura principal

- `app/seace/`: captura y parser de fuentes SEACE.
- `app/classifier/`: matcher + clasificador de oportunidad.
- `app/scoring/`: puntaje y recomendación comercial.
- `app/notifications/`: plantillas y envío Telegram.
- `app/dashboard/`: panel Streamlit.
- `app/bids/`: asistente de carpeta, checklist y resumen.
- `app/database/`: modelos SQLAlchemy.


## Persistencia de resultados

Cada ejecución de `--mode once` guarda automáticamente resultados en:
- `data/processed/opportunities_YYYYMMDD_HHMMSS.csv`
- `data/processed/latest_opportunities.csv`

El dashboard carga `latest_opportunities.csv` automáticamente si existe (sin necesidad de subir CSV manualmente).

## URL del buscador público

El scraper usa la URL pública:
`https://prod2.seace.gob.pe/seacebus-uiwd-pub/buscadorPublico/buscadorPublico.xhtml`
