"""Import and validate the three-column school recipient workbook."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import pandas as pd

REQUIRED_COLUMNS = ("E-mail", "ID_Aluno", "Escola")

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _normalise_columns(columns: Iterable[object]) -> dict[str, str]:
    aliases = {
        "email": "E-mail",
        "e-mail": "E-mail",
        "mail": "E-mail",
        "id aluno": "ID_Aluno",
        "id_aluno": "ID_Aluno",
        "idaluno": "ID_Aluno",
        "escola": "Escola",
        "nome da escola": "Escola",
    }

    result: dict[str, str] = {}

    for column in columns:
        key = str(column).strip().casefold()
        key = re.sub(r"\s+", " ", key)

        if key in aliases:
            result[str(column)] = aliases[key]

    return result


def load_students(file_path: str | Path) -> list[dict[str, str]]:
    """Read and validate an XLSX, XLSM or CSV student workbook."""

    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        frame = pd.read_csv(
            path,
            dtype=str,
            keep_default_na=False,
        )

    elif suffix in {".xlsx", ".xlsm"}:
        frame = pd.read_excel(
            path,
            dtype=str,
            keep_default_na=False,
        )

    else:
        raise ValueError(
            "Formato não suportado. Utiliza .xlsx, .xlsm ou .csv."
        )

    frame = frame.rename(
        columns=_normalise_columns(frame.columns)
    )

    missing = [
        name
        for name in REQUIRED_COLUMNS
        if name not in frame.columns
    ]

    if missing:
        raise ValueError(
            "Faltam colunas obrigatórias: " + ", ".join(missing)
        )

    records: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    errors: list[str] = []

    for index, row in frame.iterrows():
        line = int(index) + 2

        email = str(row["E-mail"]).strip()
        student_id = str(row["ID_Aluno"]).strip()
        school = str(row["Escola"]).strip()

        if not email or not EMAIL_RE.fullmatch(email):
            errors.append(
                f"Linha {line}: endereço de e-mail vazio ou inválido."
            )

        if not student_id or student_id.casefold() in {"nan", "none"}:
            errors.append(
                f"Linha {line}: ID_Aluno vazio."
            )

        if not school:
            errors.append(
                f"Linha {line}: Escola vazia."
            )

        if not student_id or not school:
            continue

        identity = (
            school.casefold(),
            student_id.casefold(),
        )

        if identity in seen:
            errors.append(
                f"Linha {line}: ID_Aluno duplicado na escola {school} "
                f"({student_id})."
            )
            continue

        seen.add(identity)

        if email and EMAIL_RE.fullmatch(email):
            records.append(
                {
                    "email": email,
                    "student_id": student_id,
                    "school": school,
                }
            )

    if errors:
        raise ValueError("\n".join(errors))

    return records
