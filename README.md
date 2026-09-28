# fluidsilicon.com

The Fluid Silicon website: 29 pages, built as plain HTML from the sources in `src/` and `content.py`. There is no framework and nothing to install for a normal build. Every page is complete HTML before any JavaScript runs. The script only adds the menus, the device-table filters and form handling.

```
python3 build.py                                  # builds dist/site, plus the one-file preview
python3 tools_check.py                            # links, disclosure guard, page metadata, open placeholders
python3 -m http.server 8000 --directory dist/site # look at it on http://localhost:8000
```

Python 3.9 or later is all the build needs. To show the site to someone before it's live, send `dist/fluid-silicon-preview.html`: it opens in any browser, offline, with every page and the technical brief shown as page images. Its forms say that nothing was sent.

## Publish

**Option A, recommended: GitHub Actions.** Put this folder in the repository that serves fluidsilicon.com. In **Settings > Pages**, set the source to **GitHub Actions**. Every push to `main` then runs `.github/workflows/pages.yml`: build, check, publish `dist/site`. If the check finds a broken link or a disclosure term, nothing is published.

**Option B: publish the built files.** Run the build and copy the contents of `dist/site/` to the root of the branch Pages serves. `CNAME` and `.nojekyll` are already included.

Old addresses still work: `/team/`, `/partners/`, `/resources/`, `/company/pressroom/`, the six `/industries/<slug>/` pages and the three `/jobs/<role>/` pages all redirect to their new homes. Both redirect pages are marked `noindex`.

## Before launch

1. **Fill the placeholders.** `tools_check.py` lists them. On the pages they show as dashed boxes starting "to fill:", so nothing gets published blank by accident. Search `src/pages/` for `{{fill:`.
   - Internships: term, dates, pay, eligibility.
   - Events: the first upcoming event (or remove the row).
   - Job pages: the compensation section was removed while equity and benefits are decided. Several US states require pay ranges in job ads, so add it back before posting.
   - Privacy and terms are filled (September 28, 2026; Fluid Silicon; Commonwealth of Pennsylvania). Have counsel read them before launch.
2. **Legal entity.** Set `LEGAL_ENTITY` in `build.py` (just above `footer_html()`) to the registered name, for example "Fluid Silicon, Inc."
3. **Forms.** Deploy `backend/apps-script/Code.gs` and set both endpoints in `src/assets/js/config.js`. See `backend/apps-script/README.md`. The demo and contact forms share `demoEndpoint`. Until then, applications go to your existing script, and the demo and contact forms offer email plus a copy button.
4. **Numbers and claims.** Each figure is defined once, in `FACTS` and `DEVICES` at the top of `build.py`, and every page reads it from there. Have engineering confirm them: 30–54% margin, < 20 ps, about 1 s per sweep, < 1% LUTs, < 5% flip-flops, < 2% delay, the device table and the "In development" families.
5. **Citations.** The Rydberg et al. (FPGA 2026) quote on the home page and in the brief comes from your deck. Check it against the paper before launch (the publisher's page couldn't be reached from here).
6. **Reply times.** The site promises replies within `replyDays` (demo, now 2 business days) and the apply-page placeholder. Set numbers the team can keep.

## Site structure

The structure follows the reference the team chose (a solutions company site): a mega menu with **Solutions** (by topic and by industry), **Technology**, **Partners**, **Resources** and **Company**, a site search, and "Request a demo".

