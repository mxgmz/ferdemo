# AGENTS.md — Fer Health OS

## Purpose

This repository is a simple local health tracking system for Fer.

The source of truth is a set of CSV files inside `data/`. Python scripts inside `scripts/` are used to write, validate, and summarize the data.

This system is not a medical device and must not be used for diagnosis. It is only for personal tracking and basic trend observation.

## Core Rule

Do not manually edit CSV files during normal operation.

Use the logging scripts:

```bash
python scripts/log_health.py
python scripts/log_food.py
python scripts/log_exercise.py
python scripts/log_sleep.py
```

Manual CSV edits are allowed only to fix obvious data-entry mistakes. If you manually edit a CSV, run:

```bash
python scripts/validate_data.py
```

## Data Files

### `data/health.csv`

Tracks body measurements from a scale or manual entry.

Columns:

```csv
date,time,height_cm,weight_kg,body_fat_pct,fat_mass_kg,lean_mass_kg,hydration_pct,source,notes
```

Rules:

* `date`: YYYY-MM-DD
* `time`: HH:MM
* `height_cm`, `weight_kg`, `body_fat_pct`, `fat_mass_kg`, `lean_mass_kg`, `hydration_pct`: numeric when present
* `source`: scale, manual, estimated, or other
* Unknown values must be blank, never invented

### `data/food.csv`

Tracks meals, calories, and beverages.

Columns:

```csv
date,time,meal_type,item_type,item,quantity,unit,calories,calorie_source,api_food_name,notes
```

Rules:

* `meal_type`: breakfast, lunch, dinner, snack, or other
* `item_type`: food or beverage
* `item`: one specific food or drink per row
* `quantity`: numeric
* `unit`: g or ml for automatic calorie lookup
* `calories`: numeric when present
* `calorie_source`: where the calorie estimate came from
* `api_food_name`: matched reference/API food name
* Use `data/nutrition_reference.csv` through `scripts/log_food.py` for automatic offline calorie estimates
* USDA FoodData Central API lookup is optional and must be explicitly enabled with `FER_ALLOW_USDA_API=1`
* Do not invent calories manually when no local/API match exists

### `data/exercise.csv`

Tracks workouts and physical activity.

Columns:

```csv
date,time,exercise_type,metadata,duration_minutes,intensity,estimated_calories_burned,notes
```

Rules:

* `exercise_type`: running, gym, boxing, walking, cycling, swimming, mobility, or other
* `metadata`: valid JSON string
* `duration_minutes`: numeric
* `intensity`: low, medium, high, or very_high
* `estimated_calories_burned`: numeric when present
* Calorie burn is always an estimate, not a medical fact

Examples of metadata:

```json
{"sets": 4, "reps": 12, "weight_kg": 20}
```

```json
{"distance_km": 5.2, "pace_min_per_km": 6.1}
```

```json
{"sparring_minutes": 20, "rounds": 5}
```

### `data/sleep.csv`

Tracks sleep and bathroom visits.

Columns:

```csv
date,sleep_time,wake_time,duration_hours,quality_1_10,bathroom_visits,notes
```

Rules:

* `date`: date the person woke up
* `sleep_time`: HH:MM
* `wake_time`: HH:MM
* `duration_hours`: calculate when possible
* `quality_1_10`: integer from 1 to 10
* `bathroom_visits`: integer >= 0

## Standard Workflow

Before logging anything:

```bash
python scripts/init_data.py
```

After logging new data:

```bash
python scripts/validate_data.py
```

To generate a report:

```bash
python scripts/read_summary.py
```

The report is written to:

```txt
reports/weekly_report.md
```

To generate the local dashboard:

```bash
python scripts/build_dashboard.py
```

The dashboard is written to:

```txt
reports/dashboard.html
```

For an auto-refreshing local dashboard:

```bash
python3 scripts/serve_dashboard.py
```

Open:

```txt
http://127.0.0.1:8787/
```

The server watches `data/*.csv`, rebuilds `reports/dashboard.html`, and refreshes the browser automatically when data changes.

## Local Skills

Project-specific skills live inside:

```txt
skills/
```

These skills are local to Fer Health OS. Prefer them over global skills when working in this repository.

### `skills/fer-health-logger`

Use this local skill whenever the user gives a natural-language update that should become a Fer Health OS record.

Trigger examples:

* meals, snacks, drinks, ingredients, grams, milliliters, calories
* exercise, boxing, workouts, rounds, sparring, duration, intensity
* sleep time, wake time, sleep quality, bathroom visits
* weight, body fat, hydration, body measurements

