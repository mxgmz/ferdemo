import argparse
import csv
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "sleep.csv"
HEADERS = [
    "date",
    "sleep_time",
    "wake_time",
    "duration_hours",
    "quality_1_10",
    "bathroom_visits",
    "notes",
]


def require_file():
    if not CSV_PATH.exists():
        raise SystemExit("Missing data/sleep.csv. Run: python scripts/init_data.py")


def validate_date(value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise SystemExit("date must use YYYY-MM-DD format") from exc
    return value


def validate_time(value, field_name):
    if value == "":
        return value
    try:
        datetime.strptime(value, "%H:%M")
    except ValueError as exc:
        raise SystemExit(f"{field_name} must use HH:MM format") from exc
    return value


def validate_duration(value):
    if value == "":
        return value
    try:
        duration = float(value)
    except ValueError as exc:
        raise SystemExit("duration_hours must be numeric") from exc
    if duration < 0:
        raise SystemExit("duration_hours must be >= 0")
    return value


def validate_quality(value):
    if value == "":
        return value
    try:
        quality = int(value)
    except ValueError as exc:
        raise SystemExit("quality_1_10 must be an integer") from exc
    if quality < 1 or quality > 10:
        raise SystemExit("quality_1_10 must be from 1 to 10")
    return value


def validate_bathroom_visits(value):
    if value == "":
        return value
    try:
        visits = int(value)
    except ValueError as exc:
        raise SystemExit("bathroom_visits must be an integer") from exc
    if visits < 0:
        raise SystemExit("bathroom_visits must be >= 0")
    return value


def calculate_duration(sleep_time, wake_time):
    if not sleep_time or not wake_time:
        return ""
    sleep_dt = datetime.strptime(sleep_time, "%H:%M")
    wake_dt = datetime.strptime(wake_time, "%H:%M")
    if wake_dt < sleep_dt:
        wake_dt += timedelta(days=1)
    hours = (wake_dt - sleep_dt).total_seconds() / 3600
    return f"{hours:.2f}"


def check_header():
    with CSV_PATH.open("r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        header = next(reader, None)
    if header != HEADERS:
        raise SystemExit("data/sleep.csv has an invalid header. Run validate_data.py for details.")


def append_row(args):
    duration = args.duration_hours
    if duration == "":
        duration = calculate_duration(args.sleep_time, args.wake_time)

    row = {
        "date": validate_date(args.date),
        "sleep_time": validate_time(args.sleep_time, "sleep_time"),
        "wake_time": validate_time(args.wake_time, "wake_time"),
        "duration_hours": validate_duration(duration),
        "quality_1_10": validate_quality(args.quality_1_10),
        "bathroom_visits": validate_bathroom_visits(args.bathroom_visits),
        "notes": args.notes,
    }

    with CSV_PATH.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=HEADERS)
        writer.writerow(row)
    print("Logged sleep row.")


def parser():
    arg_parser = argparse.ArgumentParser(description="Append a row to data/sleep.csv")
    arg_parser.add_argument("--date", required=True)
    arg_parser.add_argument("--sleep-time", default="")
    arg_parser.add_argument("--wake-time", default="")
    arg_parser.add_argument("--duration-hours", default="")
    arg_parser.add_argument("--quality-1-10", default="")
    arg_parser.add_argument("--bathroom-visits", default="")
    arg_parser.add_argument("--notes", default="")
    return arg_parser


def main():
    args = parser().parse_args()
    require_file()
    check_header()
    append_row(args)


if __name__ == "__main__":
    main()
