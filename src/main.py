"""Визуализатор графа зависимостей: командная строка и вывод."""

import argparse
import functools
import os
import re
import sys

from src import plantuml, pypi, testrepo
from src.graph import GraphBuilder

EXIT_OK = 0
EXIT_ERROR = 1
MIN_DEPTH = 0
DEFAULT_DEPTH = 3
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
        "--output", default=None,
        help="имя SVG-файла; если не задан, изображение не создаётся",
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
    """Проверить имя выходного файла (если он задан)."""
    if output is None:
        return
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


def make_source(args):
    """Вернуть функцию «имя пакета -> список его зависимостей»."""
    if args.repo_mode == REPO_MODE_TEST:
        repo = testrepo.load_repo(args.repo)
        if args.package not in repo:
            raise pypi.RepoError(f"пакет {args.package} не описан в файле")
        return lambda name: repo.get(name, [])
    return functools.lru_cache(maxsize=None)(
        lambda name: pypi.get_dependencies(args.repo, name)
    )


def print_graph(package, graph, cycles):
    """Вывести граф зависимостей и найденные циклы."""
    print(f"Граф зависимостей пакета {package}:")
    for name, dependencies in graph.items():
        targets = ", ".join(dependencies) or "(нет зависимостей)"
        print(f"  {name} -> {targets}")
    if cycles:
        print("Обнаружены циклические зависимости:")
    for cycle in cycles:
        print("  " + " -> ".join(cycle))


def output_results(args, graph):
    """Сохранить диаграмму PlantUML и SVG, если задан параметр --output."""
    if args.output is None:
        return
    diagram = plantuml.build_diagram(args.package, graph)
    puml_path = os.path.splitext(args.output)[0] + ".puml"
    plantuml.write_file(puml_path, diagram.encode("utf-8"))
    print("Диаграмма PlantUML:")
    print(diagram)
    print(f"Диаграмма сохранена: {puml_path}")
    try:
        svg = plantuml.render_svg(diagram)
    except plantuml.RenderError as error:
        message = f"{error}; текст диаграммы сохранён в {puml_path}"
        raise plantuml.RenderError(message) from error
    plantuml.write_file(args.output, svg)
    print(f"Изображение сохранено: {args.output}")


def run(args):
    """Построить граф, вывести его и сохранить изображение."""
    try:
        builder = GraphBuilder(make_source(args), args.depth, args.filter)
        graph = builder.build(args.package)
        print_graph(args.package, graph, builder.cycles)
        output_results(args, graph)
    except (pypi.RepoError, plantuml.RenderError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_OK


def main(argv=None):
    """Точка входа: разобрать и проверить параметры, построить граф."""
    args = build_parser().parse_args(argv)
    try:
        validate_config(args)
    except ConfigError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
