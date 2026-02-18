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

# Full Cirra AI wordmark SVG (logo.svg from web-app).
# CSS variables replaced with hardcoded values for dark-background standalone HTML:
#   --logo-secondary  -> #e2e8f0  (letterforms: white/light on dark bg)
#   --logo-primary    -> #5b8ef0  (i-dot, A, I: page accent blue)
#   --logo-gradient-start  -> #00ffda
#   --logo-gradient-middle -> #24f0ba
#   --logo-gradient-end    -> #4068eb
# Gradient IDs renamed to avoid conflicts if the SVG is ever used multiple times.
LOGO_FULL_SVG = """\
<svg xmlns="http://www.w3.org/2000/svg" width="153" height="54" viewBox="0 0 102 36" fill="none" aria-label="Cirra AI">
  <path d="M24.3738 6.44169V8.15064C24.3738 8.45707 24.1263 8.71046 23.814 8.71046H21.5039C19.2411 8.71046 17.373 10.4666 17.1962 12.6882C17.1785 12.8826 17.0194 13.03 16.825 13.03H14.7389C14.5208 13.03 14.3499 12.8414 14.3617 12.6234C14.5739 8.86368 17.6853 5.88186 21.498 5.88186H23.8081C24.1145 5.88186 24.3679 6.12937 24.3679 6.44169H24.3738Z" fill="url(#cai-g0)"/>
  <path d="M13.4011 27.3793C10.7375 27.3793 8.58074 25.2225 8.58074 22.5589V22.1287C8.58074 19.4651 10.7375 17.3083 13.4011 17.3083H16.6776C16.9546 17.3083 17.1785 17.5323 17.1785 17.8092V19.6773C17.1785 19.9543 17.4024 20.1782 17.6794 20.1782H19.5474C19.8244 20.1782 20.0483 19.9543 20.0483 19.6773V17.8092C20.0483 17.5323 19.8244 17.3083 19.5474 17.3083H17.6853C17.4083 17.3083 17.1844 17.0844 17.1844 16.8074V14.9806C17.1844 14.7037 16.9605 14.4797 16.6835 14.4797H13.4011C9.17592 14.4797 5.75214 17.9035 5.75214 22.1287V22.5589C5.75214 26.7841 9.17592 30.2079 13.4011 30.2079H23.867C24.1439 30.2079 24.3679 29.984 24.3679 29.707V27.8802C24.3679 27.6033 24.1439 27.3793 23.867 27.3793H13.4011Z" fill="url(#cai-g1)"/>
  <path d="M52.8772 18.2918C52.4883 18.0738 52.0816 17.9618 51.6573 17.9618C51.1211 17.9618 50.6791 18.1327 50.3255 18.4804C49.972 18.8281 49.6596 19.2583 49.3945 19.7651V24.9096H47.0786V15.6931H49.3945V17.4256C49.7127 16.8775 50.0839 16.4238 50.5141 16.0584C50.9443 15.6931 51.4334 15.5104 51.9815 15.5104C52.3115 15.5104 52.6061 15.5634 52.8772 15.6754V18.286V18.2918Z" fill="#e2e8f0"/>
  <path d="M59.8493 18.2918C59.4604 18.0738 59.0537 17.9618 58.6295 17.9618C58.0932 17.9618 57.6512 18.1327 57.2977 18.4804C56.9441 18.8281 56.6318 19.2583 56.3666 19.7651V24.9096H54.0507V15.6931H56.3666V17.4256C56.6848 16.8775 57.056 16.4238 57.4862 16.0584C57.9164 15.6931 58.4055 15.5104 58.9536 15.5104C59.2836 15.5104 59.5782 15.5634 59.8493 15.6754V18.286V18.2918Z" fill="#e2e8f0"/>
  <path d="M64.6576 15.4631C65.1585 15.4631 65.6594 15.5809 66.1721 15.8108C66.6848 16.0406 67.109 16.3529 67.4508 16.7418V15.6988H69.7667V24.9153H67.4508V23.3655C67.1856 23.8664 66.7967 24.2907 66.284 24.6501C65.7714 25.0096 65.1762 25.1864 64.4985 25.1864C63.756 25.1864 63.0724 24.9978 62.4477 24.6207C61.8231 24.2435 61.3222 23.6955 60.9451 22.9765C60.5679 22.2576 60.3793 21.3914 60.3793 20.366C60.3793 19.3406 60.5679 18.4685 60.9568 17.7377C61.3399 17.007 61.8585 16.4472 62.5067 16.0524C63.1549 15.6575 63.8797 15.4572 64.6694 15.4572L64.6576 15.4631ZM65.1349 17.726C64.6458 17.726 64.2333 17.8497 63.8856 18.0972C63.5379 18.3447 63.2669 18.6747 63.0724 19.0754C62.8779 19.4762 62.7777 19.9063 62.7777 20.3719C62.7777 21.0672 62.9899 21.6565 63.4083 22.1398C63.8267 22.6289 64.3865 22.8705 65.076 22.8705C65.4885 22.8705 65.8774 22.7585 66.2369 22.5405C66.5964 22.3224 66.8851 22.016 67.1149 21.6212C67.3389 21.2264 67.4508 20.749 67.4508 20.1892V18.8751C67.1208 18.5215 66.7673 18.2445 66.3842 18.0383C66.0012 17.832 65.5828 17.726 65.1349 17.726Z" fill="#e2e8f0"/>
  <path d="M44.9755 15.6985V24.915H42.6595V17.6726H41.1804V15.7043H44.9755V15.6985Z" fill="#e2e8f0"/>
  <path d="M43.6255 10.9015C44.0616 10.9015 44.4388 11.0547 44.757 11.3671C45.0752 11.6794 45.2343 12.0447 45.2343 12.469C45.2343 12.8933 45.0752 13.2469 44.757 13.5651C44.4388 13.8833 44.0616 14.0424 43.6255 14.0424C43.1895 14.0424 42.8123 13.8833 42.5059 13.5651C42.1936 13.2469 42.0403 12.8815 42.0403 12.469C42.0403 12.0565 42.1936 11.6735 42.5059 11.3671C42.8182 11.0606 43.1895 10.9015 43.6255 10.9015Z" fill="#5b8ef0"/>
  <path d="M40.0186 24.9032H36.0645C32.7939 24.9032 30.1303 21.8094 30.1303 18.0026C30.1303 14.1957 32.7939 11.102 36.0645 11.102H40.0127V13.5947H36.0645C34.167 13.5947 32.623 15.5688 32.623 17.9967C32.623 20.4245 34.167 22.3987 36.0645 22.3987H40.0186V24.8914V24.9032Z" fill="#e2e8f0"/>
  <path d="M82.164 12.6003L87.8566 24.9165H84.8806L83.9496 22.6359H79.1115L78.1804 24.9165H75.2045L80.897 12.6003H82.1581H82.164ZM81.5452 16.743L80.0131 20.485H83.0774L81.5452 16.743Z" fill="#5b8ef0"/>
  <path d="M95.6827 22.6342V24.9147H89.0237V22.6342H91.0862V14.9675H89.0237V12.6869H95.6827V14.9675H93.6201V22.6342H95.6827Z" fill="#5b8ef0"/>
  <defs>
    <linearGradient id="cai-g0" x1="15.1396" y1="5.28078" x2="38.6818" y2="28.823" gradientUnits="userSpaceOnUse">
      <stop stop-color="#00ffda"/>
      <stop offset="0.9" stop-color="#4068eb"/>
    </linearGradient>
    <linearGradient id="cai-g1" x1="5.82874" y1="14.5917" x2="29.3709" y2="38.1339" gradientUnits="userSpaceOnUse">
      <stop stop-color="#24f0ba"/>
      <stop offset="0.68" stop-color="#4068eb"/>
    </linearGradient>
  </defs>
</svg>"""

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
    .site-header .logo-wrap {{ line-height: 1; }}
    .site-header .sub {{ color: var(--muted); font-size: 0.9rem; margin-top: 0.4rem; }}
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
    <div class="logo-wrap">
      {LOGO_FULL_SVG}
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
