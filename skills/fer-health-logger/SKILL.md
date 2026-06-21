---
name: fer-health-logger
description: Log Fer Health OS updates from natural language into CSV-backed scripts. Use when Max gives health, food, exercise, sleep, weight, hydration, body-fat, meals, beverages, workouts, boxing, bathroom visits, or daily health updates that should be recorded in /Users/maxgomez/Documents/Fer/fer-health-os. Converts natural language into safe script calls, asks only for missing critical data, validates, regenerates reports, and relies on the local nutrition reference for food calories.
---

# Fer Health Logger

Use this skill to convert Max's natural-language health updates into Fer Health OS records.

## Project

Work in:

```txt
/Users/maxgomez/Documents/Fer/fer-health-os
```

CSV files are the source of truth, but do not edit them manually during normal logging. Use scripts.

## Core Workflow

1. Parse the user update into one or more record types:
   - food
   - exercise
   - sleep
   - health/body measurements
2. Do not invent missing values.
3. Ask a short question only when missing data blocks a correct record:
   - food item quantity is missing
   - sleep wake date is ambiguous
   - exercise duration is missing
   - body metric value is ambiguous
   - food preparation changes calories materially and no safe default exists
4. Log with the proper script.
5. Run validation:

```bash
python3 scripts/validate_data.py
```

6. Regenerate outputs:

```bash
python3 scripts/read_summary.py
python3 scripts/build_dashboard.py
```

7. Summarize what was logged, including any blanks left intentionally.

## Food

Log food one item per row.

Use:

```bash
python3 scripts/log_food.py
```

When calories are not provided, let `scripts/log_food.py` estimate them through `data/nutrition_reference.csv`. Do not estimate calories in prose and manually write them unless the user explicitly provides calories.

If the local reference has no match, do not invent calories. Add a sourced local reference row when appropriate, ask a clarifying question, or report the blocked item. USDA API lookup is optional and should only be used when explicitly enabled.

When the food phrase is ambiguous, read `references/food_mappings.md` before logging.

Example user update:

> desayune 200g de huevos, 100g de frijoles y cafe de 250ml

Log:

```bash
python3 scripts/log_food.py --date YYYY-MM-DD --meal-type breakfast --item-type food --item eggs --quantity 200 --unit g
python3 scripts/log_food.py --date YYYY-MM-DD --meal-type breakfast --item-type food --item beans --quantity 100 --unit g
python3 scripts/log_food.py --date YYYY-MM-DD --meal-type breakfast --item-type beverage --item coffee --quantity 250 --unit ml
```

## Exercise

Use:

```bash
python3 scripts/log_exercise.py
```

Keep `metadata` as JSON internally, but summarize it naturally to the user and rely on the dashboard to display human-readable details.

Example:

```bash
python3 scripts/log_exercise.py \
  --date YYYY-MM-DD \
  --exercise-type boxing \
  --metadata '{"sparring_minutes":20,"rounds":4}' \
  --duration-minutes 60 \
  --notes ""
```

If intensity or estimated calories are not provided, leave them blank.

## Sleep

Use:

```bash
python3 scripts/log_sleep.py
```

`date` is the date the person woke up.

If user says:

> me dormi ayer a las 12 y desperte hoy a las 8:15

Use:

```bash
python3 scripts/log_sleep.py \
  --date TODAY \
  --sleep-time 00:00 \
  --wake-time 08:15
```

Let the script calculate duration.

## Health

Use:

```bash
python3 scripts/log_health.py
```

Only log values explicitly provided. Unknown values stay blank.

## Safety

Do not diagnose.
Do not give medical conclusions.
Do not overwrite CSV files.
Do not change schemas while logging.
Do not add dashboard features while logging unless explicitly requested.

## Final Response

Keep the final response short:

- what was logged
- what was intentionally left blank
- validation result
- whether dashboard was regenerated
