#!/usr/bin/env python3
"""LWC Audit Scoring Script - Decodes base64 sources and scores components."""
import base64
import json
import os
import re
import sys

# Scoring rubric categories and max points
MAX_SCORES = {
    "sldsUsage": 25,
    "accessibility": 25,
    "darkModeReadiness": 25,
    "sldsMigration": 20,
    "stylingHooks": 20,
    "componentStructure": 15,
    "performance": 10,
    "picklesCompliance": 25,
}
TOTAL_MAX = 165


def decode_b64(s):
    """Decode base64 string, return empty string on failure."""
    try:
        return base64.b64decode(s).decode("utf-8", errors="replace")
    except Exception:
        return ""


def extract_files(component_result):
    """Extract decoded files from a component metadata result."""
    files = {}
    resources = component_result.get("lwcResources", {}).get("lwcResource", [])
    for r in resources:
        path = r.get("filePath", "")
        source = decode_b64(r.get("source", ""))
        files[path] = source
    return files


def score_slds_usage(html, css, js):
    """Score SLDS class usage (25 pts)."""
    score = 0
    issues = []
    all_text = html + css

    # Check for slds-* class usage
    slds_classes = re.findall(r'slds-[\w-]+', all_text)
    if slds_classes:
        unique = set(slds_classes)
        if len(unique) >= 5:
            score += 15
        elif len(unique) >= 2:
            score += 10
        elif len(unique) >= 1:
            score += 5
        # Check for proper utility classes
        utilities = [c for c in unique if any(u in c for u in ['slds-m-', 'slds-p-', 'slds-grid', 'slds-col', 'slds-text-', 'slds-align'])]
        if utilities:
            score += 5
        else:
            issues.append("No SLDS utility classes found")
        # Validate common patterns
        valid_prefixes = ['slds-', 'slds-m-', 'slds-p-', 'slds-grid', 'slds-form', 'slds-card', 'slds-modal', 'slds-notify', 'slds-box', 'slds-button']
        has_valid = any(any(c.startswith(p) for p in valid_prefixes) for c in unique)
        if has_valid:
            score += 5
    else:
        issues.append("No SLDS classes used")

    return min(score, 25), issues


def score_accessibility(html, js):
    """Score accessibility (25 pts)."""
    score = 0
    issues = []

    # ARIA labels
    aria_patterns = re.findall(r'aria-[\w-]+', html)
    if aria_patterns:
        score += 7
    else:
        issues.append("No ARIA attributes found")

    # Role attributes
    if 'role=' in html:
        score += 5
    else:
        issues.append("No role attributes found")

    # Alt text for images
    if '<img' in html:
        if 'alt=' in html:
            score += 4
        else:
            issues.append("Images without alt text")
    else:
        score += 4  # No images, no issue

    # Keyboard navigation
    if any(k in html + js for k in ['onkeydown', 'onkeyup', 'onkeypress', 'tabindex', 'handleKeyDown', 'handleKey']):
        score += 5
    else:
        issues.append("No keyboard navigation handlers")

    # Labels for inputs
    if '<label' in html or 'label=' in html or 'lightning-input' in html:
        score += 4
    else:
        if '<input' in html:
            issues.append("Input elements without labels")
        else:
            score += 4

    return min(score, 25), issues


def score_dark_mode(css, html):
    """Score dark mode readiness (25 pts)."""
    score = 25
    issues = []

    if not css.strip():
        return 20, ["No CSS file - default score"]

    # Check for hardcoded colors
    hardcoded_colors = re.findall(r'(?:color|background|border)(?:-color)?:\s*#[0-9a-fA-F]{3,8}', css)
    re.findall(r'#[0-9a-fA-F]{3,8}', css)
    rgb_colors = re.findall(r'rgb\(', css)
    named_colors = re.findall(r':\s*(?:red|blue|green|white|black|gray|grey|yellow|orange|purple|pink)\s*[;}]', css, re.IGNORECASE)

    total_hardcoded = len(hardcoded_colors) + len(rgb_colors) + len(named_colors)
    if total_hardcoded > 5:
        score -= 15
        issues.append(f"{total_hardcoded} hardcoded color values found")
    elif total_hardcoded > 2:
        score -= 10
        issues.append(f"{total_hardcoded} hardcoded color values found")
    elif total_hardcoded > 0:
        score -= 5
        issues.append(f"{total_hardcoded} hardcoded color values found")

    # Check for CSS variables usage
    css_vars = re.findall(r'var\(--', css)
    if not css_vars and total_hardcoded > 0:
        score -= 5
        issues.append("No CSS custom properties used")

    # Check for hardcoded colors in HTML style attributes
    style_attrs = re.findall(r'style="[^"]*(?:color|background)[^"]*#[0-9a-fA-F]+[^"]*"', html)
    if style_attrs:
        score -= 5
        issues.append("Hardcoded colors in inline styles")

    return max(score, 0), issues


