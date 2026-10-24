"""Тесты проверки параметров командной строки (этап 1)."""

import os
import tempfile
import unittest

from src import main as cli


class ValidationTests(unittest.TestCase):
    """Проверка функций валидации параметров."""

    def test_valid_package(self):
        """Обычное имя пакета принимается."""
        cli.validate_package("requests")

    def test_invalid_package(self):
        """Имя с пробелом отвергается."""
        with self.assertRaises(cli.ConfigError):
            cli.validate_package("bad name")

    def test_online_repo_needs_url(self):
        """В режиме online нужен URL, а не путь."""
        with self.assertRaises(cli.ConfigError):
            cli.validate_repo("not-a-url", cli.REPO_MODE_ONLINE)

    def test_online_repo_url_ok(self):
        """Корректный URL принимается."""
        cli.validate_repo("https://pypi.org/pypi", cli.REPO_MODE_ONLINE)

    def test_test_repo_missing_file(self):
        """Несуществующий тестовый файл отвергается."""
        with self.assertRaises(cli.ConfigError):
            cli.validate_repo("no_such_file.txt", cli.REPO_MODE_TEST)

    def test_test_repo_existing_file(self):
        """Существующий тестовый файл принимается."""
        with tempfile.NamedTemporaryFile() as handle:
            cli.validate_repo(handle.name, cli.REPO_MODE_TEST)

    def test_output_needs_svg(self):
        """Файл без расширения .svg отвергается."""
        with self.assertRaises(cli.ConfigError):
            cli.validate_output("graph.png")

    def test_output_missing_folder(self):
        """Несуществующая папка для файла отвергается."""
        path = os.path.join("no_such_dir", "graph.svg")
        with self.assertRaises(cli.ConfigError):
            cli.validate_output(path)

    def test_negative_depth(self):
        """Отрицательная глубина отвергается."""
        with self.assertRaises(cli.ConfigError):
            cli.validate_depth(-1)

    def test_zero_depth_ok(self):
        """Нулевая глубина допустима."""
        cli.validate_depth(0)


class MainTests(unittest.TestCase):
    """Проверка кода возврата main."""

    def test_success(self):
        """Корректные параметры дают код 0."""
        argv = ["--package", "requests", "--repo", "https://pypi.org/pypi"]
        self.assertEqual(cli.main(argv), cli.EXIT_OK)

    def test_error(self):
        """Некорректные параметры дают код ошибки."""
        argv = ["--package", "??", "--repo", "https://pypi.org/pypi"]
        self.assertEqual(cli.main(argv), cli.EXIT_ERROR)


if __name__ == "__main__":
    unittest.main()
