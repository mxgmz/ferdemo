import csv
import html
import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
REPORT_PATH = ROOT / "reports" / "dashboard.html"


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
    try:
        return float(value)
    except ValueError:
        return None


def safe(value):
    return html.escape(str(value or ""))


def fmt(value, suffix="", empty="Sin datos"):
    if value is None or value == "":
        return empty
    if isinstance(value, float):
        return f"{value:.1f}{suffix}"
    return f"{value}{suffix}"


def latest(rows, field):
    with_value = [row for row in rows if row.get(field)]
    if not with_value:
        return None
    with_value.sort(key=lambda row: (row.get("date", ""), row.get("time", "")))
    return with_value[-1]


def rows_for_date(rows, target_date):
    target = target_date.isoformat()
    return [row for row in rows if row.get("date") == target]


def group_by_date(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row.get("date", "")].append(row)
    return dict(sorted(grouped.items(), reverse=True))


def daily_sum(rows, field):
    totals = defaultdict(float)
    for row in rows:
        value = number(row.get(field, ""))
        if value is not None:
            totals[row["date"]] += value
    return dict(sorted(totals.items()))


def daily_average(rows, field):
    values = defaultdict(list)
    for row in rows:
        value = number(row.get(field, ""))
        if value is not None:
            values[row["date"]].append(value)
    return {day: sum(day_values) / len(day_values) for day, day_values in sorted(values.items())}


def last_n_points(mapping, count=14):
    items = sorted(mapping.items())[-count:]
    return [(label, value) for label, value in items]


def line_chart(points, color="#477a4e"):
    if not points:
        return '<div class="empty-chart">Sin datos suficientes</div>'
    width = 320
    height = 120
    padding = 16
    values = [value for _, value in points]
    low = min(values)
    high = max(values)
    span = high - low or 1
    x_step = (width - padding * 2) / max(len(points) - 1, 1)
    coords = []
    for index, (_, value) in enumerate(points):
        x = padding + index * x_step
        y = height - padding - ((value - low) / span) * (height - padding * 2)
        coords.append((x, y))
    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in coords)
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" />' for x, y in coords)
    return (
        f'<svg class="chart" viewBox="0 0 {width} {height}" role="img">'
        f'<polyline points="{polyline}" fill="none" stroke="{color}" stroke-width="3" />'
        f'<g fill="{color}">{dots}</g>'
        "</svg>"
    )


def bar_chart(points, color="#477a4e"):
    if not points:
        return '<div class="empty-chart">Sin datos suficientes</div>'
    width = 320
    height = 120
    padding = 16
    max_value = max(value for _, value in points) or 1
    gap = 6
    bar_width = (width - padding * 2 - gap * (len(points) - 1)) / len(points)
    bars = []
    for index, (_, value) in enumerate(points):
        bar_height = max(4, (value / max_value) * (height - padding * 2))
        x = padding + index * (bar_width + gap)
        y = height - padding - bar_height
        bars.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" rx="4" />')
    return f'<svg class="chart" viewBox="0 0 {width} {height}" role="img"><g fill="{color}">{"".join(bars)}</g></svg>'


def progress_card(label, value, max_value, axis_mid, axis_max):
    fill = 0
    if value is not None and max_value:
        fill = max(0, min(100, (value / max_value) * 100))
    return (
        '<article class="card metric-card">'
        f'<h3>{safe(label)}</h3>'
        '<div class="calorie-chart">'
        '<div class="bar-track">'
        f'<div class="bar-fill" style="width:{fill:.0f}%"></div>'
        '</div>'
        '<div class="axis">'
        '<span>0</span>'
        f'<span>{safe(axis_mid)}</span>'
        f'<span>{safe(axis_max)}</span>'
        '</div>'
        '</div>'
        '</article>'
    )


def stat_card(label, value, hint="", icon=""):
    ghost = ""
    if icon:
        ghost = f'<div class="ghost-icon" aria-hidden="true">{icon}</div>'
    return (
        '<article class="card metric-card">'
        f'<h3>{safe(label)}</h3>'
        f'<div class="big-number">{safe(value)}</div>'
        f'<div class="metric-label">{safe(hint)}</div>'
        f"{ghost}"
        "</article>"
    )


def tag_class(value):
    normalized = (value or "").strip().lower()
    if normalized == "breakfast":
        return "tag tag-breakfast"
    if normalized in {"lunch", "dinner", "snack", "other"}:
        return "tag tag-meal"
    if normalized == "beverage":
        return "tag tag-beverage"
    if normalized == "food":
        return "tag tag-food"
    if normalized in {"high", "very_high"}:
        return "tag tag-breakfast"
    if normalized in {"medium", "low"}:
        return "tag tag-meal"
    return "tag"


