"""Построение графа зависимостей алгоритмом DFS (обход с рекурсией)."""


class GraphBuilder:
    """Строит граф зависимостей обходом в глубину.

    Граф хранится как словарь «пакет -> список его зависимостей».
    """

    def __init__(self, get_dependencies, max_depth, substring=""):
        """Запомнить источник данных и ограничения анализа."""
        self.get_dependencies = get_dependencies
        self.max_depth = max_depth
        self.substring = substring
        self.graph = {}
        self.cycles = []
        self._best_depth = {}
        self._path = []

    def build(self, root):
        """Построить граф для пакета root и вернуть его."""
        self._visit(root, 0)
        return self.graph

    def _is_excluded(self, package):
        """Проверить, что имя пакета содержит подстроку-фильтр."""
        return bool(self.substring) and self.substring in package

    def _register_cycle(self, package):
        """Запомнить цикл, который замыкается на пакете package."""
        start = self._path.index(package)
        cycle = self._path[start:] + [package]
        if cycle not in self.cycles:
            self.cycles.append(cycle)

    def _visit(self, package, depth):
        """Рекурсивно обойти пакет package и его зависимости."""
        if package in self._path:
            self._register_cycle(package)
            return
        known = self._best_depth.get(package)
        if known is not None and known <= depth:
            return
        self._best_depth[package] = depth
        self.graph[package] = []
        if depth >= self.max_depth:
            return
        self._path.append(package)
        for dependency in self.get_dependencies(package):
            if self._is_excluded(dependency):
                continue
            if dependency not in self.graph[package]:
                self.graph[package].append(dependency)
            self._visit(dependency, depth + 1)
        self._path.pop()
