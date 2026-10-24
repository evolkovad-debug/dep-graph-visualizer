"""Получение прямых зависимостей пакета из репозитория (JSON API PyPI)."""

import json
import re
import urllib.error
import urllib.request

REQUEST_TIMEOUT = 10
HTTP_NOT_FOUND = 404
NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*")
EXTRA_PATTERN = re.compile(r"\bextra\s*==")


class RepoError(Exception):
    """Ошибка при обращении к репозиторию или разборе его ответа."""


def build_url(repo, package):
    """Собрать адрес JSON-описания пакета."""
    return f"{repo.rstrip('/')}/{package}/json"


def fetch_json(url):
    """Скачать и разобрать JSON по адресу url."""
    try:
        with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT) as reply:
            return json.load(reply)
    except urllib.error.HTTPError as error:
        if error.code == HTTP_NOT_FOUND:
            raise RepoError(f"пакет не найден в репозитории: {url}") from error
        raise RepoError(f"сервер ответил ошибкой {error.code}") from error
    except urllib.error.URLError as error:
        raise RepoError(f"не удалось подключиться: {error.reason}") from error
    except OSError as error:
        raise RepoError(f"ошибка сети: {error}") from error
    except ValueError as error:
        raise RepoError("ответ сервера не является JSON") from error


def parse_requirement(requirement):
    """Вернуть имя пакета из строки зависимости или None для extra."""
    spec, _, marker = requirement.partition(";")
    if EXTRA_PATTERN.search(marker):
        return None
    match = NAME_PATTERN.match(spec.strip())
    return match.group(0) if match else None


def extract_dependencies(data):
    """Получить список прямых зависимостей из JSON-описания пакета."""
    if not isinstance(data, dict):
        raise RepoError("неожиданный формат ответа репозитория")
    info = data.get("info") or {}
    requirements = info.get("requires_dist") or []
    names = []
    for requirement in requirements:
        name = parse_requirement(requirement)
        if name is not None and name not in names:
            names.append(name)
    return names


def get_dependencies(repo, package):
    """Получить прямые зависимости пакета package из репозитория repo."""
    return extract_dependencies(fetch_json(build_url(repo, package)))
