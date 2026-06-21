import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"
CONFIG_DIR = ROOT / "config"

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

NUTRITION_REFERENCE_HEADERS = [
    "item",
    "aliases",
    "kcal_per_100g",
    "reference_food_name",
    "source",
    "notes",
]


def ensure_csv(path, headers):
    if path.exists():
        return False

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
    return True


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    created = []
    for filename, headers in SCHEMAS.items():
        if ensure_csv(DATA_DIR / filename, headers):
            created.append(filename)

    if ensure_csv(DATA_DIR / "nutrition_reference.csv", NUTRITION_REFERENCE_HEADERS):
        created.append("nutrition_reference.csv")

    if created:
        print("Created CSV files:")
        for filename in created:
            print(f"- data/{filename}")
    else:
        print("All CSV files already exist. No data overwritten.")


if __name__ == "__main__":
    main()
