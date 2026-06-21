# Dashboard Checks

Use these checks after meaningful dashboard changes.

## Required

```bash
python3 scripts/validate_data.py
python3 scripts/read_summary.py
python3 scripts/build_dashboard.py
```

## Localhost

If `scripts/serve_dashboard.py` is changed or live refresh is relevant:

```bash
python3 scripts/serve_dashboard.py --host 127.0.0.1 --port 8787
curl -s http://127.0.0.1:8787/ | head
curl -s http://127.0.0.1:8787/version
```

## Visual QA

When available, verify:

- desktop layout has no overlapping text
- mobile layout has no horizontal overflow
- food section shows item-level rows
- exercise section does not show raw JSON
- dashboard title and date are correct
- no console errors for the served page
