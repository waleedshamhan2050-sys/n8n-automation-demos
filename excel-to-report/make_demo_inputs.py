#!/usr/bin/env python3
"""Generate demo input files: 2 xlsx + 1 csv with realistic scattered leads,
including one exact duplicate and one empty row (both must be handled)."""
import csv
from pathlib import Path
from openpyxl import Workbook

base = Path(__file__).resolve().parent / "input"
base.mkdir(parents=True, exist_ok=True)

wb = Workbook(); ws = wb.active
ws.append(["Name", "Phone", "Business", "Message"])
ws.append(["Ahmed Ali", "771 123 456", "Restaurant", "Need a menu update"])
ws.append(["Sara Nasser", "772 234 567", "Clinic", "Appointment booking help"])
ws.append(["Ahmed Ali", "771 123 456", "Restaurant", "Need a menu update"])  # duplicate
ws.append([None, None, None, None])  # empty row
wb.save(base / "leads-shop-a.xlsx")

wb = Workbook(); ws = wb.active
ws.append(["name", "phone", "business", "amount"])
ws.append(["Omar Saleh", "773 345 678", "Shop", 120])
ws.append(["Layla Hassan", "774 456 789", "Restaurant", 85])
wb.save(base / "orders-shop-b.xlsx")

with open(base / "leads-phone.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Name", "Phone", "Business", "Message"])
    w.writerow(["Khaled Mansour", "775 567 890", "Services", "Quote for delivery"])
    w.writerow(["Mona Adel", "776 678 901", "Clinic", "Opening hours?"])
print("demo inputs written to", base)
