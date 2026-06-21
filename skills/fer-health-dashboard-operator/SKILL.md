---
name: fer-health-dashboard-operator
description: Maintain, update, and verify the Fer Health OS local dashboard, reports, CSV schemas, and localhost live-refresh flow. Use when changing /Users/maxgomez/Documents/Fer/fer-health-os dashboard UI, build_dashboard.py, serve_dashboard.py, reports, schema.json, CSV schemas, migrations, charts, tables, or visual presentation of food, exercise, sleep, and health data.
---

# Fer Health Dashboard Operator

Use this skill when changing how Fer Health OS data is displayed, summarized, served, or migrated.

## Project

Work in:

```txt
/Users/maxgomez/Documents/Fer/fer-health-os
```

Primary files:

```txt
scripts/build_dashboard.py
scripts/serve_dashboard.py
scripts/read_summary.py
scripts/validate_data.py
config/schema.json
reports/dashboard.html
reports/weekly_report.md
data/*.csv
```

## Workflow

1. Read `AGENTS.md`.
2. Identify whether the request is:
   - UI display change
   - schema/data model change
   - summary/report change
   - live server/auto-refresh change
   - data migration or repair
3. Keep CSV files as source of truth.
4. Do not add a database or dependency unless Max explicitly approves it.
5. If schema changes, update all matching files:
   - `config/schema.json`
   - `scripts/init_data.py`
   - `scripts/validate_data.py`
   - relevant logging scripts
   - `scripts/read_summary.py`
   - `scripts/build_dashboard.py`
   - `AGENTS.md`
6. Preserve existing data. If migration is needed, explain it and keep it narrow.
7. Run validation and regenerate outputs:

```bash
python3 scripts/validate_data.py
python3 scripts/read_summary.py
python3 scripts/build_dashboard.py
```

8. If localhost is involved, verify:

```txt
http://127.0.0.1:8787/
```

## Dashboard UI Rules

- Use the registered `Health Studio` style from Max's dashboard style registry.
- Keep the dashboard operational and scannable, not a landing page.
- Show food item rows with item, quantity, unit, calories, API source, and notes.
- Show exercise metadata as human-readable details, not raw JSON.
- Keep sleep simple unless Max asks for deeper analysis.
- Avoid diagnosis, medical conclusions, and diet advice.
- Validate mobile layout when UI changes materially.

## Live Refresh Rules

`scripts/serve_dashboard.py` should:

- serve the dashboard at `http://127.0.0.1:8787/`
- watch `data/*.csv`
- rebuild `reports/dashboard.html`
- refresh the browser automatically through SSE or polling fallback

Do not leave temporary servers running except the intended Fer Health OS dashboard server.

## Data Migration Rules

Manual CSV edits are allowed only for migrations or obvious repair.

When manually editing CSVs:

1. Keep headers exact.
2. Preserve all valid user data.
3. Run `python3 scripts/validate_data.py`.
4. Regenerate report and dashboard.
5. Tell Max exactly what changed.

## Final Response

Briefly report:

- files changed
- validation result
- dashboard/report regeneration result
- any remaining caveat
