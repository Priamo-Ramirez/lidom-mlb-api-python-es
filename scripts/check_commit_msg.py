"""Valida mensajes de commit con formato Conventional Commits."""

from __future__ import annotations

import re
import sys
from pathlib import Path

CONVENTIONAL_PATTERN = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"(\([a-z0-9._/-]+\))?(!)?: [^\s].+$"
)

# Mensajes automáticos habituales que no siguen Conventional Commits.
ALLOWED_PREFIXES = (
    "Merge ",
    "Revert \"",
    "fixup! ",
    "squash! ",
    "Initial commit",
)


def is_valid_message(message: str) -> bool:
    first_line = message.splitlines()[0].strip()
    if not first_line:
        return False

    if first_line.startswith(ALLOWED_PREFIXES):
        return True

    return bool(CONVENTIONAL_PATTERN.match(first_line))


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: check_commit_msg.py <archivo_commit_msg>")
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"No existe el archivo de mensaje de commit: {path}")
        return 2

    message = path.read_text(encoding="utf-8").strip()
    if is_valid_message(message):
        return 0

    print("Mensaje de commit inválido.")
    print("Formato esperado: <tipo>(<scope opcional>): <descripción>")
    print("Tipos permitidos: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert")
    print("Ejemplo válido: feat(cli): agregar comando today")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
