import argparse
import csv
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "exercise.csv"
HEADERS = [
    "date",
    "time",
    "exercise_type",
    "metadata",
    "duration_minutes",
    "intensity",
    "estimated_calories_burned",
    "notes",
]
INTENSITIES = {"low", "medium", "high", "very_high"}


def require_file():
    if not CSV_PATH.exists():
        raise SystemExit("Missing data/exercise.csv. Run: python scripts/init_data.py")


def validate_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise SystemExit("date must use YYYY-MM-DD format") from exc
    return value


def validate_time(value):
    if value == "":
        return value
    try:
        datetime.strptime(value, "%H:%M")
    except ValueError as exc:
        raise SystemExit("time must use HH:MM format") from exc
    return value


def validate_number(value, field_name, required=False):
    if value == "" and not required:
        return value
    try:
        float(value)
    except ValueError as exc:
        raise SystemExit(f"{field_name} must be numeric") from exc
    return value


def validate_json(value):
    try:
        json.loads(value)
    except json.JSONDecodeError as exc:
        raise SystemExit("metadata must be a valid JSON string") from exc
    return value


def check_header():
    with CSV_PATH.open("r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        header = next(reader, None)
    if header != HEADERS:
        raise SystemExit("data/exercise.csv has an invalid header. Run validate_data.py for details.")


def append_row(args):
    if args.intensity and args.intensity not in INTENSITIES:
        allowed = ", ".join(sorted(INTENSITIES))
        raise SystemExit(f"intensity must be one of: {allowed}")

    row = {
        "date": validate_date(args.date),
        "time": validate_time(args.time),
        "exercise_type": args.exercise_type,
        "metadata": validate_json(args.metadata),
        "duration_minutes": validate_number(args.duration_minutes, "duration_minutes", required=True),
        "intensity": args.intensity,
        "estimated_calories_burned": validate_number(
            args.estimated_calories_burned,
            "estimated_calories_burned",
        ),
        "notes": args.notes,
    }

    with CSV_PATH.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=HEADERS)
        writer.writerow(row)
    print("Logged exercise row.")


def parser():
    arg_parser = argparse.ArgumentParser(description="Append a row to data/exercise.csv")
    arg_parser.add_argument("--date", required=True)
    arg_parser.add_argument("--time", default="")
    arg_parser.add_argument("--exercise-type", required=True)
    arg_parser.add_argument("--metadata", required=True)
    arg_parser.add_argument("--duration-minutes", required=True)
    arg_parser.add_argument("--intensity", default="")
    arg_parser.add_argument("--estimated-calories-burned", default="")
    arg_parser.add_argument("--notes", default="")
    return arg_parser


def main():
    args = parser().parse_args()
    require_file()
    check_header()
    append_row(args)


if __name__ == "__main__":
    main()
