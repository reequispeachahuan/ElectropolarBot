# SolarBot SEACE

SolarBot SEACE detecta, clasifica, guarda, alerta y ayuda a gestionar oportunidades públicas del SEACE relacionadas con energía solar: luminarias solares, paneles, baterías, sistemas fotovoltaicos, alumbrado público, electrificación rural, mantenimiento eléctrico y rubros similares.

> El bot está diseñado para consultar información pública. No evade captchas, no rompe mecanismos de seguridad y no automatiza acciones que requieran certificado SEACE o validación humana.

## Capacidades incluidas

- Diccionario configurable de palabras clave solares.
- Clasificador por reglas con descarte de falsos positivos.
- Scoring comercial para recomendar acciones.
- Modelos SQLAlchemy para PostgreSQL.
- Scraper base con Playwright/BeautifulSoup para fuentes públicas del SEACE.
- Alertas Telegram y plantillas de mensajes.
- Dashboard Streamlit tipo CRM.
- Asistente de postulación: carpetas, checklist y resumen ejecutivo.
- Scheduler para ejecución diaria y revisiones periódicas.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Para usar Playwright:

```bash
playwright install chromium
```

## Configuración

Edita `.env`:

```env
DATABASE_URL=postgresql+psycopg://solarbot:solarbot@localhost:5432/solarbot
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
SEACE_HEADLESS=true
ATTENDABLE_REGIONS=Lima,Arequipa,Cusco,Puno,Junin
ATTRACTIVE_AMOUNT=50000
```

## Ejecutar

```bash
python -m app.main --mode once
python -m app.main --mode scheduler
streamlit run app/dashboard/streamlit_app.py
```

## Tests

```bash
pytest
```

## Fases recomendadas

1. Base del proyecto y PostgreSQL.
2. Captura SEACE por fuente pública.
3. Clasificación solar.
4. Scoring comercial.
5. Alertas Telegram.
6. Dashboard.
7. Documentos y postulación asistida.
