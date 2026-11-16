# n8n Automation Demos

Three small, sellable automation demos for small businesses — built by
**Waleed Shamhan** (IT student, Yemen) as Week 1 of an independent digital
business. Goal: first $50/month, no social media.

> **Verified, not promised:** n8n 2.47.4 is installed locally and all three
> workflow files imported into it cleanly (`n8n import:workflow` —
> "Successfully imported 3 workflows"). Demo 3 runs end-to-end on any
> machine (see `excel-to-report/output/`). Demos 1–2 need the owner's own
> Google Sheets / Gmail OAuth connection — see `SETUP.md` for the
> 5-minute setup. The live webhook test still needs the owner to activate
> the test workflow in the n8n editor (see `SETUP.md`).

## The three demos

| # | Demo | What it does | Price |
|---|------|--------------|-------|
| 1 | **Lead Capture** | Web form → clean data → Google Sheets → email notification | $50 base / $80 with docs + video |
| 2 | **Inbox Triage** | Gmail → rule-based classification → Sheets log → draft reply | $50 base / $80 with docs + video |
| 3 | **Excel to Report** | Scattered xlsx/csv files → one clean `report.xlsx` + `summary.txt` | $20–40 per job |

## Quick start

**Demo 3 (runs now, no accounts needed):**
```bash
cd excel-to-report
python3 make_demo_inputs.py   # creates 3 sample input files
python3 excel-to-report.py    # merges them into output/report.xlsx
```

**Demos 1–2 (n8n):**
1. Run n8n (self-hosted, free): `npx n8n` then open http://localhost:5678
2. Workflows → Import from File → pick `lead-capture-workflow.json`
3. Connect your Google Sheets + Gmail accounts (OAuth2, in n8n → Credentials)
4. Replace the `REPLACE_WITH_…` placeholders, activate, test with the
   Production form URL.

**Local test, no Google account:**
`lead-capture-test-workflow.json` is a Webhook version of Demo 1.
Import it, activate it in the editor, then:
```bash
curl -X POST http://localhost:5678/webhook/lead-capture \
  -H 'Content-Type: application/json' \
  -d '{"name":"Test User","phone":"771 123 456","business":"Shop","message":"Hello"}'
```

## Files

- `lead-capture-workflow.json` — Demo 1 (Form → Set → Sheets → Gmail)
- `inbox-triage-workflow.json` — Demo 2 (Gmail Trigger → Code → Sheets → Gmail)
- `lead-capture-test-workflow.json` — Demo 1, webhook test version
- `excel-to-report/` — Demo 3 (script + demo inputs + verified output)
- `demo-scripts.md` — 3 demo video scripts (60–90s each, Arabic)
- `video/` — Demo 1 video: animated explainer (32s, silent) + build script
- `showcase/` — one-page showcase site (`index.html`, RTL Arabic)
- `SETUP.md` — full setup guide for both n8n workflows

## Notes

- The `.xlsx` files under `excel-to-report/input/` and `output/` are
  generated demo data. The connector used to publish this repo only pushes
  text files, so binaries may be absent from some mirrors — regenerate them
  anytime with `python3 make_demo_inputs.py && python3 excel-to-report.py`.
- **No credentials, tokens, API keys or passwords — ever.**
- No client data. All demo data is fictional.
- Inbox Triage ships with auto-reply **disabled**: drafts are reviewed first.
  Nothing is ever sent to a client's customers without their explicit approval.

## Contact

- Mostaql: https://mostaql.com/u/waleed_shamhan
- Showcase: `showcase/index.html`
