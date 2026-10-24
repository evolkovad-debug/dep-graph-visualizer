"""Чтение файла тестового репозитория (пакеты — заглавные буквы)."""

import re

from src import pypi

NAME_PATTERN = re.compile(r"^[A-Z]+$")
SEPARATOR = ":"
COMMENT_PREFIX = "#"


def parse_line(line, number):
    """Разобрать строку вида «A: B C» в пару (пакет, зависимости)."""
    head, separator, tail = line.partition(SEPARATOR)
    if not separator:
        raise pypi.RepoError(f"строка {number}: ожидался формат 'A: B C'")
    package = head.strip()
    dependencies = tail.split()
    for name in [package] + dependencies:
        if not NAME_PATTERN.match(name):
            raise pypi.RepoError(
                f"строка {number}: недопустимое имя пакета {name!r}"
            )
    return package, dependencies


def parse_repo(text):
    """Разобрать текст тестового репозитория в словарь зависимостей."""
    repo = {}
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith(COMMENT_PREFIX):
            continue
        package, dependencies = parse_line(line, number)
        if package in repo:
            raise pypi.RepoError(f"строка {number}: {package} уже описан")
        repo[package] = dependencies
    return repo


def load_repo(path):
    """Прочитать и разобрать файл тестового репозитория."""
    try:
        with open(path, encoding="utf-8") as handle:
            return parse_repo(handle.read())
    except (OSError, UnicodeDecodeError) as error:
        message = f"не удалось прочитать {path!r}: {error}"
        raise pypi.RepoError(message) from error
