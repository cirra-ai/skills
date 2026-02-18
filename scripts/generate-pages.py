#!/usr/bin/env python3
"""
Generate docs/index.html from plugin.json files.

Usage:
    python3 scripts/generate-pages.py [repo_root]

Outputs the generated HTML to stdout. The workflow pipes this to docs/index.html.
Run locally to preview changes: python3 scripts/generate-pages.py . > docs/index.html
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()

# Cirra AI icon SVG (logo-cloud-32.svg from web-app, with unique gradient IDs)
LOGO_ICON_SVG = (
    '<svg width="40" height="40" viewBox="0 0 32 32" fill="none" '
    'xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
    '<rect width="32" height="32" rx="8" fill="white"/>'
    '<path d="M26 3.62601V5.54029C26 5.88611 25.7247 6.1663 25.385 6.1663H22.8478'
    "C20.3569 6.1663 18.3068 8.12858 18.1133 10.616C18.096 10.8335 17.9179 11 "
    "17.7043 11H15.4135C15.1729 11 14.9881 10.7923 15.0006 10.5474C15.2306 6.3397 "
    '18.6562 3 22.8478 3H25.385C25.7247 3 26 3.28019 26 3.62601Z" fill="url(#lg0)"/>'
    '<path d="M14.2173 25.9421C11.3581 25.9421 9.03974 23.6099 9.03974 20.7337V20.2654'
    "C9.03974 17.3891 11.3581 15.0569 14.2173 15.0569H17.7395C18.0357 15.0569 "
    "18.2765 15.2991 18.2765 15.5972V17.6153C18.2765 17.9133 18.5173 18.1555 "
    "18.8135 18.1555H20.8197C21.1159 18.1555 21.3567 17.9133 21.3567 17.6153"
    "V15.5972C21.3567 15.2991 21.1159 15.0569 20.8197 15.0569H18.8164C18.5201 "
    "15.0569 18.2793 14.8147 18.2793 14.5167V12.5402C18.2793 12.2422 18.0386 12 "
    "17.7423 12H14.2173C9.67928 12 6 15.7012 6 20.2663V20.7337C6 25.2988 9.67928 "
    '29 14.2173 29H25.463C25.7592 29 26 28.7578 26 28.4598V26.4833C26 26.1853 '
    '25.7592 25.9431 25.463 25.9431H14.2173V25.9421Z" fill="url(#lg1)"/>'
    "<defs>"
    '<linearGradient id="lg0" x1="15.85" y1="2.33" x2="42.19" y2="28.21" '
    'gradientUnits="userSpaceOnUse">'
    '<stop stop-color="#00FFDA"/><stop offset="0.9" stop-color="#4068EB"/>'
    "</linearGradient>"
    '<linearGradient id="lg1" x1="6.08" y1="12.12" x2="31.52" y2="37.41" '
    'gradientUnits="userSpaceOnUse">'
    '<stop stop-color="#24F0BA"/><stop offset="0.68" stop-color="#4068EB"/>'
    "</linearGradient>"
    "</defs>"
    "</svg>"
)

# Keywords to suppress from tags (too generic to be useful)
SUPPRESS_KEYWORDS = {"cirra-ai", "salesforce"}


def find_plugins() -> list[dict]:
    """Scan repo for plugins with .claude-plugin/plugin.json and return sorted list."""
    plugins = []
    for plugin_json_path in sorted(REPO_ROOT.glob("*/.claude-plugin/plugin.json")):
        plugin_dir = plugin_json_path.parent.parent
        plugin_name = plugin_dir.name

        # Skip directories with spaces (build artifacts)
        if " " in plugin_name:
            continue

        try:
            data = json.loads(plugin_json_path.read_text())
        except Exception as e:
            print(f"Warning: could not parse {plugin_json_path}: {e}", file=sys.stderr)
            continue

        keywords = [k for k in data.get("keywords", []) if k not in SUPPRESS_KEYWORDS]
        has_skills = any(plugin_dir.glob("skills/*/SKILL.md"))
        is_orchestrator = "orchestration" in data.get("keywords", [])

        plugins.append(
            {
                "name": data.get("name", plugin_name),
                "version": data.get("version", ""),
                "description": data.get("description", ""),
                "keywords": keywords,
                "has_skills": has_skills,
                "is_orchestrator": is_orchestrator,
            }
        )

    # Specialist plugins first, orchestrators last; alphabetical within each group
    plugins.sort(key=lambda p: (1 if p["is_orchestrator"] else 0, p["name"]))
    return plugins


def esc(text: str) -> str:
    """Minimal HTML escaping for text content."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_tags(keywords: list[str], version: str) -> str:
    tags = []
    if version:
        tags.append(f'<span class="tag">v{version}</span>')
    for kw in keywords[:5]:
        tags.append(f'<span class="tag">{esc(kw)}</span>')
    return "\n          ".join(tags)


