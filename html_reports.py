from __future__ import annotations

from html import escape


THEMES = {
    "teal": {
        "accent": "#0f766e",
        "header_bg": "#eef3f8",
        "notice_bg": "#eefaf8",
        "notice_color": "#173f3b",
    },
    "blue": {
        "accent": "#2563eb",
        "header_bg": "#edf4ff",
        "notice_bg": "#eff6ff",
        "notice_color": "#17345f",
    },
}


def format_value(value):
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def html_value(value):
    return escape(format_value(value), quote=True)


def render_table(columns, rows, *, empty_text="No represented rows"):
    header = "".join(f"<th>{escape(label)}</th>" for _, label in columns)
    body_rows = []
    for row in rows:
        cells = "".join(
            f"<td>{html_value(row.get(key))}</td>" for key, _ in columns
        )
        body_rows.append(f"<tr>{cells}</tr>")
    if not body_rows:
        body_rows.append(
            f'<tr><td colspan="{len(columns)}">{escape(empty_text)}</td></tr>'
        )
    return (
        "<table>"
        f"<thead><tr>{header}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table>"
    )


def render_meta_grid(items):
    return "".join(
        '<div><div class="label">{}</div><div class="value">{}</div></div>'.format(
            escape(label), html_value(value)
        )
        for label, value in items
    )


def render_page(title, meta_items, sections, notice, *, theme="teal"):
    colors = THEMES.get(theme, THEMES["teal"])
    section_html = "\n".join(
        f"  <h2>{escape(heading)}</h2>\n  {content}"
        for heading, content in sections
    )
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #18212f;
      --muted: #536173;
      --line: #d6dde7;
      --panel: #f7f9fb;
      --accent: {colors['accent']};
      --header-bg: {colors['header_bg']};
      --notice-bg: {colors['notice_bg']};
      --notice-color: {colors['notice_color']};
    }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--ink);
      background: #ffffff;
      line-height: 1.45;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 32px 20px 44px;
    }}
    h1 {{ margin: 0 0 8px; font-size: 28px; }}
    h2 {{ margin: 28px 0 10px; font-size: 18px; }}
    .meta {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 10px;
      padding: 16px;
      border: 1px solid var(--line);
      background: var(--panel);
    }}
    .meta div {{ min-width: 0; }}
    .label {{ color: var(--muted); font-size: 12px; text-transform: uppercase; }}
    .value {{ font-weight: 700; overflow-wrap: anywhere; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
    th, td {{ border: 1px solid var(--line); padding: 8px 10px; text-align: left; }}
    th {{ background: var(--header-bg); }}
    .notice {{
      margin-top: 28px;
      padding: 14px 16px;
      border-left: 4px solid var(--accent);
      background: var(--notice-bg);
      color: var(--notice-color);
    }}
  </style>
</head>
<body>
<main>
  <h1>{escape(title)}</h1>
  <div class="meta">{render_meta_grid(meta_items)}</div>
{section_html}
  <div class="notice">{html_value(notice)}</div>
</main>
</body>
</html>
'''
