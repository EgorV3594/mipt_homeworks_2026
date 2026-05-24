import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]


CONFIG_PATH = Path(__file__).resolve().parent.parent / 'config.yaml'


@dataclass(frozen=True)
class AppConfig:
    api_key: str
    api_host: str
    model: str
    limit_message: int | None = None
    limit_chars: int | None = None
    temperature: float | None = None
    system_prompt: str | None = None


def load_config(config_path: Path = CONFIG_PATH) -> AppConfig:
    yaml_config = _load_yaml_config(config_path)

    api_key = _get_setting('API_KEY', 'api_key', yaml_config)
    api_host = _get_setting('API_HOST', 'api_host', yaml_config)
    model = _get_setting('MODEL', 'model', yaml_config)

    if not api_key or not api_host or not model:
        raise ValueError(
            'Не найдены обязательные настройки: API_KEY/API_HOST/MODEL '
            'или api_key/api_host/model в config.yaml.'
        )

    return AppConfig(
        api_key=api_key,
        api_host=api_host,
        model=model,
        limit_message=_get_optional_int_setting('LIMIT_MESSAGE', 'limit_message', yaml_config),
        limit_chars=_get_optional_int_setting('LIMIT_CHARS', 'limit_chars', yaml_config),
        temperature=_get_optional_float_setting('TEMPERATURE', 'temperature', yaml_config),
        system_prompt=_get_optional_str_setting('system_prompt', yaml_config),
    )


def _load_yaml_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        return {}

    with config_path.open(encoding='utf-8') as config_file:
        config = yaml.safe_load(config_file) or {}

    if not isinstance(config, dict):
        raise ValueError('config.yaml должен содержать словарь настроек.')
    return config


def _get_setting(env_name: str, yaml_name: str, yaml_config: dict[str, Any]) -> str:
    env_value = os.environ.get(env_name)

    if env_value:
        return env_value

    yaml_value = yaml_config.get(yaml_name)
    if yaml_value is None:
        return ''
    return str(yaml_value)


def _get_optional_str_setting(yaml_name: str, yaml_config: dict[str, Any]) -> str | None:
    yaml_value = yaml_config.get(yaml_name)
    if yaml_value is None:
        return None
    return str(yaml_value)


def _get_optional_int_setting(
    env_name: str,
    yaml_name: str,
    yaml_config: dict[str, Any],
) -> int | None:
    value = _get_setting(env_name, yaml_name, yaml_config)
    if not value:
        return None
    return int(value)


def _get_optional_float_setting(
    env_name: str,
    yaml_name: str,
    yaml_config: dict[str, Any],
) -> float | None:
    value = _get_setting(env_name, yaml_name, yaml_config)
    if not value:
        return None
    return float(value)