Before logging those updates, read:

```txt
skills/fer-health-logger/SKILL.md
```

If the update includes food or beverages, also read:

```txt
skills/fer-health-logger/references/food_mappings.md
```

Then follow the skill workflow:

1. Convert the natural-language update into script calls.
2. Ask only when missing data blocks a correct record.
3. Use the logging scripts, not manual CSV edits.
4. Run `python3 scripts/validate_data.py`.
5. Run `python3 scripts/read_summary.py`.
6. Run `python3 scripts/build_dashboard.py`.
7. Briefly summarize what was logged and what was intentionally left blank.

### `skills/fer-food-calorie-operator`

Use this local skill whenever the task is specifically about food accuracy, calorie lookup, nutrition API matches, item-level meal structure, food mappings, Spanish food names, portion units, or auditing calories already recorded in `data/food.csv`.

Trigger examples:

* "separa cada comida por item"
* "calcula calorias con una API"
* "revisa si esas calorias estan bien"
* "USDA", "FoodData Central", "calorie_source", or `api_food_name`
* ambiguous preparation such as fried eggs, refried beans, coffee with milk, sauces, oil, butter, cheese, sugar

Before doing this work, read:

```txt
skills/fer-food-calorie-operator/SKILL.md
```

When choosing USDA queries, also read:

```txt
skills/fer-food-calorie-operator/references/usda_query_defaults.md
```

This skill is narrower than `fer-health-logger`: use it when food/calorie correctness is the main problem. For ordinary daily logging that includes food plus sleep/exercise, use `fer-health-logger` first and let it route food details through this skill if needed.

### `skills/fer-health-dashboard-operator`

Use this local skill whenever the task changes or verifies the dashboard, local server, report presentation, schema, CSV migration, or visual display of Fer Health OS.

Trigger examples:

* dashboard UI changes
* section/table/chart changes
* raw metadata should be shown differently
* schema changes or CSV column changes
* `build_dashboard.py`, `serve_dashboard.py`, `read_summary.py`, `validate_data.py`
* localhost auto-refresh behavior
* visual QA or mobile/desktop layout checks

Before doing this work, read:

```txt
skills/fer-health-dashboard-operator/SKILL.md
```

For verification checklists, read when relevant:

```txt
skills/fer-health-dashboard-operator/references/dashboard_checks.md
```

## Agent Behavior

When the user gives a natural-language update, convert it into the right script call.

Examples:

User says:

> Fer weighed 72.4 kg this morning, 18.2 body fat, 55.1 hydration.

Agent should call something like:

```bash
python scripts/log_health.py \
  --date YYYY-MM-DD \
  --time HH:MM \
  --weight-kg 72.4 \
  --body-fat-pct 18.2 \
  --hydration-pct 55.1 \
  --source scale \
  --notes "morning weigh-in"
```

User says:

> Breakfast was 200 grams of eggs, 100 grams of beans, and 250 ml coffee.

Agent should call one row per item:

```bash
python scripts/log_food.py \
  --date YYYY-MM-DD \
  --meal-type breakfast \
  --item-type food \
  --item eggs \
  --quantity 200 \
  --unit g
```

Then repeat for `beans` and `coffee`, using `--item-type beverage` for coffee.

User says:

> He boxed for one hour, high intensity, 20 minutes sparring, around 650 calories.

Agent should call:

```bash
python scripts/log_exercise.py \
  --date YYYY-MM-DD \
  --time HH:MM \
  --exercise-type boxing \
  --metadata '{"sparring_minutes":20}' \
  --duration-minutes 60 \
  --intensity high \
  --estimated-calories-burned 650 \
  --notes ""
```

## Do Not

* Do not diagnose.
* Do not give medical conclusions.
* Do not invent missing values.
* Do not overwrite CSV files.
* Do not change schemas without explicit instruction.
* Do not add a database.
* Do not add a web dashboard unless explicitly requested.
* Do not add dependencies unless explicitly requested.

## Allowed Improvements

The agent may suggest improvements, but must not implement them without approval.

Allowed future improvements:

* HTML dashboard
* Streamlit dashboard
* charts
* monthly reports
* data backup
* Apple Health / Google Fit import
* nutrition macro tracking
* medication/supplement tracking
* symptom tracking

## Definition of Done

A change is complete only when:

1. `python scripts/init_data.py` runs successfully.
2. Logging scripts can append valid rows.
3. `python scripts/validate_data.py` passes.
4. `python scripts/read_summary.py` generates `reports/weekly_report.md`.
5. Existing data is not overwritten.