def table_cell(key, value):
    if key in {"meal_type", "item_type", "intensity"} and value:
        return f'<span class="{tag_class(value)}">{safe(value)}</span>'
    if key in {"quantity", "calories", "estimated_calories_burned", "duration_minutes", "duration_hours", "quality_1_10", "bathroom_visits", "weight_kg", "body_fat_pct", "hydration_pct"}:
        return f'<span class="num">{safe(value)}</span>'
    if key in {"api_food_name", "notes", "details"}:
        return f'<span class="notes">{safe(value)}</span>'
    if value == "":
        return '<span class="muted">-</span>'
    return safe(value)


def table(headers, rows, extra_class=""):
    if not rows:
        return '<div class="empty-state">Sin registros para mostrar.</div>'
    head = "".join(f'<th class="{safe(column_class(key))}">{safe(label)}</th>' for key, label in headers)
    body_rows = []
    for row in rows:
        cells = "".join(f"<td>{table_cell(key, row.get(key, ''))}</td>" for key, _ in headers)
        body_rows.append(f"<tr>{cells}</tr>")
    return f'<div class="table-scroll {safe(extra_class)}"><table><thead><tr>{head}</tr></thead><tbody>{"".join(body_rows)}</tbody></table></div>'


def column_class(key):
    classes = {
        "time": "col-time",
        "meal_type": "col-type",
        "item_type": "col-class",
        "item": "col-item",
        "quantity": "col-qty",
        "unit": "col-unit",
        "calories": "col-cal",
        "api_food_name": "col-source",
        "notes": "col-notes",
    }
    return classes.get(key, "")


def humanize_metadata(value):
    if not value:
        return ""
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return value
    labels = {
        "sparring_minutes": "sparring min",
        "rounds": "rounds",
        "sets": "sets",
        "reps": "reps",
        "weight_kg": "kg",
        "distance_km": "km",
        "pace_min_per_km": "pace",
    }
    parts = []
    for key, item in data.items():
        label = labels.get(key, key.replace("_", " "))
        parts.append(f"{label}: {item}")
    return ", ".join(parts)


def exercise_table(headers, rows):
    display_rows = []
    for row in rows:
        display_row = dict(row)
        display_row["details"] = humanize_metadata(row.get("metadata", ""))
        display_rows.append(display_row)
    return table(headers, display_rows)


def day_blocks(grouped, renderer):
    if not grouped:
        return '<div class="empty-state">Todavia no hay registros.</div>'
    blocks = []
    for day, rows in grouped.items():
        blocks.append(
            '<section class="card table-card day-block">'
            '<div class="table-header">'
            f'<h3>{safe(day)}</h3>'
            f'<span class="count-pill">{len(rows)} registros</span>'
            '</div>'
            f"{renderer(rows)}"
            "</section>"
        )
    return "".join(blocks)


def nav_icon(name):
    icons = {
        "home": '<path d="M4 10.5 12 4l8 6.5V20a1 1 0 0 1-1 1h-5v-6h-4v6H5a1 1 0 0 1-1-1v-9.5Z" stroke="currentColor" stroke-linejoin="round" />',
        "health": '<path d="M20.2 5.8a5.2 5.2 0 0 0-7.4 0L12 6.6l-.8-.8a5.2 5.2 0 0 0-7.4 7.4L12 21l8.2-7.8a5.2 5.2 0 0 0 0-7.4Z" stroke="currentColor" stroke-linejoin="round" />',
        "food": '<path d="M7 3v8M4 3v8M10 3v8M4 11h6M7 11v10M17 3v18M17 3c2.2 2.2 3 4.4 3 7 0 2-1.1 3-3 3" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" />',
        "exercise": '<path d="M6.5 7.5h11M8 5v5M16 5v5M4 9v3M20 9v3M9 15l3-2 3 2M12 13v7" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" />',
        "sleep": '<path d="M20 15.2A8.2 8.2 0 0 1 8.8 4a7.6 7.6 0 1 0 11.2 11.2Z" stroke="currentColor" stroke-linejoin="round" />',
        "doc": '<path d="M9 5h6M9 9h6M9 13h4M7 3h10a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />',
    }
    return f'<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">{icons[name]}</svg>'


