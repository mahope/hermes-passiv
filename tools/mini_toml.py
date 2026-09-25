#!/usr/bin/env python3
"""Minimal TOML-læser til den del af formatet vores egne filer bruger.

Hvorfor ikke `tomllib`/`tomli`: `tomllib` kom først i Python 3.11, og CI'en
kører `setup-python` med 3.12 mens denne maskines system-Python er 3.9. Samme
problem som `tools/mini_yaml.py` løste for workflowene (kørsel 36180367257 døde
på `ModuleNotFoundError: No module named 'yaml'`): en gate må ikke afhænge af en
pakke der ikke er der.

Derfor bruges den indbyggede læser når den findes, og denne ellers:

    try:
        import tomllib
    except ModuleNotFoundError:
        import mini_toml as tomllib

Understøttet, og kun det: kommentarer, tabeller, nøgle = "streng", nøgle = tal,
nøgle = true/false, nøgle = [liste] på én og flere linjer, og
`license = { text = "MIT" }`. Alt andet — arrays of tables, datoer, inline
tabeller med flere nøgler end én — fejler **hvidt** med fil og linje, fordi en
læser der gætter er værre end ingen læser.
"""
from __future__ import annotations

import re
from pathlib import Path

__all__ = ["TOMLDecodeError", "loads", "load"]


class TOMLDecodeError(ValueError):
    """TOML vi ikke understøtter. Bærer altid fil og linje."""

    def __init__(self, message: str, path: Path | None = None, line: int | None = None) -> None:
        where = ""
        if path is not None and line is not None:
            where = f" ({path}:{line})"
        elif line is not None:
            where = f" (linje {line})"
        super().__init__(f"{message}{where}")


_KEY = r"[A-Za-z0-9_.\-]+"
_LINE_COMMENT = re.compile(r"#.*$")
_STRING = re.compile(r'"((?:[^"\\]|\\.)*)"')
_SCALAR = re.compile(rf"^(?P<key>{_KEY})\s*=\s*(?P<val>.+)$")


def _strip_comment(line: str) -> str:
    """Fjern en `#`-kommentar der ikke ligger i en streng."""
    in_string = False
    escaped = False
    for index, char in enumerate(line):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char == "#":
            return line[:index]
    return line


def _unescape(raw: str) -> str:
    return (
        raw.replace("\\\\", "\x00")
        .replace('\\"', '"')
        .replace("\\n", "\n")
        .replace("\\t", "\t")
        .replace("\x00", "\\")
    )


def _parse_value(raw: str, path: Path | None, line: int) -> object:
    raw = raw.strip()
    if raw.startswith("[") or raw.startswith("{"):
        if raw.startswith("{"):
            match = re.fullmatch(r"\{\s*(\w+)\s*=\s*(\"(?:[^\"\\]|\\.)*\")\s*\}", raw)
            if not match:
                raise TOMLDecodeError(
                    "inline-tabel understøttes kun som { key = \"værdi\" }", path, line
                )
            return {match.group(1): _unescape(_STRING.match(match.group(2)).group(1))}
        inner = raw[1:-1].strip()
        if not inner:
            return []
        items = []
        for part in re.findall(r'"((?:[^"\\]|\\.)*)"', inner):
            items.append(_unescape(part))
        leftover = _STRING.sub("", inner).replace(",", " ").strip()
        if leftover:
            raise TOMLDecodeError(
                f"liste-elementer skal være strenge i mini_toml, fik: {leftover!r}", path, line
            )
        return items
    if raw in ("true", "false"):
        return raw == "true"
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    match = _STRING.fullmatch(raw)
    if match:
        return _unescape(match.group(1))
    raise TOMLDecodeError(f"værdi-formen {raw!r} understøttes ikke", path, line)


def loads(text: str, path: Path | None = None) -> dict:
    root: dict = {}
    table = root
    pending_key: str | None = None
    pending_raw: list[str] = []

    for number, original in enumerate(text.splitlines(), start=1):
        line = _strip_comment(original).strip()
        if not line:
            continue

        if pending_key is not None:
            pending_raw.append(line)
            joined = " ".join(pending_raw)
            if joined.count("[") <= joined.count("]"):
                table[pending_key] = _parse_value(joined, path, number)
                pending_key, pending_raw = None, []
            continue

        if line.startswith("[["):
            raise TOMLDecodeError("array-of-tables ([[x]]) understøttes ikke", path, number)
        if line.startswith("["):
            if not line.endswith("]"):
                raise TOMLDecodeError("uafsluttet tabeloverskrift", path, number)
            node = root
            for part in line[1:-1].strip().split("."):
                part = part.strip().strip('"')
                if not part:
                    raise TOMLDecodeError("tom tabelnøgle", path, number)
                node = node.setdefault(part, {})
                if not isinstance(node, dict):
                    raise TOMLDecodeError(
                        f"{part!r} er allerede en skala, kan ikke være en tabel", path, number
                    )
            table = node
            continue

        match = _SCALAR.match(line)
        if not match:
            raise TOMLDecodeError(f"kan ikke læse linjen: {original.strip()!r}", path, number)
        key, raw = match.group("key"), match.group("val").strip()
        if raw.startswith("[") and raw.count("[") > raw.count("]"):
            pending_key, pending_raw = key, [raw]
            continue
        table[key] = _parse_value(raw, path, number)

    if pending_key is not None:
        raise TOMLDecodeError(f"uafsluttet værdi for {pending_key!r}", path)
    return root


def load(path: Path) -> dict:
    return loads(path.read_text(encoding="utf-8"), path)