| Section | Pages |
|---|---|
| Solutions, by topic | Power & Performance · Reliability, Availability, Serviceability · Failure Prediction & Diagnostics · Card Qualification · Fleet Deployment & Operations · Lifecycle & Second Life (`/solutions/<slug>/`, plus `/solutions/`) |
| Solutions, by industry | One page, `/industries/`, with an anchored section per industry (`/industries/#<slug>`); the old per-industry addresses redirect there |
| Technology | `/technology/` (monitoring, integration, characterization, in-field, FAQ), `/technology/security/`, `/technology/devices/` |
| Resources | `/blog/` (technical brief, posts, explainers); `/resources/` redirects there |
| Company | `/company/` (about, team, where we're headed, partners at `#partners`), `/company/news/` (coverage, announcements and the press kit), `/company/events/`, `/contact/` |
| Careers | `/careers/` (top-level menu item) and `/jobs/` (all open roles on one page, anchored; old job addresses redirect) |
| Forms | `/demo/`, `/contact/`, `/apply/` |
| Legal | `/privacy/`, `/terms/` |

The six solution pages and the industries page are generated from `content.py`: solutions share one structure (hero, measured impact, applications, deep dives, industries, resources, FAQ); each industry section has a lead, three figures, four pillars and the solutions that apply. Old addresses (`/why/`, `/platform/…`, `/solutions/data-center/`, `/solutions/aerospace-defense/`, `/team/`) redirect to their new homes.

## Photos

Team headshots are `src/assets/img/team/<slug>.jpg` (square, 480 px); replace the file to change a photo.

The industry tiles and hero bands are drawn scenes (`industry_art()` in `svgparts.py`). To use a stock photo instead, save it as `src/assets/img/photos/<slug>.jpg` (about 1600×1000, JPEG) and rebuild; the build uses the photo wherever that slug's art would appear. Slugs: `board-system-makers`, `data-center-cloud`, `ai-hpc`, `aerospace-defense`, `telecommunications`, `test-measurement`, `careers`, `careers-hero`. Keep the licence for each photo with the file; a photo of a real product or company is a trademark and permission question.

## Edit content

| To change | Edit |
|---|---|
| Solution and industry pages, resources, news, team bios and profile links, why-now figures, benefits, job listings | `content.py` |
| Other page copy | `src/pages/NN-name.html`. Each file starts with a `<!--meta {...} -->` block: path, title, description, nav item. |
| Figures, device table, citations, routes, navigation | Top of `build.py` (`FACTS`, `DEVICES`, `CITES`, `ROUTES`, `NAV`) |
| Search | The index is built at publish time (`search-index.json`); nothing to maintain. |
| Shared blocks, such as the spec strip, device table, call to action and figures | Functions in `build.py`, used in pages as `{{name:arg}}` |
| Icons, the card illustration and the two charts | `svgparts.py`. They're drawn at build time as static SVG. |
| Product screens (the fleet, card and program mockups) | `mock()` in `build.py`. The data on them is illustrative and says so. |
| Colors, type, layout | `src/assets/css/site.css`. Design tokens are at the top. |
| Menus, search, tabs, filters, forms | `src/assets/js/site.js` |
| Form endpoints, contact addresses, reply time | `src/assets/js/config.js` |

To add a page, add a file in `src/pages/`, add its path to `ROUTES` (and `NAV` if it belongs in the menu), and rebuild. The sitemap updates itself.

## Regenerate images and the brief

`python3 tools_assets.py` rebuilds the favicon, app icons, the social share image (`og-image.png`, 1200×630) and the technical brief PDF. `python3 tools_assets.py og` rebuilds only the share image. It needs Playwright with Chromium and Pillow (`pip install playwright pillow`, then `playwright install chromium`).

The brief has its own frozen sources, `brief_parts.py` and `src/assets/css/brief.css`, so redesigning the site does not change the PDF. Run the full command after changing the numbers or the device table, so the PDF stays in step with the site.

`tools_logo.py` rebuilds the logo SVGs. The wordmark is outlined from Carlito Bold, which is metric-compatible with the typeface in the original logo, and needs `fontTools`. Colors are parameters, so other colorways of the IC-package mark are one call each.

## What the site says, and what it keeps back

The site says what the platform measures, what it changes, how it fits a production system, and what it costs in area, delay and downtime. It doesn't say how the sensing works. Sensor architecture, deployment mechanics and calibration are shared with evaluation partners under NDA, and the site says exactly that where someone would ask.

`tools_check.py` guards this before every publish. It fails if page text or the technical brief uses a term from your disclosure list, or names a person or personal role. The site speaks as a company. The disclosure list itself names what must stay private, so it is never stored in this repository. It was delivered separately as `fluid-silicon-guard-terms.txt`:

- **In GitHub Actions:** add a repository secret named `FS_GUARD_TERMS` and paste the file's lines into it. The workflow passes it to the check.
- **On your computer:** save the file as `.guard-terms` next to `tools_check.py`. `.gitignore` keeps it out of commits made with git. Don't upload it through the GitHub website, which ignores `.gitignore`.

Without the list the check still runs the link and people checks, and says the disclosure guard is not configured.

## Design and accessibility

- Light pages with a charcoal hero and footer. Gold for labels and accents, one orange for the primary action, green, amber and red only for status. Red Hat Display for headings, Red Hat Text for everything else, both self-hosted.
- No animation. Product screens are static mockups, the hardware illustration, the industry scenes and the charts are static SVG, and hover states are the only motion.
- Charts and the illustration have text alternatives; wide charts and tables scroll sideways and can be reached from the keyboard.
- Forms report errors next to each field and in a live region, and never fail silently.
- Text and status colors meet 4.5:1 against their backgrounds (checked with axe on every page at phone, tablet and desktop widths).

## Folder map

```
build.py            site builder (pages, shared blocks, templates, search index, sitemap, redirects, preview)
content.py          solutions, industries, resources, news, careers content
svgparts.py         icons, card illustration, industry scenes, thumbnails and charts, drawn at build time
brief_parts.py      frozen diagrams for the technical brief (with src/assets/css/brief.css)
tools_check.py      pre-publish checks
tools_assets.py     icons, share image, technical brief PDF
tools_logo.py       logo SVGs
src/pages/          page sources
src/assets/         css, js, fonts (self-hosted Red Hat), images, the brief
src/CNAME …         files copied to the site root as-is
backend/apps-script Google Apps Script for the forms, with offline tests
dist/site/          the built site: this is what gets published
dist/fluid-silicon-preview.html   every page in one self-contained file, to open locally or send privately
dist/preview/       the same preview as separate files (used to build the one-file version)
```
