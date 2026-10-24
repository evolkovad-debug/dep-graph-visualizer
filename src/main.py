"""Визуализатор графа зависимостей: CLI и получение данных."""

import argparse
import os
import re
import sys

from src import pypi

EXIT_OK = 0
EXIT_ERROR = 1
MIN_DEPTH = 0
DEFAULT_DEPTH = 3
DEFAULT_OUTPUT = "graph.svg"
OUTPUT_EXTENSION = ".svg"
REPO_MODE_ONLINE = "online"
REPO_MODE_TEST = "test"
REPO_MODES = (REPO_MODE_ONLINE, REPO_MODE_TEST)
PACKAGE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
URL_PATTERN = re.compile(r"^https?://\S+$")


class ConfigError(Exception):
    """Ошибка: пользователь передал некорректное значение параметра."""


def build_parser():
    """Создать разборщик параметров командной строки."""
    parser = argparse.ArgumentParser(
        description="Визуализатор графа зависимостей Python-пакетов."
    )
    parser.add_argument(
        "--package", required=True, help="имя анализируемого пакета"
    )
    parser.add_argument(
        "--repo", required=True,
        help="URL репозитория или путь к файлу тестового репозитория",
    )
    parser.add_argument(
        "--repo-mode", choices=REPO_MODES, default=REPO_MODE_ONLINE,
        help="режим работы с репозиторием: online (URL) или test (файл)",
    )
    parser.add_argument(
        "--output", default=DEFAULT_OUTPUT,
        help="имя файла с изображением графа (.svg)",
    )
    parser.add_argument(
        "--depth", type=int, default=DEFAULT_DEPTH,
        help="максимальная глубина анализа зависимостей",
    )
    parser.add_argument(
        "--filter", default="",
        help="подстрока для фильтрации пакетов",
    )
    return parser


def validate_package(name):
    """Проверить имя пакета."""
    if not PACKAGE_NAME_PATTERN.match(name):
        raise ConfigError(f"некорректное имя пакета: {name!r}")


def validate_repo(repo, repo_mode):
    """Проверить URL репозитория или путь к тестовому файлу."""
    if repo_mode == REPO_MODE_ONLINE:
        if not URL_PATTERN.match(repo):
            raise ConfigError(f"ожидался URL http(s), получено: {repo!r}")
    elif not os.path.isfile(repo):
        raise ConfigError(f"файл тестового репозитория не найден: {repo!r}")


def validate_output(output):
    """Проверить имя выходного файла."""
    if not output.lower().endswith(OUTPUT_EXTENSION):
        raise ConfigError("имя выходного файла должно заканчиваться на .svg")
    folder = os.path.dirname(output)
    if folder and not os.path.isdir(folder):
        raise ConfigError(f"папка для файла не существует: {folder!r}")


def validate_depth(depth):
    """Проверить максимальную глубину анализа."""
    if depth < MIN_DEPTH:
        raise ConfigError(f"глубина не может быть меньше {MIN_DEPTH}")


def validate_config(args):
    """Проверить все параметры; при ошибке бросить ConfigError."""
    validate_package(args.package)
    validate_repo(args.repo, args.repo_mode)
    validate_output(args.output)
    validate_depth(args.depth)


def print_dependencies(package, dependencies):
    """Вывести прямые зависимости пакета."""
    print(f"Прямые зависимости пакета {package}:")
    if not dependencies:
        print("  (нет зависимостей)")
    for name in dependencies:
        print(f"  {name}")


def run(args):
    """Получить и вывести зависимости; вернуть код завершения."""
    if args.repo_mode == REPO_MODE_TEST:
        print("Ошибка: режим test будет добавлен на этапе 3", file=sys.stderr)
        return EXIT_ERROR
    try:
        dependencies = pypi.get_dependencies(args.repo, args.package)
    except pypi.RepoError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    print_dependencies(args.package, dependencies)
    return EXIT_OK


def main(argv=None):
    """Точка входа: разобрать, проверить параметры и получить данные."""
    args = build_parser().parse_args(argv)
    try:
        validate_config(args)
    except ConfigError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
