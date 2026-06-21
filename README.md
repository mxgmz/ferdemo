# fer-health-os

A very simple local health tracking system for Fer.

The system uses CSV files as the source of truth and small Python scripts for all normal writes. It has no database, API, dashboard, or external dependencies.

## Setup

```bash
python scripts/init_data.py
```

## Log Health

```bash
python scripts/log_health.py \
  --date 2026-06-21 \
  --time 08:00 \
  --height-cm 178 \
  --weight-kg 72.4 \
  --body-fat-pct 18.2 \
  --fat-mass-kg 13.2 \
  --lean-mass-kg 59.2 \
  --hydration-pct 55.1 \
  --source scale \
  --notes "morning weigh-in"
```

## Log Food

```bash
python scripts/log_food.py \
  --date 2026-06-21 \
  --meal-type breakfast \
  --item-type food \
  --item eggs \
  --quantity 200 \
  --unit g
```

Food rows are item-level. Drinks are logged as `--item-type beverage`. When calories are not passed, `log_food.py` estimates them from `data/nutrition_reference.csv` and records the source.

The normal flow is offline: `data/nutrition_reference.csv` stores kcal per 100 g plus a source note, so common foods can be logged without a USDA API key. If a food is missing from the local reference, add a sourced row there or opt into a one-off USDA API lookup with `FER_ALLOW_USDA_API=1`.

## Log Exercise

```bash
python scripts/log_exercise.py \
  --date 2026-06-21 \
  --time 18:00 \
  --exercise-type boxing \
  --metadata '{"sparring_minutes":20,"rounds":5}' \
  --duration-minutes 60 \
  --intensity high \
  --estimated-calories-burned 650 \
  --notes "boxing class"
```

## Log Sleep

```bash
python scripts/log_sleep.py \
  --date 2026-06-21 \
  --sleep-time 23:40 \
  --wake-time 07:15 \
  --quality-1-10 8 \
  --bathroom-visits 1 \
  --notes ""
```

## Validate And Summarize

```bash
python scripts/validate_data.py
python scripts/read_summary.py
python scripts/build_dashboard.py
```

`read_summary.py` prints a terminal summary and writes `reports/weekly_report.md`.

`build_dashboard.py` writes a local static dashboard to `reports/dashboard.html`.

## Live Dashboard

For an auto-refreshing local dashboard:

```bash
python3 scripts/serve_dashboard.py
```

Then open:

```txt
http://127.0.0.1:8787/
```

The live server watches `data/*.csv`, rebuilds `reports/dashboard.html`, and refreshes the browser automatically when data changes.

## Privacy And Safety

This project stores personal health data locally. It is for tracking and summaries only, not medical diagnosis or treatment advice.
