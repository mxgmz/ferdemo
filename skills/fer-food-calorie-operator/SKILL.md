---
name: fer-food-calorie-operator
description: Resolve Fer Health OS food items, quantities, preparations, and calorie estimates using local nutrition references. Use when logging meals, beverages, ingredients, portions, calories, local reference matches, ambiguous food preparation, Spanish food names, or when auditing whether food calories in /Users/maxgomez/Documents/Fer/fer-health-os are accurate enough.
---

# Fer Food Calorie Operator

Use this skill to turn food descriptions into item-level calorie records with traceable nutrition sources.

## Project

Work in:

```txt
/Users/maxgomez/Documents/Fer/fer-health-os
```

Food data lives in:

```txt
data/food.csv
```

## Workflow

1. Split meals into one row per food or beverage item.
2. Normalize item names from Spanish or casual phrasing.
3. Confirm each item has quantity and unit.
4. Prefer `data/nutrition_reference.csv`; read `references/usda_query_defaults.md` only when adding or auditing reference mappings.
5. Prefer plain preparation defaults unless the user specified oil, butter, cheese, sugar, milk, sauce, frying, brand, or restaurant.
6. Run `scripts/log_food.py` so calories come from `data/nutrition_reference.csv` and source fields are recorded. USDA API lookup is optional and should only be used when explicitly enabled.
7. Run validation and regenerate outputs:

```bash
python3 scripts/validate_data.py
python3 scripts/read_summary.py
python3 scripts/build_dashboard.py
```

## Clarify Before Logging

Ask one short question when:

- quantity is missing
- unit is missing
- preparation strongly changes calories
- the item is too ambiguous
- local reference/API returns a surprising match
- a beverage includes milk, sugar, creamer, protein powder, alcohol, or another caloric add-in

## Script Contract

Use:

```bash
python3 scripts/log_food.py \
  --date YYYY-MM-DD \
  --meal-type breakfast \
  --item-type food \
  --item eggs \
  --quantity 200 \
  --unit g
```

For drinks:

```bash
python3 scripts/log_food.py \
  --date YYYY-MM-DD \
  --meal-type breakfast \
  --item-type beverage \
  --item coffee \
  --quantity 250 \
  --unit ml
```

Do not manually write calories unless the user explicitly provides them or you are repairing a clear local-reference/API mismatch with user approval.

## Audit Rules

When reviewing existing food rows:

- Check that each row is one item, not a bundled meal.
- Check `calorie_source` and `api_food_name` are present when calories came from a local reference or API lookup.
- Flag weird matches, such as fried foods when the user only said a plain item.
- Prefer correcting through script calls or a deliberate CSV repair followed by validation.

## Never

- Never invent calories.
- Never silently accept a weird local-reference/API match.
- Never combine multiple foods into one row.
- Never overwrite existing food rows unless fixing a clear mistake.
- Never give medical or diet advice from calorie data.
