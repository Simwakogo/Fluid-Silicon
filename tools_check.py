#!/usr/bin/env python3
"""Pre-publish checks for dist/site. Run after build.py:   python3 tools_check.py

  1. Internal links and #anchors resolve to real files and ids.
  2. No page text uses a term from the private disclosure list, or names people or personal roles.
  3. Every page has one h1, a title, a description and a canonical URL.
  4. Lists the placeholders still waiting for real content.

Exits 1 if 1 or 2 find anything. The disclosure list itself is private; see load_guard_terms().
"""
import html, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, "dist", "site")

# The disclosure list is private: it names the very things the site must not say, so it never lives in this
# repository. It comes from the FS_GUARD_TERMS environment variable (a GitHub Actions secret in CI) or from a
# local .guard-terms file next to this script. One regular expression per line; lines starting with # are notes.
def load_guard_terms():
    raw = os.environ.get("FS_GUARD_TERMS", "")
    local = os.path.join(ROOT, ".guard-terms")
    if not raw.strip() and os.path.exists(local):
        raw = open(local, encoding="utf-8").read()
    return [ln.strip() for ln in raw.splitlines() if ln.strip() and not ln.strip().startswith("#")]


# The site speaks as a company. The team appears only in the team sections (home and company pages, marked
# data-people="allowed"); elsewhere page text names no people and no personal roles.
ROLE_TERMS = [r"\bfounders?\b", r"co-founder", r"\bCEO\b", r"\bCTO\b", r"\badvisors?\b"]


def text_of(page_html):
    s = re.sub(r"<(script|style)\b.*?</\1>", " ", page_html, flags=re.S | re.I)
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s))


def resolve(path):
    path = path.split("#")[0].split("?")[0]
    full = os.path.join(SITE, path.lstrip("/"))
    if path.endswith("/"):
        full = os.path.join(full, "index.html")
    return full if os.path.exists(full) else None


def main():
    pages = {}
    for d, _, files in os.walk(SITE):
        for f in files:
            if f.endswith(".html"):
                p = os.path.join(d, f)
                pages[p] = open(p, encoding="utf-8").read()
    problems, notes, fills = [], [], []
    IP_TERMS = load_guard_terms()
    PEOPLE_TERMS = ROLE_TERMS
    if not IP_TERMS:
        notes.append("disclosure guard skipped: set FS_GUARD_TERMS or add a private .guard-terms file (see README)")
    ids = {p: set(re.findall(r'\bid="([^"]+)"', s)) for p, s in pages.items()}
    for p, s in pages.items():
        rel = "/" + os.path.relpath(p, SITE)
        redirect = 'http-equiv="refresh"' in s
        for attr, url in re.findall(r'\b(href|src)="([^"]+)"', s):
            if url.startswith(("http://", "https://", "mailto:", "tel:", "data:")) or url in ("#", ""):
                continue
            if url.startswith("#"):
                if url[1:] not in ids[p]:
                    problems.append(f"{rel}: anchor {url} has no matching id")
                continue
            target = resolve(url)
            if not target:
                problems.append(f"{rel}: broken link {url}")
            elif "#" in url and target.endswith(".html") and url.split("#")[1] not in ids.get(target, set()):
                problems.append(f"{rel}: {url} points at a missing id")
        if redirect:
            continue
        text = text_of(s)
        people_text = text_of(re.sub(r'<section[^>]*data-people="allowed".*?</section>', " ", s, flags=re.S))
        for pat in IP_TERMS:
            for m in re.finditer(pat, text, re.I):
                problems.append(f"{rel}: disclosure-list term '{m.group(0)}' in: …{text[max(0, m.start()-60):m.end()+60]}…")
        for pat in PEOPLE_TERMS:
            for m in re.finditer(pat, people_text, re.I):
                problems.append(f"{rel}: names a person or role '{m.group(0)}' in: …{people_text[max(0, m.start()-60):m.end()+60]}…")
        if len(re.findall(r"<h1\b", s)) != 1:
            notes.append(f"{rel}: expected exactly one h1")
        for need, pat in [("title", r"<title>[^<]+</title>"), ("description", r'<meta name="description" content="[^"]+'), ("canonical", r'<link rel="canonical"')]:
            if not re.search(pat, s):
                notes.append(f"{rel}: missing {need}")
        for key in re.findall(r'data-fill="([^"]+)"', s):
            fills.append(f"{rel}: {key}")
    # the technical brief goes through the same guard
    pdf = os.path.join(SITE, "assets", "docs", "fluid-silicon-technical-brief.pdf")
    if os.path.exists(pdf):
        try:
            t = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True, check=True).stdout
            t = re.sub(r"\s+", " ", t)
            for pat in IP_TERMS + PEOPLE_TERMS:
                for m in re.finditer(pat, t, re.I):
                    problems.append(f"technical brief PDF: '{m.group(0)}'")
        except (OSError, subprocess.CalledProcessError):
            notes.append("pdftotext not available: technical brief not scanned")
    print(f"checked {len(pages)} HTML files")
    for n in notes:
        print("note:", n)
    if fills:
        print(f"{len(fills)} placeholders still to fill:")
        for f in fills:
            print("  ", f)
    if problems:
        print(f"{len(problems)} problems:")
        for pr in problems:
            print("  ", pr)
        sys.exit(1)
    print("links, disclosure guard and people check: clean" if IP_TERMS else "links and people check: clean (disclosure guard not configured)")


if __name__ == "__main__":
    main()
