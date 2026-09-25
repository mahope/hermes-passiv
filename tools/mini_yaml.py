"""Minimal YAML-læser til de to workflow-filer.

Hvorfor ikke PyYAML: `deploy-sites.yml` kører på `setup-python`, der ikke har
PyYAML installeret, så en gate der `import yaml` fejlede alle tre deploy-jobs i
CI (kørsel 36180367257, 25. september 2026). En gate må ikke afhænge af en
pakke ingen workflow installerer.

Dette er ikke en generel YAML-implementering. Den dækker den del af sproget de
to workflows bruger — mappings, sekvenser, inline-sekvenser, skalarskalarer,
`#`-kommentarer og null værdier — og den fejler højt i stedet for at gætte, hvis
den møder noget den ikke forstår. Selftesten i `test_deploy_workflow.py` binder
de få ting gaten læser fast, så en forkert parse kan ikke se grøn ud.
"""
from __future__ import annotations

import re
from typing import Any

_INT = re.compile(r"^[+-]?\d+$")


class YamlSubsetError(Exception):
    """Filen bruger YAML ud over den del denne læser forstår."""


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _strip_comment(text: str) -> str:
    """Fjern et `#`-kommentar, men ikke et `#` inde i en quotet streng."""
    quote = ""
    for i, char in enumerate(text):
        if quote:
            if char == quote:
                quote = ""
        elif char in "'\"":
            quote = char
        elif char == "#" and (i == 0 or text[i - 1] == " "):
            return text[:i].rstrip()
    return text.rstrip()


def _scalar(text: str) -> Any:
    text = text.strip()
    if text == "" or text in ("null", "~"):
        return None
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "'\"":
        return text[1:-1]
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        return [_scalar(part) for part in _split_flow(inner)] if inner else []
    if text.startswith("{") and text.endswith("}"):
        inner = text[1:-1].strip()
        out: dict[str, Any] = {}
        for part in _split_flow(inner):
            key, _, value = part.partition(":")
            out[_scalar(key)] = _scalar(value)
        return out
    if text in ("true", "True"):
        return True
    if text in ("false", "False"):
        return False
    if _INT.match(text):
        return int(text)
    return text


def _is_mapping_start(text: str) -> bool:
    """Er `- nøgle: værdi` starten på et mapping-element i en sekvens?"""
    quote = ""
    for i, char in enumerate(text):
        if quote:
            if char == quote:
                quote = ""
        elif char in "'\"":
            quote = char
        elif char == ":" and (i + 1 == len(text) or text[i + 1] == " "):
            return True
    return False


def _split_flow(text: str) -> list[str]:
    """Del `a, b` på komma uden at klippe inde i `[ ]` eller quotes."""
    parts: list[str] = []
    depth = 0
    quote = ""
    current: list[str] = []
    for char in text:
        if quote:
            current.append(char)
            if char == quote:
                quote = ""
            continue
        if char in "'\"":
            quote = char
        elif char in "[{":
            depth += 1
        elif char in "]}":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append("".join(current))
            current = []
            continue
        current.append(char)
    if current:
        parts.append("".join(current))
    return [p.strip() for p in parts if p.strip()]


class _Reader:
    def __init__(self, text: str) -> None:
        # Tabulator i YAML-indent er en fejl, ikke whitespace.
        if "\t" in text.split("\n")[0][: len(text) - len(text.lstrip())]:
            raise YamlSubsetError("tabulator i indrykning")
        self.lines = text.splitlines()

    def parse(self) -> Any:
        self.pos = 0
        value = self._node(self._peek_indent())
        self._skip()
        if self.pos < len(self.lines):
            raise YamlSubsetError(f"uforstået indhold: {self.lines[self.pos]!r}")
        return value

    # -- position --------------------------------------------------------
    def _skip(self) -> None:
        while self.pos < len(self.lines):
            stripped = self.lines[self.pos].strip()
            if not stripped or stripped.startswith("#"):
                self.pos += 1
            else:
                return

    def _peek(self) -> str | None:
        self._skip()
        return self.lines[self.pos] if self.pos < len(self.lines) else None

    def _peek_indent(self) -> int:
        line = self._peek()
        return _indent(line) if line is not None else 0

    # -- strukturer ------------------------------------------------------
    def _node(self, indent: int) -> Any:
        line = self._peek()
        if line is None:
            return None
        if _indent(line) != indent:
            raise YamlSubsetError(f"uventet indrykning: {line!r}")
        if _strip_comment(line).lstrip().startswith("- "):
            return self._sequence(indent)
        return self._mapping(indent)

    def _mapping(self, indent: int) -> dict[str, Any]:
        out: dict[str, Any] = {}
        while True:
            line = self._peek()
            if line is None or _indent(line) < indent:
                return out
            if _indent(line) > indent:
                raise YamlSubsetError(f"uventet indrykning under nøgle: {line!r}")
            body = _strip_comment(line).strip()
            if body.startswith("- "):
                return out
            key, sep, rest = body.partition(":")
            if not sep:
                raise YamlSubsetError(f"forventede `nøgle: værdi`, fandt: {line!r}")
            self.pos += 1
            out[_scalar(key)] = self._value(rest, indent)

    def _sequence(self, indent: int) -> list[Any]:
        out: list[Any] = []
        while True:
            line = self._peek()
            if line is None or _indent(line) != indent:
                return out
            body = _strip_comment(line).strip()
            if not body.startswith("- "):
                return out
            item = body[2:].strip()
            # `- nøgle: værdi` skrives om til en mapping på egen indrykning, så
            # de følgende nøgler i samme element kan læses af samme kodevej.
            self.lines[self.pos] = " " * (indent + 2) + item
            if _is_mapping_start(item):
                out.append(self._mapping(indent + 2))
            else:
                self.pos += 1
                out.append(_scalar(item))

    def _value(self, rest: str, indent: int) -> Any:
        rest = rest.strip()
        if rest[:1] in ("|", ">"):
            return self._block_scalar(indent)
        if rest:
            return _scalar(rest)
        child_indent = self._peek_indent()
        line = self._peek()
        if line is None:
            return None
        if child_indent > indent:
            return self._node(child_indent)
        if child_indent == indent and _strip_comment(line).lstrip().startswith("- "):
            # En sekvens må stå på samme indrykning som sin nøgle.
            return self._sequence(indent)
        return None

    def _block_scalar(self, indent: int) -> str:
        block: list[str] = []
        while self.pos < len(self.lines):
            line = self.lines[self.pos]
            if line.strip() and _indent(line) <= indent:
                break
            block.append(line)
            self.pos += 1
        while block and not block[0].strip():
            block.pop(0)
        dedent = min((_indent(l) for l in block if l.strip()), default=indent + 2)
        return "\n".join(l[dedent:] if len(l) >= dedent else l.lstrip() for l in block)


def parse(text: str) -> Any:
    return _Reader(text).parse()


def load_path(path) -> Any:
    return parse(open(path, encoding="utf-8").read())
