#!/usr/bin/env python3
"""
Сводная таблица по results/pose_backend_comparison*.csv для текста ВКР.

Пример:
  python scripts/summarize_pose_comparison.py results/pose_backend_comparison_all_videos.csv
  python scripts/summarize_pose_comparison.py --latest --out docs/pose_comparison_table_fragment.md

Подставь реальный путь к CSV (не текст «ВСТАВЬ_ИМЯ»), либо используй --latest.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    parser = argparse.ArgumentParser(description="Сводка метрик compare_pose_backends по backend")
    parser.add_argument(
        "csv_path",
        nargs="?",
        type=Path,
        default=None,
        help="CSV из compare_pose_backends.py (или опусти и используй --latest)",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Взять самый новый файл results/pose_backend_comparison*.csv",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Записать markdown-таблицу в файл (иначе только stdout)",
    )
    args = parser.parse_args()

    if args.latest:
        candidates = sorted(
            REPO_ROOT.glob("results/pose_backend_comparison*.csv"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not candidates:
            raise SystemExit(
                "Не найден ни один results/pose_backend_comparison*.csv — сначала запусти run_pose_compare_all_ski_videos.sh"
            )
        csv_path = candidates[0]
        print(f"(используется самый новый: {csv_path.relative_to(REPO_ROOT)})", flush=True)
    elif args.csv_path:
        csv_path = args.csv_path if args.csv_path.is_absolute() else REPO_ROOT / args.csv_path
    else:
        raise SystemExit("Укажи путь к CSV или флаг --latest")

    if not csv_path.is_file():
        raise SystemExit(
            f"Файл не найден: {csv_path}\n"
            f"Список: ls results/pose_backend_comparison*.csv\n"
            f"Или: python3 scripts/summarize_pose_comparison.py --latest --out docs/pose_comparison_table_thesis.md"
        )

    df = pd.read_csv(csv_path)
    if "backend" not in df.columns:
        raise SystemExit("В CSV нет колонки backend")

    num_cols = [
        c
        for c in df.columns
        if c not in ("backend", "video", "error") and pd.api.types.is_numeric_dtype(df[c])
    ]
    agg = df.groupby("backend", dropna=False)[num_cols].agg(
        lambda s: float(np.nanmean(pd.to_numeric(s, errors="coerce")))
    )
    agg["videos"] = df.groupby("backend")["video"].count()

    # порядок столбцов для читаемости
    front = ["videos"] + [c for c in agg.columns if c != "videos"]
    agg = agg[[c for c in front if c in agg.columns]]

    md_lines = [
        "| Backend | " + " | ".join(agg.columns) + " |",
        "|" + "|".join(["---"] * (len(agg.columns) + 1)) + "|",
    ]
    for backend, row in agg.iterrows():
        cells = [str(backend)]
        for c in agg.columns:
            v = row[c]
            if c == "videos":
                cells.append(str(int(v)))
            elif isinstance(v, (float, np.floating)) and not np.isnan(v):
                cells.append(f"{float(v):.4f}")
            else:
                cells.append(str(v))
        md_lines.append("| " + " | ".join(cells) + " |")

    text = "\n".join(md_lines) + "\n"
    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            "<!-- Сводка из summarize_pose_comparison.py — вставить в ВКР или приложение -->\n\n"
            + text,
            encoding="utf-8",
        )
        print(f"✓ Записано: {args.out}", flush=True)


if __name__ == "__main__":
    main()
