# Deploy en Contabo

Guia para pasar SolarBot SEACE a un VPS Ubuntu de Contabo y probar Telegram con credenciales reales.

Referencias oficiales usadas para estos comandos:

- Docker Engine para Ubuntu: https://docs.docker.com/engine/install/ubuntu/
- Docker post-install en Linux: https://docs.docker.com/engine/install/linux-postinstall/
- Docker Compose plugin: https://docs.docker.com/compose/install/linux/
- Docker Compose secrets: https://docs.docker.com/compose/how-tos/use-secrets/

## 1. Supuestos

- VPS Contabo con Ubuntu 22.04 o 24.04.
- Acceso SSH al servidor.
- Repo ya subido a GitHub con los ultimos cambios.
- Token de Telegram creado con `@BotFather`.
- El bot debe correr permanente con Docker Compose, PostgreSQL y backups.

## 2. Instalar Docker en el VPS

Entra por SSH:

```bash
ssh usuario@IP_DEL_SERVIDOR
```

Instala Docker Engine y el plugin de Compose desde el repositorio oficial:

```bash
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl status docker
sudo docker run hello-world
docker compose version
```

Opcional: permitir usar `docker` sin `sudo`.

```bash
sudo groupadd docker || true
sudo usermod -aG docker "$USER"
newgrp docker
docker run hello-world
```

## 3. Subir el codigo

Usa la rama que tenga estos cambios productivos:

```bash
mkdir -p ~/apps
cd ~/apps
git clone https://github.com/4zzuf/ElectropolarBotB.git
cd ElectropolarBotB
git checkout modificaciones
```

Si el deploy se hace desde otra rama, reemplaza `modificaciones` por la rama real.

## 4. Crear configuracion productiva

```bash
cp .env.production.example .env.production
openssl rand -hex 24
nano .env.production
```

Cambia como minimo:

```env
APP_ENV_FILE=.env.production
POSTGRES_PASSWORD=UNA_CLAVE_LARGA_Y_UNICA
SEACE_SEARCH_KEYWORDS=solar,panel solar,luminaria solar
SEACE_DEPARTMENTS=
SCAN_INTERVAL_HOURS=3
SEACE_MAX_PAGES=0
TELEGRAM_ENABLED=true
```

Notas:

- `SEACE_DEPARTMENTS` vacio busca en todo Peru.
- `SEACE_MAX_PAGES=0` recorre todas las paginas disponibles.
- `POSTGRES_PASSWORD` no debe quedar como `solarbot` ni como placeholder. Usa el valor generado con `openssl rand -hex 24` para evitar caracteres problematicos dentro del `DATABASE_URL`.

## 5. Crear secretos de Telegram

Los secretos no van en Git ni en `.env.production`; Docker Compose los monta como archivos en `/run/secrets/...`.

```bash
mkdir -p secrets
printf '%s' 'TOKEN_REAL_DEL_BOT' > secrets/telegram_bot_token.txt
printf '%s' '' > secrets/telegram_chat_id.txt
chmod 600 secrets/*.txt
```

Para obtener el chat id:

1. Escribele un mensaje al bot desde tu Telegram.
2. Corre:

```bash
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml run --rm app python -m app.main --mode telegram-chat-id
```

3. Copia el `chat_id` mostrado y guardalo:

```bash
printf '%s' 'CHAT_ID_REAL' > secrets/telegram_chat_id.txt
chmod 600 secrets/telegram_chat_id.txt
```

## 6. Preflight antes de levantar produccion

Este chequeo revisa archivos, `.gitignore`, YAML, `.env.production`, secrets y Docker:

```bash
python3 scripts/preflight.py --production --env-file .env.production --require-docker
```

El resultado esperado al final es:

```text
Preflight: OK
```

Si falla por Python o dependencias del host, puedes validar Compose directamente:

```bash
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml config
```

## 7. Probar Telegram real

Primero valida token y envio de mensaje:

```bash
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml run --rm app python -m app.main --mode test-telegram
```

Luego haz una corrida controlada contra SEACE:

```bash
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml run --rm -e SEACE_MAX_PAGES=1 app python -m app.main --mode once --keywords "solar" --departments "TACNA"
```

Revisa lo encontrado:

```bash
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml run --rm app python -m app.main --mode list --limit 20
```

## 8. Levantar el bot permanente

Con bot, PostgreSQL y backups diarios:

```bash
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml --profile backup up -d --build
```

Ver logs:

```bash
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml logs -f app
```

Ver estado:

```bash
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml ps
```

Healthcheck manual:

```bash
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml exec app python -m app.health
```

## 9. Dashboard opcional

Levanta Streamlit solo si lo vas a usar:

```bash
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml --profile dashboard up -d --build dashboard
```

El dashboard expone el puerto `8501`. Para produccion comercial, lo mas prudente es no abrirlo publicamente; usa firewall, VPN, proxy con auth o tunel SSH:

```bash
ssh -L 8501:localhost:8501 usuario@IP_DEL_SERVIDOR
```

Luego abre `http://localhost:8501` en tu maquina.

## 10. Backups y restore

Los backups quedan en `backups/` y se retienen por defecto 14 dias.

Listar backups:

```bash
ls -lh backups
```

Restaurar un backup manualmente:

```bash
cat backups/NOMBRE_DEL_BACKUP.sql.gz | gunzip | docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml exec -T postgres psql -U solarbot -d solarbot
```

## 11. Actualizar version en el VPS

```bash
cd ~/apps/ElectropolarBotB
git pull
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml --profile backup up -d --build
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml logs -f app
```

## 12. Checklist final

- `git status` limpio antes de subir cambios a GitHub.
- `.env.production` existe en el VPS y no esta en Git.
- `secrets/telegram_bot_token.txt` tiene token real.
- `secrets/telegram_chat_id.txt` tiene chat id real.
- `POSTGRES_PASSWORD` fue cambiado.
- `python3 scripts/preflight.py --production --env-file .env.production --require-docker` termina en OK.
- `--mode test-telegram` envia mensaje.
- `--mode once` encuentra y guarda resultados.
- `--profile backup` esta levantado.
- Puerto `5432` no esta publicado.
- Puerto `8501` solo se abre si el dashboard esta protegido.
