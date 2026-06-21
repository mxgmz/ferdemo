import argparse
import csv
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "food.csv"
NUTRITION_REFERENCE_PATH = ROOT / "data" / "nutrition_reference.csv"
HEADERS = [
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
]
MEAL_TYPES = {"breakfast", "lunch", "dinner", "snack", "other"}
ITEM_TYPES = {"food", "beverage"}
FDC_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"
DEFAULT_FDC_QUERIES = {
    "eggs": "egg whole cooked hard-boiled",
    "egg": "egg whole cooked hard-boiled",
    "huevos": "egg whole cooked hard-boiled",
    "beans": "beans cooked boiled",
    "frijoles": "beans cooked boiled",
    "coffee": "coffee brewed",
    "cafe": "coffee brewed",
    "café": "coffee brewed",
}


def require_file():
    if not CSV_PATH.exists():
        raise SystemExit("Missing data/food.csv. Run: python scripts/init_data.py")


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
        raise SystemExit("data/food.csv has an invalid header. Run validate_data.py for details.")


def normalize_query(item):
    return DEFAULT_FDC_QUERIES.get(item.strip().lower(), item)


def normalize_key(value):
    return value.strip().lower()


def reference_aliases(row):
    aliases = [row.get("item", "")]
    aliases.extend(row.get("aliases", "").split("|"))
    return {normalize_key(alias) for alias in aliases if alias.strip()}


def read_local_nutrition_reference():
    if not NUTRITION_REFERENCE_PATH.exists():
        return {}
    with NUTRITION_REFERENCE_PATH.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return {
            alias: row
            for row in reader
            for alias in reference_aliases(row)
        }


def estimate_calories_from_local_reference(item, quantity, unit):
    reference = read_local_nutrition_reference()
    row = reference.get(normalize_key(item))
    if not row:
        return None

    grams = quantity_to_grams(float(quantity), unit)
    kcal_per_100g = float(row["kcal_per_100g"])
    calories = grams * kcal_per_100g / 100
    source = row.get("source", "local nutrition reference")
    reference_food_name = row.get("reference_food_name", row["item"])
    return {
        "calories": f"{calories:.0f}",
        "calorie_source": f"local nutrition reference; source={source}; kcal_per_100g={kcal_per_100g:g}",
        "api_food_name": reference_food_name,
    }


def energy_kcal_from_food(food):
    for nutrient in food.get("foodNutrients", []):
        name = nutrient.get("nutrientName", "").lower()
        unit = nutrient.get("unitName", "").upper()
        value = nutrient.get("value")
        if name == "energy" and unit == "KCAL" and value is not None:
            return float(value)
    return None


def estimate_calories(item, quantity, unit, fdc_query=""):
    local_estimate = estimate_calories_from_local_reference(item, quantity, unit)
    if local_estimate:
        return local_estimate

    if os.environ.get("FER_ALLOW_USDA_API", "").lower() not in {"1", "true", "yes"}:
        raise SystemExit(
            f"No local nutrition reference found for item: {item}. "
            "Add it to data/nutrition_reference.csv or pass --fdc-query with FER_ALLOW_USDA_API=1."
        )

    api_key = os.environ.get("FDC_API_KEY", "DEMO_KEY")
    query = fdc_query or normalize_query(item)
    params = {
        "api_key": api_key,
        "query": query,
        "pageSize": 5,
    }
    url = FDC_SEARCH_URL + "?" + urllib.parse.urlencode(params)

    try:
        with urllib.request.urlopen(url, timeout=12) as response:
            data = json.load(response)
    except Exception as exc:
        raise SystemExit(f"Could not fetch calories from USDA FoodData Central: {exc}") from exc

    for food in data.get("foods", []):
        kcal_per_100g = energy_kcal_from_food(food)
        if kcal_per_100g is None:
            continue
        grams = quantity_to_grams(float(quantity), unit)
        calories = grams * kcal_per_100g / 100
        return {
            "calories": f"{calories:.0f}",
            "calorie_source": f"USDA FoodData Central; fdc_id={food.get('fdcId')}; query={query}",
            "api_food_name": food.get("description", ""),
        }

    raise SystemExit(f"No usable USDA calorie match found for item: {item}")


def quantity_to_grams(quantity, unit):
    normalized = unit.strip().lower()
    if normalized in {"g", "gram", "grams"}:
        return quantity
    if normalized in {"ml", "milliliter", "milliliters"}:
        # Approximation for water-like beverages. Use grams when precise density matters.
        return quantity
    raise SystemExit("unit must be g or ml for automatic calorie estimation")


def append_row(args):
    if args.meal_type not in MEAL_TYPES:
        allowed = ", ".join(sorted(MEAL_TYPES))
        raise SystemExit(f"meal_type must be one of: {allowed}")
    if args.item_type not in ITEM_TYPES:
        allowed = ", ".join(sorted(ITEM_TYPES))
        raise SystemExit(f"item_type must be one of: {allowed}")
    if not args.item:
        raise SystemExit("item is required")
    validate_number(args.quantity, "quantity")
    if not args.quantity:
        raise SystemExit("quantity is required")

    calories = validate_number(args.calories, "calories")
    calorie_source = args.calorie_source
    api_food_name = args.api_food_name
    if calories == "":
        estimate = estimate_calories(args.item, args.quantity, args.unit, args.fdc_query)
        calories = estimate["calories"]
        calorie_source = estimate["calorie_source"]
        api_food_name = estimate["api_food_name"]

    row = {
        "date": validate_date(args.date),
        "time": validate_time(args.time),
        "meal_type": args.meal_type,
        "item_type": args.item_type,
        "item": args.item,
        "quantity": args.quantity,
        "unit": args.unit,
        "calories": calories,
        "calorie_source": calorie_source,
        "api_food_name": api_food_name,
        "notes": args.notes,
    }

    with CSV_PATH.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=HEADERS)
        writer.writerow(row)
    print("Logged food row.")


def parser():
    arg_parser = argparse.ArgumentParser(description="Append an item-level row to data/food.csv")
    arg_parser.add_argument("--date", required=True)
    arg_parser.add_argument("--time", default="")
    arg_parser.add_argument("--meal-type", required=True)
    arg_parser.add_argument("--item-type", choices=sorted(ITEM_TYPES), default="food")
    arg_parser.add_argument("--item", required=True)
    arg_parser.add_argument("--quantity", required=True)
    arg_parser.add_argument("--unit", required=True)
    arg_parser.add_argument("--calories", default="")
    arg_parser.add_argument("--calorie-source", default="")
    arg_parser.add_argument("--api-food-name", default="")
    arg_parser.add_argument("--fdc-query", default="")
    arg_parser.add_argument("--notes", default="")
    return arg_parser


def main():
    args = parser().parse_args()
    require_file()
    check_header()
    append_row(args)


if __name__ == "__main__":
    main()
