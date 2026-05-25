# SolarBot SEACE

SolarBot SEACE detecta, clasifica, guarda, alerta y ayuda a gestionar oportunidades publicas del SEACE relacionadas con energia solar: luminarias solares, paneles, baterias, sistemas fotovoltaicos, alumbrado publico, electrificacion rural, mantenimiento electrico y rubros similares.

El bot esta disenado para consultar informacion publica. No evade captchas, no rompe mecanismos de seguridad y no automatiza acciones que requieran certificado SEACE o validacion humana.

## Capacidades incluidas

- Diccionario configurable de palabras clave solares.
- Clasificador por reglas con descarte de falsos positivos.
- Scoring comercial para recomendar acciones.
- Modelos SQLAlchemy para PostgreSQL o SQLite local.
- Scraper base con Playwright/BeautifulSoup para fuentes publicas del SEACE.
- Alertas Telegram y registro de alertas enviadas.
- Dashboard Streamlit tipo CRM.
- Asistente de postulacion: carpetas, checklist y resumen ejecutivo.
- Scheduler para ejecucion diaria y revisiones periodicas.

## Desarrollo local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
playwright install chromium
pytest
```

En Windows:

```powershell
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pytest
```

Para probar local sin PostgreSQL, usa SQLite en `.env`:

```env
DATABASE_URL=sqlite:///solarbot.db
```

## Configuracion

Edita `.env`:

```env
DATABASE_URL=sqlite:///solarbot.db
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
TELEGRAM_ENABLED=true
TELEGRAM_ALERT_PRIORITIES=alta
TELEGRAM_SUMMARY_ENABLED=true
TELEGRAM_SUMMARY_PRIORITIES=media,baja
TELEGRAM_SUMMARY_LIMIT=15
TELEGRAM_ERROR_ALERTS=true
SEACE_HEADLESS=true
ATTENDABLE_REGIONS=Lima,Arequipa,Cusco,Puno,Junin
ATTRACTIVE_AMOUNT=50000
DATA_DIR=data
SEACE_SEARCH_KEYWORDS=solar
SEACE_DEPARTMENTS=
SEACE_SOURCE=openegocio
SEACE_OPENEGOCIO_BASE_URL=https://prod4.seace.gob.pe:8086/api/oportunidades
SEACE_OBJECT_CODES=62,63,64,65
SEACE_REQUEST_DELAY_SECONDS=2
SEACE_REQUEST_TIMEOUT_SECONDS=60
SCAN_INTERVAL_HOURS=3
SCAN_JITTER_MINUTES=20
DAILY_SCAN_HOUR=6
DAILY_SCAN_MINUTE=0
DAILY_SUMMARY_HOUR=18
DAILY_SUMMARY_MINUTE=0
SEACE_MAX_PAGES=0
SEACE_CAPTURE_DETAIL_URLS=false
RESULTS_CSV_PATH=data/processed/opportunities.csv
```

`SEACE_DEPARTMENTS` vacio busca en todo el Peru. Para filtrar por regiones/departamentos de SEACE:

```env
SEACE_DEPARTMENTS=TACNA,CUSCO,PUNO
SEACE_SEARCH_KEYWORDS=solar,panel solar,luminaria solar
```

## Comandos utiles

```bash
python -m app.main --mode init-db
python -m app.main --mode test-telegram
python -m app.main --mode telegram-chat-id
python -m app.main --mode once
python -m app.main --mode once --keywords "solar,panel solar" --departments "TACNA,CUSCO"
python -m app.main --mode list --limit 20
python -m app.main --mode list --priority alta --limit 20
python -m app.main --mode list-regions
python -m app.main --mode list-keywords
python -m app.main --mode export-csv
python -m app.main --mode send-summary
python -m app.main --mode scheduler
streamlit run app/dashboard/streamlit_app.py
```

Cada corrida `once` exporta los resultados a `data/processed/opportunities.csv`.

### Alertas, resumen y CRM

- Las oportunidades `alta` se alertan inmediatamente si `TELEGRAM_ENABLED=true`.
- Las prioridades `media,baja` van al resumen diario si `TELEGRAM_SUMMARY_ENABLED=true`.
- Las `descartada` nunca se alertan.
- Los errores de corrida se notifican si `TELEGRAM_ERROR_ALERTS=true`.
- Cada corrida queda registrada en `scan_runs` con estado, filtros, conteos y alertas enviadas/fallidas.

El dashboard permite filtrar, revisar oportunidades, cambiar estados comerciales y ver ultimas corridas.

Estados comerciales:

```text
nueva -> revisar_bases -> cotizar -> preparar_documentos -> postulada -> ganada/perdida/descartada
```

## Produccion con Docker

La guia completa para Contabo esta en `docs/DEPLOY_CONTABO.md`. El `docker-compose.yml` levanta:

- `app`: bot en modo scheduler.
- `postgres`: base de datos persistente.
- `dashboard`: Streamlit opcional con perfil `dashboard`.
- `backup`: backups diarios de PostgreSQL con perfil `backup`.

Preflight local:

```bash
python scripts/preflight.py
```

Produccion con secretos Docker:

```bash
cp .env.production.example .env.production
mkdir -p secrets
printf "TOKEN_AQUI" > secrets/telegram_bot_token.txt
printf "CHAT_ID_AQUI" > secrets/telegram_chat_id.txt
python3 scripts/preflight.py --production --env-file .env.production --require-docker
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml --profile backup up -d --build
```

Con dashboard:

```bash
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml --profile dashboard up -d --build dashboard
```

Logs:

```bash
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml logs -f app
```

Los backups se guardan en `backups/` y se retienen por defecto 14 dias. PostgreSQL no publica el puerto `5432`; el bot accede por la red interna de Docker.

## Telegram

1. Crea un bot con `@BotFather`.
2. Copia el token en `TELEGRAM_BOT_TOKEN`.
3. Escribele un mensaje al bot desde Telegram.
4. Ejecuta `python -m app.main --mode telegram-chat-id` para ver chats recientes.
5. Copia el id deseado en `TELEGRAM_CHAT_ID`.
6. Activa `TELEGRAM_ENABLED=true`.
7. Ejecuta `python -m app.main --mode test-telegram`.

Cuando `TELEGRAM_ENABLED=true`, el modo `once` y el scheduler envian alertas para prioridades incluidas en `TELEGRAM_ALERT_PRIORITIES`. Por defecto:

```env
TELEGRAM_ALERT_PRIORITIES=alta
```

Healthcheck local:

```bash
python -m app.health
```

## Tests

```bash
pytest
```
