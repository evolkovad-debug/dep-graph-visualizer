"""Тесты построения графа зависимостей (этап 3)."""

import unittest

from src.graph import GraphBuilder

DIAMOND = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": ["E"], "E": []}
LONG_PATH = {"A": ["B", "C"], "B": ["C"], "C": ["D"], "D": []}
CYCLE = {"A": ["B"], "B": ["C"], "C": ["A", "D"], "D": []}


def build(repo, depth, substring=""):
    """Построить граф для пакета A по словарю repo."""
    builder = GraphBuilder(lambda name: repo.get(name, []), depth, substring)
    return builder.build("A"), builder.cycles


class DepthTests(unittest.TestCase):
    """Проверка ограничения глубины."""

    def test_full_graph(self):
        """Большая глубина даёт полный граф."""
        graph, cycles = build(DIAMOND, 10)
        self.assertEqual(graph, DIAMOND)
        self.assertEqual(cycles, [])

    def test_depth_zero(self):
        """Глубина 0 — только сам пакет."""
        graph, _ = build(DIAMOND, 0)
        self.assertEqual(graph, {"A": []})

    def test_depth_one(self):
        """Глубина 1 — пакет и его прямые зависимости."""
        graph, _ = build(DIAMOND, 1)
        self.assertEqual(graph, {"A": ["B", "C"], "B": [], "C": []})

    def test_shorter_path_wins(self):
        """Пакет, найденный сначала глубоко, раскрывается по короткому пути."""
        graph, _ = build(LONG_PATH, 2)
        expected = {"A": ["B", "C"], "B": ["C"], "C": ["D"], "D": []}
        self.assertEqual(graph, expected)


class FilterTests(unittest.TestCase):
    """Проверка фильтра по подстроке."""

    def test_filter_excludes_package(self):
        """Пакет с подстрокой в имени не попадает в граф."""
        graph, _ = build(DIAMOND, 10, "C")
        expected = {"A": ["B"], "B": ["D"], "D": ["E"], "E": []}
        self.assertEqual(graph, expected)

    def test_empty_filter_ignored(self):
        """Пустая подстрока ничего не исключает."""
        graph, _ = build(DIAMOND, 10, "")
        self.assertEqual(graph, DIAMOND)


class CycleTests(unittest.TestCase):
    """Проверка циклических зависимостей."""

    def test_cycle_found(self):
        """Цикл не приводит к бесконечному обходу и находится."""
        graph, cycles = build(CYCLE, 10)
        self.assertEqual(graph["C"], ["A", "D"])
        self.assertEqual(cycles, [["A", "B", "C", "A"]])

    def test_self_dependency(self):
        """Пакет, зависящий от самого себя, — цикл."""
        graph, cycles = build({"A": ["A"]}, 10)
        self.assertEqual(graph, {"A": ["A"]})
        self.assertEqual(cycles, [["A", "A"]])


if __name__ == "__main__":
    unittest.main()
