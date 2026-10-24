"""Тесты получения зависимостей из репозитория (этап 2)."""

import contextlib
import io
import unittest
import urllib.error
from unittest import mock

from src import main as cli
from src import pypi

SAMPLE = {
    "info": {
        "requires_dist": [
            "charset_normalizer<4,>=2",
            "idna<4,>=2.5",
            'PySocks!=1.5.7,>=1.5.6; extra == "socks"',
            "idna>=2.5",
            'colorama; python_version < "3.9"',
        ]
    }
}


class ParsingTests(unittest.TestCase):
    """Проверка разбора описания пакета."""

    def test_build_url(self):
        """Адрес собирается без двойных слэшей."""
        url = pypi.build_url("https://pypi.org/pypi/", "requests")
        self.assertEqual(url, "https://pypi.org/pypi/requests/json")

    def test_parse_plain(self):
        """Имя извлекается из строки с версиями."""
        name = pypi.parse_requirement("idna<4,>=2.5")
        self.assertEqual(name, "idna")

    def test_parse_extra_skipped(self):
        """Необязательные зависимости (extra) пропускаются."""
        line = 'PySocks>=1.5.6; extra == "socks"'
        self.assertIsNone(pypi.parse_requirement(line))

    def test_extract_unique_names(self):
        """Список без extra и без повторов."""
        names = pypi.extract_dependencies(SAMPLE)
        self.assertEqual(names, ["charset_normalizer", "idna", "colorama"])

    def test_extract_no_requires(self):
        """Нет поля requires_dist — пустой список."""
        self.assertEqual(pypi.extract_dependencies({"info": {}}), [])

    def test_extract_bad_format(self):
        """Ответ не словарь — ошибка репозитория."""
        with self.assertRaises(pypi.RepoError):
            pypi.extract_dependencies([1, 2])


class NetworkErrorTests(unittest.TestCase):
    """Проверка обработки ошибок сети."""

    def test_not_found(self):
        """Ответ 404 превращается в понятную ошибку."""
        error = urllib.error.HTTPError("u", 404, "Not Found", None, None)
        with mock.patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaises(pypi.RepoError):
                pypi.fetch_json("https://pypi.org/pypi/nope/json")

    def test_no_connection(self):
        """Нет соединения — ошибка репозитория."""
        error = urllib.error.URLError("no network")
        with mock.patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaises(pypi.RepoError):
                pypi.fetch_json("https://pypi.org/pypi/x/json")


class MainTests(unittest.TestCase):
    """Проверка вывода зависимостей из main."""

    def test_prints_dependencies(self):
        """Зависимости печатаются построчно."""
        argv = ["--package", "requests", "--repo", "https://pypi.org/pypi"]
        buffer = io.StringIO()
        with mock.patch("src.pypi.get_dependencies", return_value=["idna"]):
            with contextlib.redirect_stdout(buffer):
                code = cli.main(argv)
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("  idna", buffer.getvalue())

    def test_repo_error_code(self):
        """Ошибка репозитория даёт код ошибки."""
        argv = ["--package", "requests", "--repo", "https://pypi.org/pypi"]
        error = pypi.RepoError("сбой")
        with mock.patch("src.pypi.get_dependencies", side_effect=error):
            with contextlib.redirect_stderr(io.StringIO()):
                code = cli.main(argv)
        self.assertEqual(code, cli.EXIT_ERROR)


if __name__ == "__main__":
    unittest.main()
