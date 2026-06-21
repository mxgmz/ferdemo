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


def line_chart(points, color="#7AE7B7"):
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


def bar_chart(points, color="#B8A4FF"):
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


def stat_card(label, value, hint=""):
    return (
        '<article class="stat-card">'
        f'<span>{safe(label)}</span>'
        f'<strong>{safe(value)}</strong>'
        f'<small>{safe(hint)}</small>'
        "</article>"
    )


def table(headers, rows):
    if not rows:
        return '<div class="empty-state">Sin registros para mostrar.</div>'
    head = "".join(f"<th>{safe(label)}</th>" for _, label in headers)
    body_rows = []
    for row in rows:
        cells = "".join(f"<td>{safe(row.get(key, ''))}</td>" for key, _ in headers)
        body_rows.append(f"<tr>{cells}</tr>")
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{"".join(body_rows)}</tbody></table></div>'


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
            '<section class="day-block">'
            f'<header><strong>{safe(day)}</strong><span>{len(rows)} registros</span></header>'
            f"{renderer(rows)}"
            "</section>"
        )
    return "".join(blocks)


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
        ("api_food_name", "Fuente API"),
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

    payload = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "version": datetime.now().isoformat(timespec="microseconds"),
        "today": today.isoformat(),
    }

    return f"""<!doctype html>
<html lang="es" data-version="{safe(payload["version"])}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%230B0F0E'/%3E%3Cpath d='M8 17h5l2-6 4 12 2-6h3' fill='none' stroke='%237AE7B7' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E">
  <title>Fer Health OS Dashboard</title>
  <style>
    :root {{
      --bg: #0B0F0E;
      --panel: #121816;
      --panel-2: #18201D;
      --line: #33443D;
      --text: #EFF7F2;
      --muted: #98A79F;
      --mint: #7AE7B7;
      --violet: #B8A4FF;
      --amber: #F4C95D;
      --coral: #F97068;
      --shadow: 0 18px 60px rgba(0, 0, 0, 0.28);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, Avenir Next, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
    }}
    button, input {{ font: inherit; }}
    .shell {{ display: grid; grid-template-columns: 240px 1fr; min-height: 100dvh; }}
    .rail {{
      border-right: 1px solid var(--line);
      background: #09100D;
      padding: 22px 16px;
      position: sticky;
      top: 0;
      height: 100dvh;
    }}
    .brand {{ display: grid; gap: 4px; margin-bottom: 24px; }}
    .brand strong {{ font-size: 18px; }}
    .brand span, .meta, small {{ color: var(--muted); }}
    .nav {{ display: grid; gap: 8px; }}
    .nav button {{
      min-height: 44px;
      border: 1px solid transparent;
      border-radius: 6px;
      background: transparent;
      color: var(--muted);
      text-align: left;
      padding: 10px 12px;
      cursor: pointer;
    }}
    .nav button.active, .nav button:hover, .nav button:focus-visible {{
      color: var(--text);
      border-color: var(--line);
      background: var(--panel);
      outline: none;
    }}
    main {{ padding: 28px; max-width: 1380px; width: 100%; }}
    .topbar {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 18px; margin-bottom: 22px; }}
    h1, h2, h3 {{ margin: 0; letter-spacing: 0; }}
    h1 {{ font-size: 28px; line-height: 1.2; }}
    h2 {{ font-size: 20px; margin-bottom: 14px; }}
    h3 {{ font-size: 15px; }}
    .screen {{ display: none; }}
    .screen.active {{ display: block; }}
    .grid {{ display: grid; gap: 14px; }}
    .stats {{ grid-template-columns: repeat(4, minmax(0, 1fr)); margin-bottom: 18px; }}
    .two {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    .three {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    .panel, .stat-card, .day-block {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }}
    .panel {{ padding: 16px; }}
    .stat-card {{ padding: 14px; display: grid; gap: 4px; min-height: 112px; }}
    .stat-card span {{ color: var(--muted); font-size: 13px; }}
    .stat-card strong {{ font-size: 28px; font-variant-numeric: tabular-nums; line-height: 1.1; }}
    .stat-card small {{ min-height: 20px; }}
    .today-list {{ display: grid; gap: 10px; }}
    .today-item {{
      display: grid;
      grid-template-columns: 90px 1fr auto;
      gap: 12px;
      align-items: center;
      min-height: 48px;
      padding: 10px 12px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--panel-2);
    }}
    .pill {{
      display: inline-flex;
      width: fit-content;
      align-items: center;
      min-height: 26px;
      padding: 3px 9px;
      border-radius: 999px;
      border: 1px solid var(--line);
      color: var(--mint);
      background: rgba(122, 231, 183, 0.08);
      font-size: 12px;
    }}
    .chart {{ width: 100%; height: 130px; display: block; background: var(--panel-2); border-radius: 6px; }}
    .chart-row {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }}
    .empty-chart, .empty-state {{
      min-height: 84px;
      display: grid;
      place-items: center;
      color: var(--muted);
      border: 1px dashed var(--line);
      border-radius: 6px;
      background: var(--panel-2);
      padding: 16px;
    }}
    .day-block {{ overflow: hidden; box-shadow: none; }}
    .day-block header {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      padding: 12px 14px;
      background: var(--panel-2);
      border-bottom: 1px solid var(--line);
    }}
    .day-block header span {{ color: var(--muted); }}
    .table-wrap {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; min-width: 760px; }}
    th, td {{ text-align: left; padding: 11px 12px; border-bottom: 1px solid rgba(51, 68, 61, 0.75); vertical-align: top; }}
    th {{ color: var(--muted); font-size: 12px; font-weight: 600; }}
    td {{ font-size: 14px; }}
    .section-head {{ display: flex; justify-content: space-between; gap: 16px; align-items: end; margin: 4px 0 16px; }}
    .section-head p {{ margin: 4px 0 0; color: var(--muted); }}
    .search {{
      min-height: 44px;
      width: min(280px, 100%);
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--panel);
      color: var(--text);
      padding: 9px 12px;
    }}
    .meta {{ font-size: 13px; }}
    @media (max-width: 920px) {{
      .shell {{ grid-template-columns: 1fr; }}
      .rail {{ position: static; height: auto; border-right: 0; border-bottom: 1px solid var(--line); }}
      .nav {{ grid-template-columns: repeat(5, minmax(0, 1fr)); }}
      .nav button {{ text-align: center; padding: 8px 6px; }}
      main {{ padding: 18px; }}
      .stats, .two, .three, .chart-row {{ grid-template-columns: 1fr; }}
      .topbar, .section-head {{ display: grid; }}
      .today-item {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <aside class="rail">
      <div class="brand">
        <strong>Fer Health OS</strong>
        <span>CSV local dashboard</span>
      </div>
      <nav class="nav" aria-label="Pantallas">
        <button class="active" data-screen="home">Hoy</button>
        <button data-screen="health">Salud</button>
        <button data-screen="food">Comida</button>
        <button data-screen="exercise">Ejercicio</button>
        <button data-screen="sleep">Sueño</button>
      </nav>
    </aside>
    <main>
      <div class="topbar">
        <div>
          <h1>Hoy, {safe(today.isoformat())}</h1>
          <div class="meta">Generado desde CSVs locales. Sin diagnosticos, solo seguimiento.</div>
        </div>
        <div class="pill">Actualizado {safe(payload["generated"])}</div>
      </div>

      <section id="home" class="screen active">
        <div class="grid stats">
          {stat_card("Peso mas reciente", fmt(latest_health.get("weight_kg"), " kg"), latest_health.get("date", ""))}
          {stat_card("Grasa corporal", fmt(latest_health.get("body_fat_pct"), "%"), latest_health.get("source", ""))}
          {stat_card("Calorias hoy", fmt(context["calories_today"]), f'{len(context["today_food"])} comidas registradas')}
          {stat_card("Ejercicio hoy", fmt(context["minutes_today"], " min"), f'{len(context["today_exercise"])} sesiones registradas')}
        </div>
        <div class="grid two">
          <section class="panel">
            <h2>Como vamos hoy</h2>
            <div class="today-list">
              <div class="today-item"><span class="pill">Comida</span><strong>{safe(fmt(context["calories_today"]))}</strong><small>calorias registradas hoy</small></div>
              <div class="today-item"><span class="pill">Ejercicio</span><strong>{safe(fmt(context["minutes_today"], " min"))}</strong><small>actividad registrada hoy</small></div>
              <div class="today-item"><span class="pill">Sueño</span><strong>{safe(fmt((number(context["today_sleep"][-1]["duration_hours"]) if context["today_sleep"] else None), " h"))}</strong><small>ultimo registro de sueño de hoy</small></div>
            </div>
          </section>
          <section class="panel">
            <h2>Mini tendencias</h2>
            <div class="chart-row">
              <div><h3>Peso</h3>{line_chart(weight_points, "#7AE7B7")}</div>
              <div><h3>Calorias</h3>{bar_chart(calorie_points, "#B8A4FF")}</div>
            </div>
          </section>
        </div>
      </section>

      <section id="health" class="screen">
        <div class="section-head">
          <div><h2>Salud corporal</h2><p>Peso, grasa, hidratacion y origen de medicion.</p></div>
        </div>
        <div class="grid three">
          <section class="panel"><h3>Peso</h3>{line_chart(weight_points, "#7AE7B7")}</section>
          <section class="panel"><h3>Grasa corporal</h3>{line_chart(fat_points, "#F4C95D")}</section>
          {stat_card("Hidratacion mas reciente", fmt(latest_health.get("hydration_pct"), "%"), latest_health.get("date", ""))}
        </div>
        <div class="grid" style="margin-top:14px;">{table(health_headers, sorted(health_rows, key=lambda row: (row.get("date", ""), row.get("time", "")), reverse=True))}</div>
      </section>

      <section id="food" class="screen">
        <div class="section-head">
          <div><h2>Comida por dia</h2><p>Revisa que comio ayer, antier o cualquier dia registrado.</p></div>
          <input class="search" data-filter="food" placeholder="Filtrar por fecha o texto">
        </div>
        <div class="grid two">
          <section class="panel"><h3>Calorias por dia</h3>{bar_chart(calorie_points, "#B8A4FF")}</section>
          {stat_card("Items registrados", str(len(food_rows)), "total historico")}
        </div>
        <div class="grid filterable" data-list="food" style="margin-top:14px;">
          {day_blocks(group_by_date(food_rows), lambda rows: table(food_headers, sorted(rows, key=lambda row: row.get("time", ""))))}
        </div>
      </section>

      <section id="exercise" class="screen">
        <div class="section-head">
          <div><h2>Ejercicio</h2><p>Sesiones, intensidad, duracion y calorias estimadas.</p></div>
          <input class="search" data-filter="exercise" placeholder="Filtrar por fecha o tipo">
        </div>
        <div class="grid two">
          <section class="panel"><h3>Minutos por dia</h3>{bar_chart(exercise_points, "#7AE7B7")}</section>
          {stat_card("Sesiones registradas", str(len(exercise_rows)), "total historico")}
        </div>
        <div class="grid filterable" data-list="exercise" style="margin-top:14px;">
          {day_blocks(group_by_date(exercise_rows), lambda rows: exercise_table(exercise_headers, sorted(rows, key=lambda row: row.get("time", ""))))}
        </div>
      </section>

      <section id="sleep" class="screen">
        <div class="section-head">
          <div><h2>Sueño</h2><p>Horas, calidad y visitas al baño por noche.</p></div>
        </div>
        <div class="grid two">
          <section class="panel"><h3>Horas de sueño</h3>{line_chart(sleep_points, "#7AE7B7")}</section>
          <section class="panel"><h3>Calidad</h3>{line_chart(quality_points, "#B8A4FF")}</section>
        </div>
        <div class="grid" style="margin-top:14px;">{table(sleep_headers, sorted(sleep_rows, key=lambda row: row.get("date", ""), reverse=True))}</div>
      </section>
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


def main():
    context = build_context()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(render_dashboard(context), encoding="utf-8")
    print(f"Wrote {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
