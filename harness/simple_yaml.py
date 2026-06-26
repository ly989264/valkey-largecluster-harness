"""Small YAML subset parser used by the harness configuration files.

The project intentionally keeps bootstrap dependencies low. This parser covers
the mapping/list/scalar subset used by inventories and scenarios; callers still
perform explicit schema validation after parsing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class SimpleYamlError(ValueError):
    """Raised when a configuration file uses unsupported YAML syntax."""


def load_yaml(path: str | Path) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8")
    parser = _Parser(text.splitlines())
    data = parser.parse()
    if not isinstance(data, dict):
        raise SimpleYamlError("top-level YAML value must be a mapping")
    return data


def dump_json_like(data: Any, indent: int = 2) -> str:
    import json

    return json.dumps(data, indent=indent, sort_keys=True) + "\n"


class _Parser:
    def __init__(self, lines: list[str]) -> None:
        self.lines: list[tuple[int, str]] = []
        for raw in lines:
            stripped = _strip_comment(raw).rstrip()
            if not stripped.strip():
                continue
            indent = len(stripped) - len(stripped.lstrip(" "))
            if "\t" in stripped[:indent]:
                raise SimpleYamlError("tabs are not supported for indentation")
            self.lines.append((indent, stripped.lstrip(" ")))
        self.index = 0

    def parse(self) -> Any:
        if not self.lines:
            return {}
        value = self._parse_block(self.lines[0][0])
        if self.index != len(self.lines):
            raise SimpleYamlError(f"unexpected content near line {self.index + 1}")
        return value

    def _parse_block(self, indent: int) -> Any:
        if self.index >= len(self.lines):
            return {}
        current_indent, content = self.lines[self.index]
        if current_indent != indent:
            raise SimpleYamlError(f"expected indent {indent}, got {current_indent}")
        if content.startswith("- "):
            return self._parse_list(indent)
        return self._parse_mapping(indent)

    def _parse_mapping(self, indent: int) -> dict[str, Any]:
        result: dict[str, Any] = {}
        while self.index < len(self.lines):
            current_indent, content = self.lines[self.index]
            if current_indent < indent:
                break
            if current_indent > indent:
                raise SimpleYamlError(f"unexpected indentation before {content!r}")
            if content.startswith("- "):
                break
            key, raw_value = _split_key_value(content)
            self.index += 1
            if raw_value == "":
                if self.index < len(self.lines) and self.lines[self.index][0] > indent:
                    result[key] = self._parse_block(self.lines[self.index][0])
                else:
                    result[key] = {}
            else:
                result[key] = _parse_scalar(raw_value)
        return result

    def _parse_list(self, indent: int) -> list[Any]:
        result: list[Any] = []
        while self.index < len(self.lines):
            current_indent, content = self.lines[self.index]
            if current_indent < indent:
                break
            if current_indent > indent:
                raise SimpleYamlError(f"unexpected indentation before {content!r}")
            if not content.startswith("- "):
                break
            item = content[2:].strip()
            self.index += 1
            if item == "":
                if self.index < len(self.lines) and self.lines[self.index][0] > indent:
                    result.append(self._parse_block(self.lines[self.index][0]))
                else:
                    result.append({})
                continue
            if ":" in item and not _is_quoted(item):
                key, raw_value = _split_key_value(item)
                mapping: dict[str, Any] = {key: _parse_scalar(raw_value) if raw_value else {}}
                while self.index < len(self.lines) and self.lines[self.index][0] > indent:
                    extra_indent = self.lines[self.index][0]
                    extra = self._parse_block(extra_indent)
                    if not isinstance(extra, dict):
                        raise SimpleYamlError("list item continuations must be mappings")
                    mapping.update(extra)
                result.append(mapping)
            else:
                result.append(_parse_scalar(item))
        return result


def _split_key_value(content: str) -> tuple[str, str]:
    if ":" not in content:
        raise SimpleYamlError(f"expected key: value mapping, got {content!r}")
    key, value = content.split(":", 1)
    key = key.strip()
    if not key:
        raise SimpleYamlError("mapping key cannot be empty")
    return key, value.strip()


def _strip_comment(raw: str) -> str:
    quote: str | None = None
    result: list[str] = []
    for ch in raw:
        if ch in {"'", '"'}:
            quote = None if quote == ch else ch if quote is None else quote
        if ch == "#" and quote is None:
            break
        result.append(ch)
    return "".join(result)


def _is_quoted(value: str) -> bool:
    return (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    )


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    if _is_quoted(value):
        return value[1:-1]
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value in {"null", "Null", "~"}:
        return None
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(part.strip()) for part in inner.split(",")]
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value
