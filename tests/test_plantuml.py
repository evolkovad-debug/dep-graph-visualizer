"""Тесты диаграммы PlantUML и сохранения изображения (этап 5)."""

import contextlib
import io
import os
import tempfile
import unittest
import urllib.error
from unittest import mock

from src import main as cli
from src import plantuml

GRAPH = {"A": ["B", "C"], "B": [], "C": []}
SVG_DATA = b'<?xml version="1.0"?><svg></svg>'


def fake_reply(data):
    """Подменить ответ urlopen: вернуть объект с методом read."""
    reply = mock.MagicMock()
    reply.__enter__.return_value.read.return_value = data
    return reply


class DiagramTests(unittest.TestCase):
    """Проверка текста диаграммы."""

    def test_diagram_structure(self):
        """Диаграмма содержит узлы и стрелки зависимостей."""
        text = plantuml.build_diagram("A", GRAPH)
        self.assertTrue(text.startswith("@startuml"))
        self.assertTrue(text.rstrip().endswith("@enduml"))
        self.assertIn('rectangle "A" as n0 #LightBlue', text)
        self.assertIn("n0 --> n1", text)
        self.assertIn("n0 --> n2", text)

    def test_only_root_highlighted(self):
        """Цветом выделен только анализируемый пакет."""
        text = plantuml.build_diagram("A", GRAPH)
        self.assertEqual(text.count("#LightBlue"), 1)

    def test_encode_known_example(self):
        """Кодирование совпадает с примером из документации PlantUML."""
        encoded = plantuml.encode_diagram("Bob -> Alice : hello")
        self.assertEqual(encoded, "SyfFKj2rKt3CoKnELR1Io4ZDoSa70000")


class RenderTests(unittest.TestCase):
    """Проверка получения изображения (без реальной сети)."""

    def test_render_ok(self):
        """Ответ с SVG возвращается как есть."""
        with mock.patch("urllib.request.urlopen") as opener:
            opener.return_value = fake_reply(SVG_DATA)
            result = plantuml.render_svg("@startuml\n@enduml")
        self.assertEqual(result, SVG_DATA)

    def test_render_not_svg(self):
        """Ответ без SVG — ошибка."""
        with mock.patch("urllib.request.urlopen") as opener:
            opener.return_value = fake_reply(b"<html></html>")
            with self.assertRaises(plantuml.RenderError):
                plantuml.render_svg("x")

    def test_render_http_error(self):
        """Ошибка HTTP превращается в RenderError."""
        error = urllib.error.HTTPError("u", 500, "Error", None, None)
        with mock.patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaises(plantuml.RenderError):
                plantuml.render_svg("x")

    def test_render_no_network(self):
        """Нет соединения — RenderError."""
        error = urllib.error.URLError("no network")
        with mock.patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaises(plantuml.RenderError):
                plantuml.render_svg("x")


class MainOutputTests(unittest.TestCase):
    """Проверка параметра --output в main."""

    def run_main(self, folder, extra=()):
        """Запустить main в режиме test; вернуть код возврата."""
        repo = os.path.join(os.path.dirname(__file__), "data", "simple.txt")
        argv = ["--package", "A", "--repo", repo, "--repo-mode", "test"]
        argv += ["--output", os.path.join(folder, "graph.svg")] + list(extra)
        with contextlib.redirect_stdout(io.StringIO()):
            with contextlib.redirect_stderr(io.StringIO()):
                return cli.main(argv)

    def test_files_created(self):
        """Создаются и .puml, и .svg."""
        with tempfile.TemporaryDirectory() as folder:
            with mock.patch("src.plantuml.render_svg", return_value=SVG_DATA):
                code = self.run_main(folder)
            self.assertEqual(code, cli.EXIT_OK)
            self.assertTrue(os.path.isfile(os.path.join(folder, "graph.svg")))
            self.assertTrue(os.path.isfile(os.path.join(folder, "graph.puml")))

    def test_render_failure_keeps_puml(self):
        """При сбое сервера текст диаграммы всё равно сохраняется."""
        error = plantuml.RenderError("сбой")
        with tempfile.TemporaryDirectory() as folder:
            with mock.patch("src.plantuml.render_svg", side_effect=error):
                code = self.run_main(folder)
            self.assertEqual(code, cli.EXIT_ERROR)
            self.assertTrue(os.path.isfile(os.path.join(folder, "graph.puml")))
            self.assertFalse(os.path.exists(os.path.join(folder, "graph.svg")))

    def test_no_output_no_files(self):
        """Без --output файлы не создаются и сервер не вызывается."""
        argv = ["--package", "A", "--repo-mode", "test", "--repo"]
        repo = os.path.join(os.path.dirname(__file__), "data", "simple.txt")
        with mock.patch("src.plantuml.render_svg") as render:
            with contextlib.redirect_stdout(io.StringIO()):
                code = cli.main(argv + [repo])
        self.assertEqual(code, cli.EXIT_OK)
        render.assert_not_called()


if __name__ == "__main__":
    unittest.main()