def plant_svg():
    return """
      <svg class="plant" viewBox="0 0 160 160" fill="none" aria-hidden="true">
        <path d="M82 132V75" stroke="#9CAF88" stroke-width="4" stroke-linecap="round" />
        <path d="M82 96C57 96 41 77 38 46c28 2 47 18 44 50Z" fill="#D9E5C8" />
        <path d="M88 85c29-7 45-25 48-55-27 1-49 21-48 55Z" fill="#B9C9A3" />
        <path d="M74 115c-23-4-39-20-48-48 29 2 47 18 48 48Z" fill="#C8D7B5" />
        <path d="M86 117c23-5 38-20 45-46-27 3-44 19-45 46Z" fill="#E0E8D3" />
        <ellipse cx="82" cy="139" rx="46" ry="8" fill="#EAEFE2" />
      </svg>
    """


def build_context():
    today = date.today()
    health_rows = read_rows("health.csv")
    food_rows = read_rows("food.csv")
    exercise_rows = read_rows("exercise.csv")
    sleep_rows = read_rows("sleep.csv")
    latest_health = latest(health_rows, "weight_kg") or {}
    today_food = rows_for_date(food_rows, today)
    today_exercise = rows_for_date(exercise_rows, today)
    today_sleep = rows_for_date(sleep_rows, today)
    yesterday = today - timedelta(days=1)

    calories_today = sum(number(row.get("calories", "")) or 0 for row in today_food)
    minutes_today = sum(number(row.get("duration_minutes", "")) or 0 for row in today_exercise)

    return {
        "today": today,
        "yesterday": yesterday,
        "health_rows": health_rows,
        "food_rows": food_rows,
        "exercise_rows": exercise_rows,
        "sleep_rows": sleep_rows,
        "latest_health": latest_health,
        "today_food": today_food,
        "today_exercise": today_exercise,
        "today_sleep": today_sleep,
        "calories_today": calories_today if today_food else None,
        "minutes_today": minutes_today if today_exercise else None,
    }


