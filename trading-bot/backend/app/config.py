import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_env: str = "local"
    database_path: str = "./tenk_to_million.db"
    data_source: str = "jquants"
    initial_cash: int = 10_000
    jquants_api_key: str = ""
    jquants_email: str = ""
    jquants_password: str = ""
    yahoo_finance_enabled: bool = False
    openai_api_key: str = ""
    openai_analyst_model: str = "gpt-4.1-mini"
    scheduler_enabled: bool = False
    cors_origins: tuple[str, ...] = ("http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174")
    market_symbols: tuple[str, ...] = (
        "3778",
        "2160",
        "4565",
        "6920",
        "5253",
        "7014",
        "1514",
        "5586",
        "5595",
        "6526",
    )


@lru_cache
def get_settings() -> Settings:
    env = _read_env_file(Path(".env"))
    return Settings(
        app_env=_value("APP_ENV", env, "local"),
        database_path=_value("DATABASE_PATH", env, "./tenk_to_million.db"),
        data_source=_value("DATA_SOURCE", env, "jquants"),
        initial_cash=int(_value("INITIAL_CASH", env, "10000")),
        jquants_api_key=_value("JQUANTS_API_KEY", env, ""),
        jquants_email=_value("JQUANTS_EMAIL", env, ""),
        jquants_password=_value("JQUANTS_PASSWORD", env, ""),
        yahoo_finance_enabled=_value("YAHOO_FINANCE_ENABLED", env, "false").lower() == "true",
        openai_api_key=_value("OPENAI_API_KEY", env, ""),
        openai_analyst_model=_value("OPENAI_ANALYST_MODEL", env, "gpt-4.1-mini"),
        scheduler_enabled=_value("SCHEDULER_ENABLED", env, "false").lower() == "true",
        cors_origins=tuple(
            origin.strip()
            for origin in _value(
                "CORS_ORIGINS",
                env,
                "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174",
            ).split(",")
            if origin.strip()
        ),
        market_symbols=tuple(
            symbol.strip()
            for symbol in _value("MARKET_SYMBOLS", env, "3778,2160,4565,6920,5253,7014,1514,5586,5595,6526").split(",")
            if symbol.strip()
        ),
    )


def _value(key: str, env: dict[str, str], default: str) -> str:
    return os.environ.get(key) or env.get(key) or default


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values
