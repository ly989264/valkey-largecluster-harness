"""Tiny YAML reader for simple repository fixtures.

The loader intentionally supports only dictionaries, lists, and scalar values.
JSON is accepted by the higher-level config loader before this fallback.
"""


class MiniYamlError(ValueError):
    pass


def parse_scalar(value):
    value = value.strip()
    if value == "":
        return ""
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value in {"null", "None", "~"}:
        return None
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(part.strip()) for part in inner.split(",")]
    try:
        return int(value)
    except ValueError:
        return value


def parse(text):
    root = {}
    stack = [(-1, root)]
    lines = text.splitlines()
    for lineno, raw in enumerate(lines, 1):
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent % 2:
            raise MiniYamlError(f"line {lineno}: indentation must use multiples of two spaces")
        stripped = line.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise MiniYamlError(f"line {lineno}: invalid indentation")
        parent = stack[-1][1]
        if stripped.startswith("- "):
            if not isinstance(parent, list):
                raise MiniYamlError(f"line {lineno}: list item without list parent")
            item = stripped[2:].strip()
            if ":" in item:
                key, value = item.split(":", 1)
                obj = {key.strip(): parse_scalar(value)}
                parent.append(obj)
                stack.append((indent, obj))
            else:
                parent.append(parse_scalar(item))
            continue
        if ":" not in stripped:
            raise MiniYamlError(f"line {lineno}: expected key: value")
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not isinstance(parent, dict):
            raise MiniYamlError(f"line {lineno}: mapping entry without mapping parent")
        if value:
            parent[key] = parse_scalar(value)
        else:
            next_container = _container_for_next(lines, lineno)
            parent[key] = next_container
            stack.append((indent, next_container))
    return root


def _container_for_next(lines, lineno):
    for raw in lines[lineno:]:
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        return [] if line.strip().startswith("- ") else {}
    return {}