def score_slds_migration(html, css, js):
    """Score SLDS migration - no deprecated SLDS 1 patterns (20 pts)."""
    score = 20
    issues = []

    # Deprecated SLDS 1 tokens/patterns
    deprecated_patterns = [
        (r'--lwc-', "Deprecated --lwc- token prefix found"),
        (r'slds-size--', "Deprecated slds-size-- pattern (use slds-size_)"),
        (r'slds-theme--', "Deprecated slds-theme-- pattern (use slds-theme_)"),
        (r'slds-[\w]*--[\w]', "Deprecated double-dash BEM modifier (use single underscore)"),
        (r'\.slds-(?:is-)?deprecated', "Deprecated SLDS class used"),
    ]
    all_text = html + css + js
    for pattern, msg in deprecated_patterns:
        matches = re.findall(pattern, all_text)
        if matches:
            score -= 4
            issues.append(f"{msg} ({len(matches)} occurrences)")

    # Check for old token references
    old_tokens = re.findall(r'--lwc-[\w]+', css)
    if old_tokens:
        score -= min(len(old_tokens), 4)
        issues.append(f"{len(old_tokens)} deprecated --lwc- tokens")

    return max(score, 0), issues


def score_styling_hooks(css):
    """Score styling hooks usage (20 pts)."""
    score = 5  # Base score
    issues = []

    if not css.strip():
        return 10, ["No CSS file - partial score"]

    # Check for --slds-g-* variables
    slds_g_vars = re.findall(r'--slds-g-[\w-]+', css)
    if slds_g_vars:
        score += 10
        if len(set(slds_g_vars)) >= 3:
            score += 5
    else:
        issues.append("No --slds-g-* styling hooks used")

    # Check for --slds-c-* component hooks
    slds_c_vars = re.findall(r'--slds-c-[\w-]+', css)
    if slds_c_vars:
        score += 5

    # Check for --lwc- vars (old but acceptable)
    lwc_vars = re.findall(r'--lwc-[\w]+', css)
    if lwc_vars and not slds_g_vars:
        score += 3
        issues.append("Using --lwc- vars instead of --slds-g-* hooks")

    # Any var() usage at all
    any_vars = re.findall(r'var\(', css)
    if any_vars and score < 10:
        score = max(score, 8)

    return min(score, 20), issues


def score_component_structure(html, js):
    """Score component structure (15 pts)."""
    score = 0
    issues = []

    # Uses lightning-* base components
    lightning_components = re.findall(r'<lightning-[\w-]+', html)
    if lightning_components:
        unique = set(lightning_components)
        if len(unique) >= 3:
            score += 10
        elif len(unique) >= 1:
            score += 6
    else:
        issues.append("No lightning-* base components used")

    # Proper LWC patterns in JS
    if 'LightningElement' in js:
        score += 3
    if '@api' in js:
        score += 2
    elif 'export default' in js:
        score += 1

    return min(score, 15), issues


def score_performance(css, js, html):
    """Score performance (10 pts)."""
    score = 10
    issues = []

    # Check for !important
    important_count = len(re.findall(r'!important', css))
    if important_count > 3:
        score -= 4
        issues.append(f"{important_count} !important declarations")
    elif important_count > 0:
        score -= 2
        issues.append(f"{important_count} !important declarations")

    # Check for deep nesting selectors
    deep_selectors = re.findall(r'[\w.-]+\s+[\w.-]+\s+[\w.-]+\s+[\w.-]+\s+[\w.-]+', css)
    if deep_selectors:
        score -= 2
        issues.append("Deeply nested CSS selectors")

    # Check for universal selectors
    if re.search(r'[^a-zA-Z]\*\s*\{', css):
        score -= 2
        issues.append("Universal selector (*) used")

    # Check for inefficient DOM queries in JS
    if 'querySelectorAll' in js:
        score -= 1
        issues.append("querySelectorAll usage (prefer template refs)")

    return max(score, 0), issues