def render_plugin_card(plugin: dict) -> str:
    name = esc(plugin["name"])
    desc = esc(plugin["description"])
    tags = render_tags(plugin["keywords"], plugin["version"])
    dl_url = f"https://github.com/cirra-ai/skills/releases/latest/download/{plugin['name']}.zip"
    return f"""\
  <div class="card">
    <div class="card-body">
      <div class="card-title">{name}</div>
      <div class="card-desc">{desc}</div>
      <div class="card-tags">
          {tags}
      </div>
    </div>
    <a class="btn btn-primary" href="{dl_url}">&#11015; Download</a>
  </div>"""


def render_skill_card(plugin: dict) -> str:
    name = esc(plugin["name"])
    # Trim description to ~150 chars for the skill-only card
    desc = plugin["description"]
    if len(desc) > 150:
        desc = desc[:147].rstrip() + "…"
    desc = esc(desc)
    tags = render_tags(plugin["keywords"][:2], "")
    dl_url = (
        f"https://github.com/cirra-ai/skills/releases/latest/download/"
        f"{plugin['name']}-skill.zip"
    )
    return f"""\
  <div class="card">
    <div class="card-body">
      <div class="card-title">{name} — Skill Only</div>
      <div class="card-desc">{desc}</div>
      <div class="card-tags">
          {tags}
          <span class="tag">skill-only</span>
      </div>
    </div>
    <a class="btn btn-outline" href="{dl_url}">&#11015; Download</a>
  </div>"""


def all_in_one_tags(plugins: list[dict]) -> str:
    names = [p["name"].replace("cirra-ai-sf-", "").replace("cirra-ai-sf", "sf") for p in plugins]
    return "\n          ".join(f'<span class="tag">{esc(n)}</span>' for n in names)


