import csv
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

SCHEMAS = {
    "health.csv": [
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
    ],
    "food.csv": [
        "date",
        "time",
        "meal_type",
        "item_type",
        "item",
        "quantity",
        "unit",
        "calories",
        "calorie_source",
        "api_food_name",
        "notes",
    ],
    "exercise.csv": [
        "date",
        "time",
        "exercise_type",
        "metadata",
        "duration_minutes",
        "intensity",
        "estimated_calories_burned",
        "notes",
    ],
    "sleep.csv": [
        "date",
        "sleep_time",
        "wake_time",
        "duration_hours",
        "quality_1_10",
        "bathroom_visits",
        "notes",
    ],
}

MEAL_TYPES = {"breakfast", "lunch", "dinner", "snack", "other"}
ITEM_TYPES = {"food", "beverage"}
INTENSITIES = {"low", "medium", "high", "very_high"}


def is_date(value):
    datetime.strptime(value, "%Y-%m-%d")


def is_time(value):
    datetime.strptime(value, "%H:%M")


def is_number(value):
    if value:
        float(value)


def is_int(value):
    if value:
        int(value)


def add_error(errors, filename, row_number, message):
    location = f"{filename} row {row_number}" if row_number else filename
    errors.append(f"{location}: {message}")


def validate_health(row, filename, row_number, errors):
    is_date(row["date"])
    is_time(row["time"])
    for field in [
        "height_cm",
        "weight_kg",
        "body_fat_pct",
        "fat_mass_kg",
        "lean_mass_kg",
        "hydration_pct",
    ]:
        is_number(row[field])


def validate_food(row, filename, row_number, errors):
    is_date(row["date"])
    if row["time"]:
        is_time(row["time"])
    if row["meal_type"] not in MEAL_TYPES:
        add_error(errors, filename, row_number, "meal_type is invalid")
    if row["item_type"] not in ITEM_TYPES:
        add_error(errors, filename, row_number, "item_type is invalid")
    if not row["item"]:
        add_error(errors, filename, row_number, "item is required")
    is_number(row["quantity"])
    if not row["quantity"]:
        add_error(errors, filename, row_number, "quantity is required")
    if not row["unit"]:
        add_error(errors, filename, row_number, "unit is required")
    is_number(row["calories"])


def validate_exercise(row, filename, row_number, errors):
    is_date(row["date"])
    if row["time"]:
        is_time(row["time"])
    json.loads(row["metadata"])
    is_number(row["duration_minutes"])
    if not row["duration_minutes"]:
        add_error(errors, filename, row_number, "duration_minutes is required")
    if row["intensity"] and row["intensity"] not in INTENSITIES:
        add_error(errors, filename, row_number, "intensity is invalid")
    is_number(row["estimated_calories_burned"])


def validate_sleep(row, filename, row_number, errors):
    is_date(row["date"])
    if row["sleep_time"]:
        is_time(row["sleep_time"])
    if row["wake_time"]:
        is_time(row["wake_time"])
    is_number(row["duration_hours"])
    is_int(row["quality_1_10"])
    is_int(row["bathroom_visits"])
    if row["quality_1_10"]:
        quality = int(row["quality_1_10"])
        if quality < 1 or quality > 10:
            add_error(errors, filename, row_number, "quality_1_10 must be from 1 to 10")
    if row["bathroom_visits"] and int(row["bathroom_visits"]) < 0:
        add_error(errors, filename, row_number, "bathroom_visits must be >= 0")


VALIDATORS = {
    "health.csv": validate_health,
    "food.csv": validate_food,
    "exercise.csv": validate_exercise,
    "sleep.csv": validate_sleep,
}


def validate_file(filename, errors):
    path = DATA_DIR / filename
    if not path.exists():
        add_error(errors, filename, None, "file is missing")
        return

    with path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != SCHEMAS[filename]:
            add_error(errors, filename, None, "header does not match expected schema")
            return

        for row_number, row in enumerate(reader, start=2):
            try:
                VALIDATORS[filename](row, filename, row_number, errors)
            except (ValueError, json.JSONDecodeError) as exc:
                add_error(errors, filename, row_number, str(exc))


def main():
    errors = []
    print("Validation report")
    print("=================")

    for filename in SCHEMAS:
        validate_file(filename, errors)

    if errors:
        print("Status: INVALID")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("Status: VALID")
    for filename in SCHEMAS:
        print(f"- data/{filename}: ok")


if __name__ == "__main__":
    main()
