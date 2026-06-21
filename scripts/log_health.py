import argparse
import csv
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "health.csv"
HEADERS = [
    "date",
    "time",
    "height_cm",
    "weight_kg",
    "body_fat_pct",
    "fat_mass_kg",
    "lean_mass_kg",
    "hydration_pct",
    "source",
    "notes",
]


def require_file():
    if not CSV_PATH.exists():
        raise SystemExit("Missing data/health.csv. Run: python scripts/init_data.py")


def validate_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise SystemExit("date must use YYYY-MM-DD format") from exc
    return value


def validate_time(value):
    try:
        datetime.strptime(value, "%H:%M")
    except ValueError as exc:
        raise SystemExit("time must use HH:MM format") from exc
    return value


def validate_number(value, field_name):
    if value == "":
        return value
    try:
        float(value)
    except ValueError as exc:
        raise SystemExit(f"{field_name} must be numeric") from exc
    return value


def check_header():
    with CSV_PATH.open("r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        header = next(reader, None)
    if header != HEADERS:
        raise SystemExit("data/health.csv has an invalid header. Run validate_data.py for details.")


def append_row(args):
    row = {
        "date": validate_date(args.date),
        "time": validate_time(args.time),
        "height_cm": validate_number(args.height_cm, "height_cm"),
        "weight_kg": validate_number(args.weight_kg, "weight_kg"),
        "body_fat_pct": validate_number(args.body_fat_pct, "body_fat_pct"),
        "fat_mass_kg": validate_number(args.fat_mass_kg, "fat_mass_kg"),
        "lean_mass_kg": validate_number(args.lean_mass_kg, "lean_mass_kg"),
        "hydration_pct": validate_number(args.hydration_pct, "hydration_pct"),
        "source": args.source,
        "notes": args.notes,
    }

    with CSV_PATH.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=HEADERS)
        writer.writerow(row)
    print("Logged health row.")


def parser():
    arg_parser = argparse.ArgumentParser(description="Append a row to data/health.csv")
    arg_parser.add_argument("--date", required=True)
    arg_parser.add_argument("--time", required=True)
    arg_parser.add_argument("--height-cm", default="")
    arg_parser.add_argument("--weight-kg", default="")
    arg_parser.add_argument("--body-fat-pct", default="")
    arg_parser.add_argument("--fat-mass-kg", default="")
    arg_parser.add_argument("--lean-mass-kg", default="")
    arg_parser.add_argument("--hydration-pct", default="")
    arg_parser.add_argument("--source", default="")
    arg_parser.add_argument("--notes", default="")
    return arg_parser


def main():
    args = parser().parse_args()
    require_file()
    check_header()
    append_row(args)


if __name__ == "__main__":
    main()
