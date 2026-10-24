"""Тесты тестового репозитория и режима test (этап 3)."""

import contextlib
import io
import os
import unittest

from src import main as cli
from src import pypi, testrepo

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def data_path(name):
    """Путь к файлу с тестовыми данными."""
    return os.path.join(DATA_DIR, name)


class ParseTests(unittest.TestCase):
    """Проверка разбора файла."""

    def test_parse_valid(self):
        """Комментарии и пустые строки пропускаются."""
        text = "# коммент\n\nA: B C\nB:\n"
        self.assertEqual(testrepo.parse_repo(text), {"A": ["B", "C"], "B": []})

    def test_missing_separator(self):
        """Строка без двоеточия — ошибка."""
        with self.assertRaises(pypi.RepoError):
            testrepo.parse_repo("A B C")

    def test_lowercase_name(self):
        """Имя не из заглавных букв — ошибка."""
        with self.assertRaises(pypi.RepoError):
            testrepo.parse_repo("A: b")

    def test_duplicate_package(self):
        """Повторное описание пакета — ошибка."""
        with self.assertRaises(pypi.RepoError):
            testrepo.parse_repo("A: B\nA: C")

    def test_missing_file(self):
        """Отсутствующий файл — ошибка репозитория."""
        with self.assertRaises(pypi.RepoError):
            testrepo.load_repo("no_such_file.txt")

    def test_load_data_file(self):
        """Файл с примером загружается."""
        repo = testrepo.load_repo(data_path("simple.txt"))
        self.assertEqual(repo["A"], ["B", "C"])


class MainTestModeTests(unittest.TestCase):
    """Проверка main в режиме test."""

    def run_main(self, name, extra=()):
        """Запустить main на файле name; вернуть (код, вывод)."""
        argv = ["--package", "A", "--repo", data_path(name)]
        argv += ["--repo-mode", "test"] + list(extra)
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = cli.main(argv)
        return code, buffer.getvalue()

    def test_prints_graph(self):
        """Граф печатается построчно."""
        code, output = self.run_main("simple.txt")
        self.assertEqual(code, cli.EXIT_OK)
        self.assertIn("  A -> B, C", output)

    def test_prints_cycle(self):
        """Цикл попадает в вывод."""
        _, output = self.run_main("cycle.txt")
        self.assertIn("A -> B -> C -> A", output)

    def test_broken_file(self):
        """Файл неверного формата даёт код ошибки."""
        with contextlib.redirect_stderr(io.StringIO()):
            code, _ = self.run_main("broken.txt")
        self.assertEqual(code, cli.EXIT_ERROR)


if __name__ == "__main__":
    unittest.main()
