#!/usr/bin/env python3
"""
excel-to-report.py — Excel / CSV to unified report
=================================================
Reads scattered .xlsx / .csv files from ./input/ and produces:
  - report.xlsx  (sheet "All Data" + sheet "Summary")
  - summary.txt  (plain-text summary)

Usage:
  python3 excel-to-report.py [--input input] [--output output]
  python3 excel-to-report.py --help

Rules (transparent, no hidden magic):
  * Column names are matched case-insensitively after stripping spaces.
    Known aliases: name/الاسم, phone/هاتف/واتساب, business/النشاط,
    message/رسالة, amount/المبلغ, date/التاريخ.
    Unknown columns are kept as-is.
  * Empty rows are skipped. Exact duplicate rows are removed (counted).
  * Dates/amounts are kept as text if they cannot be parsed — nothing is
    silently dropped; the summary reports how many rows were skipped.
  * No network, no credentials, no external services. Stdlib + openpyxl only.

Demo service this powers: "Excel to clean report" — $20-40 per job.
"""

import argparse
import csv
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill

ALIASES = {
    "name": "Name", "الاسم": "Name", "customer": "Name", "client": "Name",
    "phone": "Phone", "هاتف": "Phone", "whatsapp": "Phone", "واتساب": "Phone",
    "mobile": "Phone", "جوال": "Phone",
    "business": "Business", "النشاط": "Business", "type": "Business",
    "message": "Message", "رسالة": "Message", "notes": "Message",
    "amount": "Amount", "المبلغ": "Amount", "price": "Amount",
    "date": "Date", "التاريخ": "Date", "timestamp": "Date",
}

HEADER_FILL = PatternFill("solid", fgColor="0F4C5C")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
TITLE_FONT = Font(bold=True, size=13, color="0F4C5C")


def normalize_header(raw: str) -> str:
    key = str(raw or "").strip().lower()
    return ALIASES.get(key, str(raw or "").strip() or "Column")


def read_xlsx(path: Path):
    wb = load_workbook(path, data_only=True, read_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return [], []
    headers = [normalize_header(h) for h in rows[0]]
    return headers, [dict(zip(headers, r)) for r in rows[1:]]


def read_csv(path: Path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return [], []
        headers = [normalize_header(h) for h in reader.fieldnames]
        return headers, [dict(zip(headers, [row.get(h) for h in reader.fieldnames])) for row in reader]


def collect(input_dir: Path):
    files = sorted(p for p in input_dir.iterdir()
                   if p.is_file() and p.suffix.lower() in (".xlsx", ".csv"))
    all_headers, all_rows, stats = [], [], {"files": 0, "rows_read": 0,
                                            "empty_rows": 0, "duplicates": 0}
    seen = set()
    for path in files:
        try:
            headers, rows = (read_xlsx(path) if path.suffix.lower() == ".xlsx"
                             else read_csv(path))
        except Exception as exc:  # noqa: BLE001 - report and continue
            print(f"  ! skipped {path.name}: {exc}", file=sys.stderr)
            stats.setdefault("errors", []).append(f"{path.name}: {exc}")
            continue
        stats["files"] += 1
        for header in headers:
            if header not in all_headers:
                all_headers.append(header)
        for row in rows:
            stats["rows_read"] += 1
            values = {h: ("" if row.get(h) is None else str(row.get(h)).strip())
                      for h in all_headers}
            if not any(values.values()):
                stats["empty_rows"] += 1
                continue
            key = tuple(values[h] for h in all_headers)
            if key in seen:
                stats["duplicates"] += 1
                continue
            seen.add(key)
            all_rows.append(values)
    return all_headers, all_rows, stats


def write_report(headers, rows, stats, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "All Data"
    ws.append(headers)
    for cell in ws[1]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
    for row in rows:
        ws.append([row.get(h, "") for h in headers])
    for col in ws.columns:
        width = max((len(str(c.value or "")) for c in col), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(max(width + 2, 12), 45)

    summary = wb.create_sheet("Summary")
    summary["A1"] = "Report summary"
    summary["A1"].font = TITLE_FONT
    lines = [
        ("Generated", datetime.now().strftime("%Y-%m-%d %H:%M")),
        ("Files processed", stats["files"]),
        ("Rows read", stats["rows_read"]),
        ("Rows in report", len(rows)),
        ("Empty rows skipped", stats["empty_rows"]),
        ("Duplicate rows removed", stats["duplicates"]),
    ]
    for label, value in lines:
        summary.append([label, value])
    if "Business" in headers:
        summary.append([])
        summary.append(["Business type", "Count"])
        for biz, count in Counter(r.get("Business", "") for r in rows).most_common():
            summary.append([biz or "(blank)", count])
    summary.column_dimensions["A"].width = 24
    summary.column_dimensions["B"].width = 14

    xlsx_path = out_dir / "report.xlsx"
    wb.save(xlsx_path)

    counts = Counter(r.get("Business", "") for r in rows) if "Business" in headers else {}
    txt = ["Excel to Report — summary", f"Generated: {lines[0][1]}", ""]
    txt += [f"{label}: {value}" for label, value in lines[1:]]
    if counts:
        txt += ["", "By business type:"]
        txt += [f"  {biz or '(blank)'}: {n}" for biz, n in counts.most_common()]
    if stats.get("errors"):
        txt += ["", "Files skipped with errors:"]
        txt += [f"  {e}" for e in stats["errors"]]
    txt_path = out_dir / "summary.txt"
    txt_path.write_text("\n".join(txt) + "\n", encoding="utf-8")
    return xlsx_path, txt_path


def main() -> int:
    ap = argparse.ArgumentParser(description="Merge scattered xlsx/csv files into one clean report.")
    ap.add_argument("--input", default="input", help="Folder with source files (default: input)")
    ap.add_argument("--output", default="output", help="Folder for report.xlsx + summary.txt (default: output)")
    args = ap.parse_args()
    input_dir = Path(args.input)
    if not input_dir.is_dir():
        print(f"error: input folder not found: {input_dir}", file=sys.stderr)
        return 2
    headers, rows, stats = collect(input_dir)
    if not headers:
        print("error: no readable .xlsx/.csv files found in input folder.", file=sys.stderr)
        return 1
    xlsx_path, txt_path = write_report(headers, rows, stats, Path(args.output))
    print(f"files processed : {stats['files']}")
    print(f"rows read       : {stats['rows_read']}")
    print(f"rows in report  : {len(rows)}  (empty skipped: {stats['empty_rows']}, duplicates removed: {stats['duplicates']})")
    print(f"report          : {xlsx_path}")
    print(f"summary         : {txt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