def render_dashboard(context):
    today = context["today"]
    health_rows = context["health_rows"]
    food_rows = context["food_rows"]
    exercise_rows = context["exercise_rows"]
    sleep_rows = context["sleep_rows"]
    latest_health = context["latest_health"]

    weight_points = last_n_points({row["date"]: number(row["weight_kg"]) for row in health_rows if number(row.get("weight_kg", "")) is not None})
    fat_points = last_n_points({row["date"]: number(row["body_fat_pct"]) for row in health_rows if number(row.get("body_fat_pct", "")) is not None})
    calorie_points = last_n_points(daily_sum(food_rows, "calories"))
    exercise_points = last_n_points(daily_sum(exercise_rows, "duration_minutes"))
    sleep_points = last_n_points(daily_average(sleep_rows, "duration_hours"))
    quality_points = last_n_points(daily_average(sleep_rows, "quality_1_10"))

    food_headers = [
        ("time", "Hora"),
        ("meal_type", "Tipo"),
        ("item_type", "Clase"),
        ("item", "Item"),
        ("quantity", "Cantidad"),
        ("unit", "Unidad"),
        ("calories", "Calorias"),
        ("api_food_name", "Referencia"),
        ("notes", "Notas"),
    ]
    health_headers = [
        ("date", "Fecha"),
        ("time", "Hora"),
        ("weight_kg", "Peso"),
        ("body_fat_pct", "Grasa"),
        ("hydration_pct", "Hidratacion"),
        ("source", "Fuente"),
        ("notes", "Notas"),
    ]
    exercise_headers = [
        ("time", "Hora"),
        ("exercise_type", "Tipo"),
        ("duration_minutes", "Min"),
        ("intensity", "Intensidad"),
        ("estimated_calories_burned", "Calorias"),
        ("details", "Detalles"),
        ("notes", "Notas"),
    ]
    sleep_headers = [
        ("date", "Fecha"),
        ("sleep_time", "Dormir"),
        ("wake_time", "Despertar"),
        ("duration_hours", "Horas"),
        ("quality_1_10", "Calidad"),
        ("bathroom_visits", "Bano"),
        ("notes", "Notas"),
    ]

    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    payload = {
        "generated": generated,
        "version": datetime.now().isoformat(timespec="microseconds"),
        "today": today.isoformat(),
        "style": "Botanical Ledger Light",
    }

    today_sleep_hours = None
    if context["today_sleep"]:
        today_sleep_hours = number(context["today_sleep"][-1].get("duration_hours", ""))

    return f"""<!doctype html>
<html lang="es" data-version="{safe(payload["version"])}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='10' fill='%23edf4e8'/%3E%3Cpath d='M23.2 7.1C19.5 6.8 16.4 7.9 14 10.2c-2.4 2.2-3.6 5.4-3.5 9.6 5.3-.1 9-1.6 11-4.4 1.6-2 2.1-4.8 1.7-8.3Z' fill='none' stroke='%23315b38' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/%3E%3Cpath d='M7 25c2.7-6.4 7-10.7 13.2-12.8' fill='none' stroke='%23315b38' stroke-width='2' stroke-linecap='round'/%3E%3C/svg%3E">
  <title>Fer Health OS Dashboard</title>
  <style>
    :root {{
      --bg: #f7f8f4;
      --bg-soft: #fbfbf8;
      --sidebar: #fafbf7;
      --card: #ffffff;
      --card-soft: #f9faf6;
      --text: #17201b;
      --text-muted: #68736b;
      --text-soft: #8a928b;
      --border: #e3e8df;
      --border-strong: #d4ddcf;
      --shadow-sm: 0 4px 14px rgba(24, 38, 29, 0.06);
      --shadow-md: 0 16px 40px rgba(24, 38, 29, 0.08);
      --accent: #477a4e;
      --accent-dark: #315b38;
      --accent-soft: #edf4e8;
      --accent-soft-2: #f4f8ef;
      --blue-soft: #eef5f7;
      --blue: #416c7a;
      --orange-soft: #fbf2e8;
      --orange: #976735;
      --radius-sm: 10px;
      --radius-md: 16px;
      --radius-lg: 22px;
      --sidebar-w: 272px;
      --content-max: 1180px;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      background:
        radial-gradient(circle at 70% 0%, rgba(82, 117, 84, 0.08), transparent 30%),
        linear-gradient(180deg, var(--bg-soft), var(--bg));
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 15px;
      line-height: 1.45;
    }}
    button, input {{ font: inherit; }}
    .app-shell {{
      min-height: 100vh;
      display: grid;
      grid-template-columns: var(--sidebar-w) minmax(0, 1fr);
    }}
    .sidebar {{
      position: sticky;
      top: 0;
      height: 100vh;
      padding: 30px 20px;
      border-right: 1px solid var(--border);
      background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.76), rgba(250, 251, 247, 0.92)),
        var(--sidebar);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}
    .brand {{
      display: flex;
      gap: 13px;
      align-items: flex-start;
      margin-bottom: 54px;
    }}
    .brand-mark {{
      width: 36px;
      height: 36px;
      border-radius: 12px;
      background: var(--accent-soft);
      display: grid;
      place-items: center;
      color: var(--accent-dark);
      flex: 0 0 auto;
    }}
    .brand-mark svg {{ width: 22px; height: 22px; }}
    .brand h1 {{
      margin: 0;
      font-size: 19px;
      line-height: 1.15;
      letter-spacing: -0.03em;
      font-weight: 760;
    }}
    .brand p {{
      margin: 7px 0 0;
      color: var(--text-muted);
      font-size: 13px;
    }}
    .nav {{
      display: grid;
      gap: 10px;
    }}
    .nav-item {{
      min-height: 52px;
      padding: 0 16px;
      border-radius: 14px;
      display: flex;
      align-items: center;
      gap: 13px;
      color: var(--text-muted);
      background: transparent;
      font-weight: 600;
      position: relative;
      border: 1px solid transparent;
      cursor: pointer;
      text-align: left;
    }}
    .nav-item svg {{
      width: 21px;
      height: 21px;
      stroke-width: 1.9;
      flex: 0 0 auto;
    }}
    .nav-item.active {{
      color: var(--accent-dark);
      background: linear-gradient(90deg, var(--accent-soft), rgba(255, 255, 255, 0.88));
      border-color: var(--border-strong);
      box-shadow: var(--shadow-sm);
    }}
    .nav-item.active::before {{
      content: "";
      position: absolute;
      left: -1px;
      top: 10px;
      width: 4px;
      height: 32px;
      border-radius: 10px;
      background: var(--accent);
    }}
    .nav-item:hover, .nav-item:focus-visible {{
      color: var(--accent-dark);
      border-color: var(--border-strong);
      outline: none;
    }}
    .sidebar-footer {{
      padding: 16px;
      border: 1px solid var(--border);
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.65);
      color: var(--text-muted);
      font-size: 12px;
      box-shadow: var(--shadow-sm);
    }}
    .sidebar-footer strong {{
      display: block;
      color: var(--text);
      font-size: 13px;
      margin-bottom: 3px;
    }}
    .plant {{
      width: 118px;
      height: 118px;
      margin: 0 auto 22px;
      opacity: 0.82;
      display: block;
    }}
    main {{ padding: 34px 44px 48px; min-width: 0; }}
    .content {{ max-width: var(--content-max); margin: 0 auto; }}
    .topbar {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 28px;
      margin-bottom: 34px;
    }}
    .headline h2 {{
      margin: 0;
      font-size: clamp(32px, 4vw, 44px);
      line-height: 1.05;
      letter-spacing: -0.055em;
      font-weight: 820;
    }}
    .headline p {{
      margin: 10px 0 0;
      color: var(--text-muted);
      font-size: 14px;
    }}
    .status-pill {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      white-space: nowrap;
      border: 1px solid var(--border);
      background: var(--accent-soft-2);
      color: var(--accent-dark);
      border-radius: 999px;
      padding: 9px 13px;
      font-weight: 650;
      font-size: 13px;
      box-shadow: var(--shadow-sm);
    }}
    .status-dot {{
      width: 18px;
      height: 18px;
      border-radius: 50%;
      display: grid;
      place-items: center;
      background: var(--accent);
      color: white;
      font-size: 11px;
      line-height: 1;
    }}
    .toolbar {{
      display: flex;
      justify-content: flex-end;
      margin-bottom: 16px;
    }}
    .search {{
      width: min(360px, 100%);
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 0 15px;
      min-height: 48px;
      border-radius: 12px;
      border: 1px solid var(--border);
      background: rgba(255, 255, 255, 0.82);
      box-shadow: var(--shadow-sm);
      color: var(--text-soft);
    }}
    .search svg {{ width: 19px; height: 19px; flex: 0 0 auto; }}
    .search input {{
      width: 100%;
      border: 0;
      outline: 0;
      background: transparent;
      color: var(--text);
      min-width: 0;
    }}
    .search input::placeholder {{ color: var(--text-soft); }}
    .screen {{ display: none; }}
    .screen.active {{ display: block; }}
    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 22px;
      margin-bottom: 24px;
    }}
    .grid {{ display: grid; gap: 22px; }}
    .grid.two {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    .grid.three {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    .card {{
      background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(255, 255, 255, 0.84)),
        var(--card);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      box-shadow: var(--shadow-md);
    }}
    .metric-card {{
      min-height: 194px;
      padding: 25px 26px;
      overflow: hidden;
      position: relative;
    }}
    .metric-card h3, .table-card h3, .panel h3 {{
      margin: 0;
      font-size: 17px;
      letter-spacing: -0.02em;
      font-weight: 760;
    }}
    .panel {{ padding: 22px; }}
    .calorie-chart {{ margin-top: 26px; }}
    .bar-track {{
      height: 54px;
      border-radius: 8px;
      background:
        repeating-linear-gradient(90deg, rgba(49, 91, 56, 0.08) 0, rgba(49, 91, 56, 0.08) 2px, transparent 2px, transparent 24px),
        #f5f7f1;
      padding: 9px;
      border: 1px solid #eef1ea;
    }}
    .bar-fill {{
      height: 100%;
      min-width: 18px;
      max-width: 100%;
      border-radius: 7px;
      background: linear-gradient(90deg, #5d8d62, #7ca77e);
      box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.35);
    }}
    .axis {{
      margin-top: 12px;
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      color: var(--text-soft);
      font-size: 13px;
    }}
    .axis span:nth-child(2) {{ text-align: center; }}
    .axis span:nth-child(3) {{ text-align: right; }}
    .big-number {{
      margin-top: 27px;
      font-size: 56px;
      line-height: 1;
      letter-spacing: -0.06em;
      font-weight: 820;
      color: var(--accent);
      font-variant-numeric: tabular-nums;
      overflow-wrap: anywhere;
    }}
    .metric-label {{
      margin-top: 16px;
      color: var(--text-muted);
    }}
    .ghost-icon {{
      position: absolute;
      right: 24px;
      bottom: 23px;
      width: 76px;
      height: 76px;
      border-radius: 26px;
      display: grid;
      place-items: center;
      color: var(--accent);
      background: var(--accent-soft);
      opacity: 0.75;
    }}
    .ghost-icon svg {{ width: 32px; height: 32px; }}
    .table-card {{ overflow: hidden; }}
    .table-header {{
      min-height: 62px;
      padding: 0 22px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }}
    .count-pill {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 34px;
      padding: 0 13px;
      border: 1px solid var(--border);
      border-radius: 999px;
      background: #f6f7f3;
      color: var(--text-muted);
      font-weight: 650;
      font-size: 13px;
      white-space: nowrap;
    }}
    .table-scroll {{ overflow-x: auto; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
      min-width: 920px;
    }}
    th {{
      height: 42px;
      padding: 0 12px;
      text-align: left;
      color: var(--text-muted);
      font-size: 12px;
      font-weight: 760;
      border-bottom: 1px solid var(--border);
      background: rgba(250, 251, 247, 0.84);
    }}
    td {{
      padding: 16px 12px;
      vertical-align: top;
      border-bottom: 1px solid var(--border);
      color: var(--text);
      font-size: 14px;
      overflow-wrap: anywhere;
    }}
    tr:last-child td {{ border-bottom: 0; }}
    tbody tr:hover {{ background: #fbfcf8; }}
    .muted {{ color: var(--text-soft); }}
    .num {{ font-variant-numeric: tabular-nums; }}
    .tag {{
      display: inline-flex;
      align-items: center;
      min-height: 26px;
      padding: 0 9px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      border: 1px solid var(--border);
      white-space: nowrap;
      color: var(--text-muted);
      background: #f6f7f3;
    }}
    .tag-breakfast {{
      color: var(--orange);
      background: var(--orange-soft);
      border-color: #f1dfca;
    }}
    .tag-meal, .tag-food {{
      color: var(--accent-dark);
      background: var(--accent-soft);
      border-color: var(--border-strong);
    }}
    .tag-beverage {{
      color: var(--blue);
      background: var(--blue-soft);
      border-color: #d9e8ed;
    }}
    .notes {{
      color: var(--text-muted);
      line-height: 1.45;
    }}
    .col-time {{ width: 7%; }}
    .col-type {{ width: 10%; }}
    .col-class {{ width: 10%; }}
    .col-item {{ width: 11%; }}
    .col-qty {{ width: 9%; }}
    .col-unit {{ width: 7%; }}
    .col-cal {{ width: 8%; }}
    .col-source {{ width: 17%; }}
    .col-notes {{ width: 21%; }}
    .section-head {{
      display: flex;
      justify-content: space-between;
      align-items: end;
      gap: 22px;
      margin-bottom: 18px;
    }}
    .section-head h2 {{
      margin: 0;
      font-size: 26px;
      letter-spacing: -0.04em;
      line-height: 1.1;
    }}
    .section-head p {{
      margin: 7px 0 0;
      color: var(--text-muted);
      font-size: 14px;
    }}
    .chart {{
      width: 100%;
      height: 130px;
      display: block;
      background:
        repeating-linear-gradient(90deg, rgba(49, 91, 56, 0.06) 0, rgba(49, 91, 56, 0.06) 1px, transparent 1px, transparent 28px),
        #f5f7f1;
      border-radius: 10px;
      border: 1px solid #eef1ea;
      margin-top: 14px;
    }}
    .empty-chart, .empty-state {{
      min-height: 94px;
      display: grid;
      place-items: center;
      color: var(--text-muted);
      border: 1px dashed var(--border-strong);
      border-radius: 12px;
      background: var(--card-soft);
      padding: 16px;
    }}
    .day-block {{ margin-bottom: 18px; }}
    .day-block:last-child {{ margin-bottom: 0; }}
    @media (max-width: 980px) {{
      .app-shell {{ grid-template-columns: 1fr; }}
      .sidebar {{
        position: static;
        height: auto;
        padding: 18px;
        border-right: 0;
        border-bottom: 1px solid var(--border);
      }}
      .brand {{ margin-bottom: 18px; }}
      .nav {{
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 8px;
      }}
      .nav-item {{
        justify-content: center;
        padding: 0 10px;
      }}
      .nav-item span {{ display: none; }}
      .plant, .sidebar-footer {{ display: none; }}
      main {{ padding: 24px 16px 34px; }}
      .topbar, .section-head {{
        display: flex;
        flex-direction: column;
        align-items: stretch;
      }}
      .summary-grid, .grid.two, .grid.three {{ grid-template-columns: 1fr; }}
      .toolbar {{ justify-content: stretch; }}
      .search {{ width: 100%; }}
    }}
  </style>
</head>
<body>
  <div class="app-shell">
    <aside class="sidebar">
      <div>
        <div class="brand">
          <div class="brand-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none">
              <path d="M19.4 4.6C16.5 4.4 14 5.2 12 7c-2 1.8-3 4.5-3 8 4.5-.1 7.6-1.3 9.3-3.6 1.3-1.7 1.7-4 1.1-6.8Z" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" />
              <path d="M5 19c2.1-5.2 5.7-8.7 10.8-10.4" stroke="currentColor" stroke-linecap="round" />
            </svg>
          </div>
          <div>
            <h1>Fer Health OS</h1>
            <p>CSV local dashboard</p>
          </div>
        </div>

        <nav class="nav" aria-label="Pantallas">
          <button class="nav-item active" data-screen="home">{nav_icon("home")}<span>Hoy</span></button>
          <button class="nav-item" data-screen="health">{nav_icon("health")}<span>Salud</span></button>
          <button class="nav-item" data-screen="food">{nav_icon("food")}<span>Comida</span></button>
          <button class="nav-item" data-screen="exercise">{nav_icon("exercise")}<span>Ejercicio</span></button>
          <button class="nav-item" data-screen="sleep">{nav_icon("sleep")}<span>Sueño</span></button>
        </nav>
      </div>

      <div>
        {plant_svg()}
        <div class="sidebar-footer">
          <strong>Datos locales</strong>
          CSV • Sin diagnosticos
        </div>
      </div>
    </aside>

    <main>
      <div class="content">
        <header class="topbar">
          <div class="headline">
            <h2>Hoy, {safe(today.isoformat())}</h2>
            <p>Generado desde CSVs locales. Sin diagnosticos, solo seguimiento.</p>
          </div>
          <div class="status-pill">
            <span class="status-dot">✓</span>
            Actualizado {safe(generated)}
          </div>
        </header>

        <section id="home" class="screen active">
          <div class="summary-grid">
            {progress_card("Calorias por dia", context["calories_today"], 3000, "1,500", "3,000")}
            {stat_card("Items registrados", str(len(food_rows)), "total historico", nav_icon("doc"))}
          </div>
          <div class="grid two">
            <section class="card panel">
              <h3>Como vamos hoy</h3>
              <div class="table-scroll" style="margin-top:18px;">
                <table>
                  <thead><tr><th>Area</th><th>Registro</th><th>Detalle</th></tr></thead>
                  <tbody>
                    <tr><td><span class="tag tag-food">Comida</span></td><td class="num">{safe(fmt(context["calories_today"]))}</td><td><span class="notes">calorias registradas hoy</span></td></tr>
                    <tr><td><span class="tag tag-meal">Ejercicio</span></td><td class="num">{safe(fmt(context["minutes_today"], " min"))}</td><td><span class="notes">actividad registrada hoy</span></td></tr>
                    <tr><td><span class="tag tag-beverage">Sueño</span></td><td class="num">{safe(fmt(today_sleep_hours, " h"))}</td><td><span class="notes">ultimo registro de sueño de hoy</span></td></tr>
                  </tbody>
                </table>
              </div>
            </section>
            <section class="card panel">
              <h3>Mini tendencias</h3>
              <div class="grid two" style="margin-top:18px;">
                <div><h3>Peso</h3>{line_chart(weight_points)}</div>
                <div><h3>Calorias</h3>{bar_chart(calorie_points)}</div>
              </div>
            </section>
          </div>
        </section>

        <section id="health" class="screen">
          <div class="section-head">
            <div><h2>Salud corporal</h2><p>Peso, grasa, hidratacion y origen de medicion.</p></div>
          </div>
          <div class="summary-grid">
            <section class="card panel"><h3>Peso</h3>{line_chart(weight_points)}</section>
            <section class="card panel"><h3>Grasa corporal</h3>{line_chart(fat_points, "#976735")}</section>
          </div>
          <div class="summary-grid">
            {stat_card("Peso mas reciente", fmt(latest_health.get("weight_kg"), " kg"), latest_health.get("date", ""))}
            {stat_card("Hidratacion", fmt(latest_health.get("hydration_pct"), "%"), latest_health.get("source", ""))}
          </div>
          <section class="card table-card">{table_header("Mediciones", len(health_rows))}{table(health_headers, sorted(health_rows, key=lambda row: (row.get("date", ""), row.get("time", "")), reverse=True))}</section>
        </section>

        <section id="food" class="screen">
          <div class="section-head">
            <div><h2>Comida por dia</h2><p>Revisa que comio ayer, antier o cualquier dia registrado.</p></div>
            {search_box("food", "Filtrar por fecha o texto")}
          </div>
          <div class="summary-grid">
            {progress_card("Calorias por dia", context["calories_today"], 3000, "1,500", "3,000")}
            {stat_card("Items registrados", str(len(food_rows)), "total historico", nav_icon("doc"))}
          </div>
          <div class="filterable" data-list="food">
            {day_blocks(group_by_date(food_rows), lambda rows: table(food_headers, sorted(rows, key=lambda row: row.get("time", ""))))}
          </div>
        </section>

        <section id="exercise" class="screen">
          <div class="section-head">
            <div><h2>Ejercicio</h2><p>Sesiones, intensidad, duracion y calorias estimadas.</p></div>
            {search_box("exercise", "Filtrar por fecha o tipo")}
          </div>
          <div class="summary-grid">
            <section class="card panel"><h3>Minutos por dia</h3>{bar_chart(exercise_points)}</section>
            {stat_card("Sesiones registradas", str(len(exercise_rows)), "total historico")}
          </div>
          <div class="filterable" data-list="exercise">
            {day_blocks(group_by_date(exercise_rows), lambda rows: exercise_table(exercise_headers, sorted(rows, key=lambda row: row.get("time", ""))))}
          </div>
        </section>

        <section id="sleep" class="screen">
          <div class="section-head">
            <div><h2>Sueño</h2><p>Horas, calidad y visitas al baño por noche.</p></div>
          </div>
          <div class="summary-grid">
            <section class="card panel"><h3>Horas de sueño</h3>{line_chart(sleep_points)}</section>
            <section class="card panel"><h3>Calidad</h3>{line_chart(quality_points, "#416c7a")}</section>
          </div>
          <section class="card table-card">{table_header("Registros de sueño", len(sleep_rows))}{table(sleep_headers, sorted(sleep_rows, key=lambda row: row.get("date", ""), reverse=True))}</section>
        </section>
      </div>
    </main>
  </div>
  <script type="application/json" id="payload">{safe(json.dumps(payload))}</script>
  <script>
    if (window.location.protocol.startsWith('http')) {{
      const currentVersion = document.documentElement.dataset.version;
      const reloadWhenUpdated = (version) => {{
        if (version && currentVersion && version !== currentVersion) {{
          window.location.reload();
        }}
      }};

      if (typeof EventSource !== 'undefined') {{
        const events = new EventSource('/events');
        events.addEventListener('dashboard-updated', (event) => reloadWhenUpdated(event.data));
      }} else {{
        window.setInterval(async () => {{
          try {{
            const response = await fetch('/version', {{ cache: 'no-store' }});
            reloadWhenUpdated((await response.text()).trim());
          }} catch (error) {{
            console.warn('Dashboard refresh check failed', error);
          }}
        }}, 2000);
      }}
    }}

    const buttons = document.querySelectorAll('[data-screen]');
    const screens = document.querySelectorAll('.screen');
    buttons.forEach((button) => {{
      button.addEventListener('click', () => {{
        buttons.forEach((item) => item.classList.remove('active'));
        screens.forEach((screen) => screen.classList.remove('active'));
        button.classList.add('active');
        document.getElementById(button.dataset.screen).classList.add('active');
      }});
    }});

    document.querySelectorAll('[data-filter]').forEach((input) => {{
      input.addEventListener('input', () => {{
        const list = document.querySelector(`[data-list="${{input.dataset.filter}}"]`);
        const query = input.value.trim().toLowerCase();
        list.querySelectorAll('.day-block').forEach((block) => {{
          block.style.display = block.innerText.toLowerCase().includes(query) ? '' : 'none';
        }});
      }});
    }});
  </script>
</body>
</html>
"""


def search_box(kind, placeholder):
    return (
        f'<label class="search" aria-label="{safe(placeholder)}">'
        '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">'
        '<path d="m21 21-4.3-4.3M10.8 18a7.2 7.2 0 1 1 0-14.4 7.2 7.2 0 0 1 0 14.4Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" />'
        '</svg>'
        f'<input type="search" data-filter="{safe(kind)}" placeholder="{safe(placeholder)}">'
        '</label>'
    )


def table_header(title, count):
    return (
        '<div class="table-header">'
        f'<h3>{safe(title)}</h3>'
        f'<span class="count-pill">{count} registros</span>'
        '</div>'
    )


def main():
    context = build_context()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(render_dashboard(context), encoding="utf-8")
    print(f"Wrote {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