def generate_html(plugins: list[dict]) -> str:
    year = datetime.now().year
    plugin_cards = "\n\n".join(render_plugin_card(p) for p in plugins)
    skill_plugins = [p for p in plugins if p["has_skills"]]
    skill_cards = "\n\n".join(render_skill_card(p) for p in skill_plugins)
    bundle_tags = all_in_one_tags(plugins)
    plugin_count = len(plugins)

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Cirra AI Salesforce Plugins — Downloads</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg:       #0f1117;
      --surface:  #1a1d27;
      --border:   #2a2d3a;
      --accent:   #5b8ef0;
      --accent2:  #38c78a;
      --text:     #e2e8f0;
      --muted:    #8892a4;
      --tag-bg:   #1e2535;
      --tag-text: #7aa2f7;
    }}

    body {{
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 15px;
      line-height: 1.6;
      padding: 2rem 1rem 4rem;
    }}

    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}

    .container {{ max-width: 860px; margin: 0 auto; }}

    /* ── Header ── */
    .site-header {{
      display: flex;
      align-items: center;
      gap: 1rem;
      margin-bottom: 2.5rem;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid var(--border);
    }}
    .site-header .logo-icon {{
      flex-shrink: 0;
      display: flex;
      align-items: center;
    }}
    .site-header .logo {{
      font-size: 1.6rem;
      font-weight: 700;
      color: var(--text);
    }}
    .site-header .logo span {{ color: var(--accent); }}
    .site-header .sub {{ color: var(--muted); font-size: 0.9rem; margin-top: 0.15rem; }}
    .badge {{
      display: inline-block;
      padding: 0.15rem 0.55rem;
      border-radius: 9999px;
      font-size: 0.7rem;
      font-weight: 600;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }}
    .badge-blue  {{ background: #1e3a6e; color: #7aa2f7; }}
    .badge-green {{ background: #1a3d30; color: #38c78a; }}

    /* ── Intro ── */
    .intro {{ margin-bottom: 2rem; color: var(--muted); max-width: 640px; }}
    .intro strong {{ color: var(--text); }}

    /* ── Section headings ── */
    h2 {{
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--text);
      margin: 2.5rem 0 1rem;
      padding-bottom: 0.4rem;
      border-bottom: 1px solid var(--border);
    }}
    h2 .badge {{ margin-left: 0.5rem; vertical-align: middle; }}

    /* ── Cards ── */
    .card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.25rem 1.5rem;
      margin-bottom: 1rem;
      display: flex;
      align-items: flex-start;
      gap: 1.25rem;
    }}
    .card.featured {{
      border-color: var(--accent);
      background: #141827;
    }}
    .card-body {{ flex: 1; min-width: 0; }}
    .card-title {{
      font-size: 1rem;
      font-weight: 600;
      color: var(--text);
      margin-bottom: 0.25rem;
    }}
    .card-desc {{ color: var(--muted); font-size: 0.875rem; margin-bottom: 0.6rem; }}
    .card-tags {{ display: flex; flex-wrap: wrap; gap: 0.35rem; }}
    .tag {{
      display: inline-block;
      background: var(--tag-bg);
      color: var(--tag-text);
      border-radius: 4px;
      font-size: 0.72rem;
      padding: 0.1rem 0.45rem;
      font-family: "SF Mono", "Fira Code", monospace;
    }}

    /* ── Download button ── */
    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.5rem 1rem;
      border-radius: 6px;
      font-size: 0.85rem;
      font-weight: 600;
      white-space: nowrap;
      transition: opacity 0.15s;
      text-decoration: none !important;
    }}
    .btn:hover {{ opacity: 0.85; }}
    .btn-primary  {{ background: var(--accent); color: #fff; }}
    .btn-secondary {{ background: var(--accent2); color: #000; }}
    .btn-outline {{
      background: transparent;
      color: var(--accent);
      border: 1px solid var(--accent);
    }}

    /* ── How to install section ── */
    .install-box {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.25rem 1.5rem;
      margin-bottom: 1rem;
    }}
    .install-box h3 {{ font-size: 0.95rem; font-weight: 600; margin-bottom: 0.75rem; }}
    .install-box ol {{ padding-left: 1.25rem; color: var(--muted); font-size: 0.875rem; }}
    .install-box li {{ margin-bottom: 0.4rem; }}
    .install-box li strong {{ color: var(--text); }}
    code {{
      font-family: "SF Mono", "Fira Code", monospace;
      font-size: 0.82rem;
      background: #12151f;
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 0.05rem 0.35rem;
      color: #e2e8f0;
    }}

    /* ── Callout ── */
    .callout {{
      background: #12192b;
      border-left: 3px solid var(--accent);
      border-radius: 0 6px 6px 0;
      padding: 0.75rem 1rem;
      font-size: 0.875rem;
      color: var(--muted);
      margin-bottom: 1.5rem;
    }}
    .callout strong {{ color: var(--text); }}

    /* ── Footer ── */
    .site-footer {{
      margin-top: 3rem;
      padding-top: 1.5rem;
      border-top: 1px solid var(--border);
      color: var(--muted);
      font-size: 0.82rem;
      display: flex;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 0.5rem;
    }}

    @media (max-width: 620px) {{
      .card {{ flex-direction: column; gap: 0.75rem; }}
    }}
  </style>
</head>
<body>
<div class="container">

  <!-- Header -->
  <header class="site-header">
    <div class="logo-icon">
      {LOGO_ICON_SVG}
    </div>
    <div>
      <div class="logo">Cirra AI <span>Salesforce Plugins</span></div>
      <div class="sub">Claude Code &amp; Claude Cowork plugins for Salesforce development</div>
    </div>
  </header>

  <!-- Intro -->
  <p class="intro">
    Download and install AI plugins for Salesforce development in <strong>Claude Code</strong> or
    <strong>Claude Cowork</strong>. Each package includes everything needed to generate Apex code,
    build Flows, query data, and more — powered by the Cirra AI MCP Server.
  </p>

  <div class="callout">
    <strong>What should I download?</strong> — If you&#8217;re not sure, grab the
    <strong>All-in-One Plugin Bundle</strong> below. It installs all {plugin_count} plugins at once.
    Individual plugins and skill-only files are also available for leaner installs.
  </div>

  <!-- ── Plugin Packages ── -->
  <h2>Plugin Packages <span class="badge badge-blue">Recommended</span></h2>
  <p style="color:var(--muted);font-size:0.875rem;margin-bottom:1.25rem;">
    Full packages with skills, commands, hooks, templates, and MCP server configuration.
    Install via the plugin manager or by uploading the zip in Claude Cowork.
  </p>

  <!-- All-in-one bundle (featured) -->
  <div class="card featured">
    <div class="card-body">
      <div class="card-title">All-in-One Plugin Bundle</div>
      <div class="card-desc">
        All {plugin_count} Salesforce plugins in one zip. The easiest way to get started.
      </div>
      <div class="card-tags">
          {bundle_tags}
      </div>
    </div>
    <a class="btn btn-secondary"
       href="https://github.com/cirra-ai/skills/releases/latest/download/cirra-ai-sf-skills.zip">
      &#11015; Download Bundle
    </a>
  </div>

  <!-- Individual plugin cards (auto-generated from plugin.json files) -->
{plugin_cards}

  <!-- ── Skill-Only Files ── -->
  <h2>Skill-Only Files <span class="badge badge-green">Lightweight</span></h2>
  <p style="color:var(--muted);font-size:0.875rem;margin-bottom:1.25rem;">
    Just the <code>SKILL.md</code> instruction file, plus <code>LICENSE</code> and
    <code>CREDITS.md</code>. Use these if you only want the AI instructions without hooks,
    commands, or templates. Each file includes a self-contained license section.
  </p>

{skill_cards}

  <!-- ── How to Install ── -->
  <h2>How to Install</h2>

  <div class="install-box">
    <h3>Claude Cowork (browser)</h3>
    <ol>
      <li>Download a plugin zip from above</li>
      <li>Open Claude Cowork and click <strong>Plugins</strong> in the left sidebar</li>
      <li>Click <strong>Upload Plugin</strong> and select the downloaded zip</li>
      <li>The plugin activates immediately in your current session</li>
    </ol>
  </div>

  <div class="install-box">
    <h3>Claude Code (CLI)</h3>
    <ol>
      <li>Download a plugin zip and note the path</li>
      <li>Run: <code>/plugin install path/to/cirra-ai-sf-apex.zip</code></li>
      <li>Or install directly from the marketplace:<br>
          <code>/plugin marketplace add cirra-ai/skills</code><br>
          <code>/plugin install cirra-ai-sf-apex@cirra-ai</code>
      </li>
    </ol>
  </div>

  <div class="install-box">
    <h3>Skill-Only Files</h3>
    <ol>
      <li>Download a skill zip and extract it</li>
      <li>Place <code>SKILL.md</code> in your project&#8217;s <code>.claude/skills/</code> directory</li>
      <li>Claude will pick up the skill automatically in that project</li>
    </ol>
  </div>

  <!-- Footer -->
  <footer class="site-footer">
    <span>
      &copy; {year} <a href="https://cirra.ai">Cirra AI, Inc.</a> — MIT License
    </span>
    <span>
      <a href="https://github.com/cirra-ai/skills">GitHub</a> &#183;
      <a href="https://github.com/cirra-ai/skills/releases">All Releases</a> &#183;
      <a href="https://github.com/cirra-ai/skills/issues">Issues</a>
    </span>
  </footer>

</div>
</body>
</html>
"""


if __name__ == "__main__":
    plugins = find_plugins()
    if not plugins:
        print("Warning: no plugins found!", file=sys.stderr)
    print(f"Found {len(plugins)} plugins: {[p['name'] for p in plugins]}", file=sys.stderr)
    print(generate_html(plugins), end="")
