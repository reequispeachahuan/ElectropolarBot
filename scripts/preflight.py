from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - useful on a fresh VPS host
    yaml = None


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = (
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.prod.yml",
    ".env.production.example",
    "scripts/backup_postgres.sh",
    "app/main.py",
    "app/health.py",
)

PRODUCTION_SECRET_FILES = (
    "secrets/telegram_bot_token.txt",
    "secrets/telegram_chat_id.txt",
)


@dataclass(frozen=True)
class Check:
    level: str
    message: str


class Reporter:
    def __init__(self) -> None:
        self.checks: list[Check] = []

    def ok(self, message: str) -> None:
        self.checks.append(Check("OK", message))

    def warn(self, message: str) -> None:
        self.checks.append(Check("WARN", message))

    def fail(self, message: str) -> None:
        self.checks.append(Check("FAIL", message))

    def print(self) -> None:
        for check in self.checks:
            print(f"[{check.level}] {check.message}")

    @property
    def failed(self) -> bool:
        return any(check.level == "FAIL" for check in self.checks)


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def is_placeholder(value: str | None) -> bool:
    if not value:
        return True
    normalized = value.strip().lower()
    return (
        normalized in {"solarbot", "password", "changeme", "change_me", "secret"}
        or normalized.startswith("cambiar")
        or normalized.startswith("replace")
    )


def check_required_files(reporter: Reporter) -> None:
    for relative_path in REQUIRED_PATHS:
        path = ROOT / relative_path
        if path.exists():
            reporter.ok(f"Existe {relative_path}")
        else:
            reporter.fail(f"Falta {relative_path}")


def check_gitignore(reporter: Reporter) -> None:
    gitignore = ROOT / ".gitignore"
    if not gitignore.exists():
        reporter.fail("Falta .gitignore")
        return

    patterns = set(gitignore.read_text(encoding="utf-8").splitlines())
    for pattern in (".env", ".env.production", "secrets/*.txt", "backups/"):
        if pattern in patterns:
            reporter.ok(f".gitignore protege {pattern}")
        else:
            reporter.fail(f".gitignore debe incluir {pattern}")


def check_yaml_files(reporter: Reporter) -> None:
    if yaml is None:
        reporter.warn("PyYAML no esta instalado; se omite validacion YAML de Compose")
        return

    for relative_path in ("docker-compose.yml", "docker-compose.prod.yml"):
        path = ROOT / relative_path
        try:
            with path.open(encoding="utf-8") as handle:
                yaml.safe_load(handle)
        except Exception as exc:
            reporter.fail(f"{relative_path} no se pudo parsear como YAML: {exc}")
        else:
            reporter.ok(f"{relative_path} parsea como YAML")


def check_env(reporter: Reporter, env_file: Path, production: bool) -> dict[str, str]:
    if not env_file.exists():
        if production:
            reporter.fail(f"Falta {env_file.name}; crea una copia desde .env.production.example")
        else:
            reporter.warn(f"No existe {env_file.name}; el desarrollo local puede requerirlo")
        return {}

    reporter.ok(f"Existe {env_file.name}")
    env = parse_env_file(env_file)

    if production:
        if env.get("APP_ENV_FILE") == env_file.name:
            reporter.ok("APP_ENV_FILE apunta al archivo productivo")
        else:
            reporter.warn(f"APP_ENV_FILE deberia ser {env_file.name} para deploy productivo")

        if is_placeholder(env.get("POSTGRES_PASSWORD")):
            reporter.fail("POSTGRES_PASSWORD debe cambiarse por una clave larga antes de produccion")
        elif len(env["POSTGRES_PASSWORD"]) < 16:
            reporter.warn("POSTGRES_PASSWORD funciona, pero conviene que tenga 16+ caracteres")
        elif any(char in env["POSTGRES_PASSWORD"] for char in ":/@?#[]%"):
            reporter.warn("POSTGRES_PASSWORD contiene caracteres que pueden requerir URL encoding")
        else:
            reporter.ok("POSTGRES_PASSWORD no parece placeholder")

        if env.get("TELEGRAM_BOT_TOKEN"):
            reporter.fail("No pongas TELEGRAM_BOT_TOKEN directo en .env.production; usa secrets/*.txt")
        else:
            reporter.ok("Telegram token no esta inline en .env.production")

        for key in ("TELEGRAM_BOT_TOKEN_FILE", "TELEGRAM_CHAT_ID_FILE"):
            if env.get(key, "").startswith("/run/secrets/"):
                reporter.ok(f"{key} usa Docker secrets")
            else:
                reporter.fail(f"{key} debe apuntar a /run/secrets/...")

        if env.get("TELEGRAM_ENABLED", "").lower() == "true":
            reporter.ok("TELEGRAM_ENABLED=true")
        else:
            reporter.fail("TELEGRAM_ENABLED debe estar en true para produccion con alertas")

    else:
        telegram_enabled = env.get("TELEGRAM_ENABLED", "").lower() == "true"
        has_token = bool(env.get("TELEGRAM_BOT_TOKEN") or env.get("TELEGRAM_BOT_TOKEN_FILE"))
        has_chat = bool(env.get("TELEGRAM_CHAT_ID") or env.get("TELEGRAM_CHAT_ID_FILE"))
        if telegram_enabled and not (has_token and has_chat):
            reporter.warn("Telegram esta activo pero faltan token/chat id")
        else:
            reporter.ok("Configuracion local de Telegram no bloquea pruebas")

    for key in ("SCAN_INTERVAL_HOURS", "SEACE_MAX_PAGES"):
        if key not in env:
            continue
        try:
            value = int(env[key])
        except ValueError:
            reporter.fail(f"{key} debe ser entero")
            continue
        minimum = 1 if key == "SCAN_INTERVAL_HOURS" else 0
        if value < minimum:
            reporter.fail(f"{key} debe ser >= {minimum}")
        else:
            reporter.ok(f"{key} tiene valor valido")

    return env


