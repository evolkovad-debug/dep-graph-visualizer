"""Диаграмма PlantUML для графа зависимостей и получение SVG-изображения."""

import urllib.error
import urllib.request
import zlib

SERVER_URL = "https://www.plantuml.com/plantuml/svg/"
REQUEST_TIMEOUT = 30
USER_AGENT = "dep-graph-visualizer/1.0"
SVG_MARKER = b"<svg"
ROOT_COLOR = "#LightBlue"
ALPHABET = (
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz-_"
)
GROUP_SIZE = 3


class RenderError(Exception):
    """Ошибка при получении или сохранении изображения."""


def build_diagram(root, graph):
    """Сформировать текст диаграммы PlantUML по графу зависимостей."""
    aliases = {name: f"n{index}" for index, name in enumerate(graph)}
    lines = [
        "@startuml",
        "skinparam shadowing false",
        f"title Dependencies of {root}",
    ]
    for name, alias in aliases.items():
        color = f" {ROOT_COLOR}" if name == root else ""
        lines.append(f'rectangle "{name}" as {alias}{color}')
    for name, dependencies in graph.items():
        for dependency in dependencies:
            lines.append(f"{aliases[name]} --> {aliases[dependency]}")
    lines.append("@enduml")
    return "\n".join(lines) + "\n"


def encode_group(first, second, third):
    """Закодировать три байта четырьмя символами алфавита PlantUML."""
    indexes = (
        first >> 2,
        ((first & 0x3) << 4) | (second >> 4),
        ((second & 0xF) << 2) | (third >> 6),
        third & 0x3F,
    )
    return "".join(ALPHABET[index] for index in indexes)


def encode_diagram(text):
    """Сжать текст диаграммы и закодировать его для адреса сервера."""
    compressor = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)
    data = compressor.compress(text.encode("utf-8")) + compressor.flush()
    data += bytes(-len(data) % GROUP_SIZE)
    groups = [
        encode_group(*data[start:start + GROUP_SIZE])
        for start in range(0, len(data), GROUP_SIZE)
    ]
    return "".join(groups)


def render_svg(text):
    """Получить SVG-изображение диаграммы с сервера PlantUML."""
    url = SERVER_URL + encode_diagram(text)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as reply:
            data = reply.read()
    except urllib.error.HTTPError as error:
        message = f"сервер PlantUML ответил ошибкой {error.code}"
        raise RenderError(message) from error
    except OSError as error:
        message = f"не удалось связаться с сервером PlantUML: {error}"
        raise RenderError(message) from error
    if SVG_MARKER not in data:
        raise RenderError("сервер PlantUML вернул не SVG-изображение")
    return data


def write_file(path, data):
    """Записать байты data в файл path."""
    try:
        with open(path, "wb") as handle:
            handle.write(data)
    except OSError as error:
        raise RenderError(f"не удалось записать {path!r}: {error}") from error
