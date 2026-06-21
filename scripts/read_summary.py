import csv
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
REPORT_PATH = ROOT / "reports" / "weekly_report.md"


def read_rows(filename):
    path = DATA_DIR / filename
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def number(value):
    if value == "":
        return None
    return float(value)


def average(values):
    clean_values = [value for value in values if value is not None]
    if not clean_values:
        return None
    return sum(clean_values) / len(clean_values)


def latest_value(rows, field):
    rows_with_value = [row for row in rows if row.get(field)]
    if not rows_with_value:
        return None
    rows_with_value.sort(key=lambda row: (row.get("date", ""), row.get("time", "")))
    return rows_with_value[-1][field]


def average_daily_calories(food_rows):
    calories_by_date = defaultdict(float)
    for row in food_rows:
        calories = number(row["calories"])
        if calories is not None:
            calories_by_date[row["date"]] += calories
    if not calories_by_date:
        return None
    return sum(calories_by_date.values()) / len(calories_by_date)


def recent_exercise(exercise_rows, today):
    start_date = today - timedelta(days=6)
    recent = []
    for row in exercise_rows:
        row_date = parse_date(row["date"])
        if start_date <= row_date <= today:
            recent.append(row)
    return recent


def format_value(value, suffix=""):
    if value is None:
        return "Not enough data yet"
    if isinstance(value, float):
        return f"{value:.2f}{suffix}"
    return f"{value}{suffix}"


def build_summary(today=None):
    today = today or date.today()
    health_rows = read_rows("health.csv")
    food_rows = read_rows("food.csv")
    exercise_rows = read_rows("exercise.csv")
    sleep_rows = read_rows("sleep.csv")

    recent = recent_exercise(exercise_rows, today)
    exercise_minutes = sum(number(row["duration_minutes"]) or 0 for row in recent)
    exercise_calorie_values = [
        number(row["estimated_calories_burned"])
        for row in recent
        if number(row["estimated_calories_burned"]) is not None
    ]
    exercise_calories = sum(exercise_calorie_values) if exercise_calorie_values else None

    summary = {
        "latest_weight": latest_value(health_rows, "weight_kg"),
        "latest_body_fat": latest_value(health_rows, "body_fat_pct"),
        "latest_hydration": latest_value(health_rows, "hydration_pct"),
        "average_daily_calories": average_daily_calories(food_rows),
        "exercise_sessions_7d": len(recent) if recent else None,
        "exercise_minutes_7d": exercise_minutes if recent else None,
        "exercise_calories_7d": exercise_calories,
        "average_sleep_duration": average(number(row["duration_hours"]) for row in sleep_rows),
        "average_sleep_quality": average(number(row["quality_1_10"]) for row in sleep_rows),
        "average_bathroom_visits": average(number(row["bathroom_visits"]) for row in sleep_rows),
    }
    return summary


def render_markdown(summary):
    lines = [
        "# Weekly Health Report",
        "",
        "This report describes recorded health tracking data only. It is not medical advice.",
        "",
        f"- Latest weight: {format_value(summary['latest_weight'], ' kg')}",
        f"- Latest body fat: {format_value(summary['latest_body_fat'], '%')}",
        f"- Latest hydration: {format_value(summary['latest_hydration'], '%')}",
        f"- Average daily calories: {format_value(summary['average_daily_calories'])}",
        f"- Exercise sessions in last 7 days: {format_value(summary['exercise_sessions_7d'])}",
        f"- Total exercise minutes in last 7 days: {format_value(summary['exercise_minutes_7d'])}",
        f"- Estimated calories burned in last 7 days: {format_value(summary['exercise_calories_7d'])}",
        f"- Average sleep duration: {format_value(summary['average_sleep_duration'], ' hours')}",
        f"- Average sleep quality: {format_value(summary['average_sleep_quality'], '/10')}",
        f"- Average bathroom visits per night: {format_value(summary['average_bathroom_visits'])}",
        "",
    ]
    return "\n".join(lines)


def main():
    summary = build_summary()
    markdown = render_markdown(summary)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(markdown, encoding="utf-8")

    print(markdown)
    print(f"Wrote {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