def score_pickles(html, css, js, meta_xml, files):
    """Score PICKLES compliance (25 pts)."""
    score = 0
    issues = []

    # P - Progressive Enhancement
    if 'if:true' in html or 'if:false' in html or 'lwc:if' in html:
        score += 3
    else:
        issues.append("No conditional rendering")

    # I - Isolation (component encapsulation)
    if ':host' in css or not css.strip():
        score += 3
    else:
        score += 1
        issues.append("No :host selector for style encapsulation")

    # C - Composition (uses child components)
    child_components = re.findall(r'<c-[\w-]+', html) + re.findall(r'<lightning-[\w-]+', html)
    if child_components:
        score += 4
    else:
        issues.append("No component composition")

    # K - Knowledge sharing (documentation/comments)
    if '/**' in js or '//' in js or '<!--' in html:
        score += 3
    else:
        issues.append("No code documentation")

    # L - Lifecycle awareness
    lifecycle_hooks = ['connectedCallback', 'disconnectedCallback', 'renderedCallback', 'errorCallback']
    if any(hook in js for hook in lifecycle_hooks):
        score += 3
    else:
        issues.append("No lifecycle hooks implemented")

    # E - Event-driven architecture
    if 'dispatchEvent' in js or 'CustomEvent' in js or '@wire' in js:
        score += 4
    else:
        issues.append("No event-driven patterns")

    # S - Separation of concerns (meta.xml targets)
    if 'lightning__FlowScreen' in meta_xml or 'lightning__RecordPage' in meta_xml or 'lightning__AppPage' in meta_xml:
        score += 3
    elif 'isExposed>true' in meta_xml:
        score += 2
    else:
        score += 1

    # API version freshness
    api_match = re.search(r'<apiVersion>([\d.]+)</apiVersion>', meta_xml)
    if api_match:
        api_ver = float(api_match.group(1))
        if api_ver >= 58:
            score += 2
        elif api_ver >= 50:
            score += 1
        else:
            issues.append(f"Old API version {api_ver}")

    return min(score, 25), issues


def score_component(name, files, api_version):
    """Score a single component against all rubric categories."""
    html = ""
    css = ""
    js = ""
    meta_xml = ""

    for path, content in files.items():
        if path.endswith('.html'):
            html += content
        elif path.endswith('.css'):
            css += content
        elif path.endswith('.js-meta.xml'):
            meta_xml += content
        elif path.endswith('.js'):
            js += content

    categories = {}
    all_issues = []

    s, i = score_slds_usage(html, css, js)
    categories["sldsUsage"] = s
    all_issues.extend(i)

    s, i = score_accessibility(html, js)
    categories["accessibility"] = s
    all_issues.extend(i)

    s, i = score_dark_mode(css, html)
    categories["darkModeReadiness"] = s
    all_issues.extend(i)

    s, i = score_slds_migration(html, css, js)
    categories["sldsMigration"] = s
    all_issues.extend(i)

    s, i = score_styling_hooks(css)
    categories["stylingHooks"] = s
    all_issues.extend(i)

    s, i = score_component_structure(html, js)
    categories["componentStructure"] = s
    all_issues.extend(i)

    s, i = score_performance(css, js, html)
    categories["performance"] = s
    all_issues.extend(i)

    s, i = score_pickles(html, css, js, meta_xml, files)
    categories["picklesCompliance"] = s
    all_issues.extend(i)

    total = sum(categories.values())
    pct = round(total / TOTAL_MAX * 100)

    return {
        "name": name,
        "score": total,
        "maxScore": TOTAL_MAX,
        "pct": pct,
        "apiVersion": api_version,
        "issues": all_issues[:10],  # Top 10 issues
        "categories": categories,
    }


def process_metadata_results(results_list):
    """Process a list of metadata_read results."""
    components = []
    for result in results_list:
        name = result.get("fullName", "unknown")
        api_version = result.get("apiVersion", 0)
        files = extract_files(result)

        # Write files to disk
        comp_dir = f"/home/user/skills/audit_output/intermediate/lwc/{name}"
        os.makedirs(comp_dir, exist_ok=True)
        for path, content in files.items():
            filename = os.path.basename(path)
            filepath = os.path.join(comp_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

        # Score component
        scored = score_component(name, files, api_version)
        components.append(scored)

    return components


def main():
    """Main entry point - reads all metadata JSON files and scores them."""
    all_scored = []

    # Read metadata from JSON files passed as arguments or from stdin
    if len(sys.argv) > 1:
        for filepath in sys.argv[1:]:
            with open(filepath) as f:
                data = json.load(f)
            if isinstance(data, list):
                # Array of results
                for item in data:
                    if "text" in item:
                        parsed = json.loads(item["text"])
                        results = parsed.get("results", [])
                        all_scored.extend(process_metadata_results(results))
                    elif "results" in item:
                        all_scored.extend(process_metadata_results(item["results"]))
            elif "results" in data:
                all_scored.extend(process_metadata_results(data["results"]))
    else:
        # Read from stdin
        data = json.load(sys.stdin)
        if "results" in data:
            all_scored.extend(process_metadata_results(data["results"]))

    # Output JSON
    print(json.dumps(all_scored, indent=2))


if __name__ == "__main__":
    main()