def check_production_secrets(reporter: Reporter, production: bool) -> None:
    for relative_path in PRODUCTION_SECRET_FILES:
        path = ROOT / relative_path
        if not path.exists():
            if production:
                reporter.fail(f"Falta secreto {relative_path}")
            else:
                reporter.warn(f"No existe {relative_path}; normal si aun no pruebas Telegram real")
            continue
        value = path.read_text(encoding="utf-8").strip()
        if value:
            reporter.ok(f"Secreto {relative_path} existe y no esta vacio")
        elif production:
            reporter.fail(f"Secreto {relative_path} existe pero esta vacio")
        else:
            reporter.warn(f"Secreto {relative_path} esta vacio")


def check_docker(reporter: Reporter, require_docker: bool, env_file: Path, production: bool) -> None:
    docker = shutil.which("docker")
    if not docker:
        message = "Docker no esta instalado o no esta en PATH"
        if require_docker:
            reporter.fail(message)
        else:
            reporter.warn(message)
        return

    reporter.ok("Docker esta disponible en PATH")
    version = subprocess.run(
        [docker, "compose", "version"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if version.returncode == 0:
        reporter.ok(version.stdout.strip())
    elif require_docker:
        reporter.fail("Docker Compose plugin no respondio correctamente")
    else:
        reporter.warn("Docker Compose plugin no respondio correctamente")

    compose_command = [docker, "compose"]
    if env_file.exists():
        compose_command.extend(["--env-file", str(env_file)])
    compose_command.extend(["-f", "docker-compose.yml"])
    if production:
        compose_command.extend(["-f", "docker-compose.prod.yml"])
    compose_command.append("config")

    config = subprocess.run(
        compose_command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if config.returncode == 0:
        reporter.ok("docker compose config valido")
    elif require_docker:
        reporter.fail(f"docker compose config fallo: {config.stderr.strip()}")
    else:
        reporter.warn(f"docker compose config fallo: {config.stderr.strip()}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Chequeos previos al deploy de SolarBot SEACE")
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Archivo de variables a validar. En Contabo usa .env.production",
    )
    parser.add_argument(
        "--production",
        action="store_true",
        help="Exige secretos y configuracion productiva",
    )
    parser.add_argument(
        "--require-docker",
        action="store_true",
        help="Falla si Docker o docker compose no estan disponibles",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    reporter = Reporter()
    env_file = ROOT / args.env_file

    check_required_files(reporter)
    check_gitignore(reporter)
    check_yaml_files(reporter)
    check_env(reporter, env_file, production=args.production)
    check_production_secrets(reporter, production=args.production)
    check_docker(
        reporter,
        require_docker=args.require_docker,
        env_file=env_file,
        production=args.production,
    )

    reporter.print()
    if reporter.failed:
        print("\nPreflight: FAIL")
        return 1
    print("\nPreflight: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
