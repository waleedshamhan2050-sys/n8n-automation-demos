# Week 1 Demos — n8n Automation Demos (Waleed Shamhan)

Three sellable demos, built in Week 1 of the Independent Digital Business plan.
Goal: first $50/month, no social media. Prices are the approved prices.

| Demo | What it does | Price |
|---|---|---|
| 1. Lead Capture | Web form → clean data → Google Sheets → email notification | $50 base / $80 with docs + video |
| 2. Inbox Triage | Gmail → rule-based classification → Sheets log → reply (draft by default) | $50 base / $80 with docs + video |
| 3. Excel to Report | Scattered xlsx/csv files → one clean report.xlsx + summary.txt | $20–40 per job |

## How to use these workflows (owner steps — needs the user)

Both `.json` files import directly into n8n: **Workflows → ⋯ → Import from File**.

### Lead Capture — `lead-capture-workflow.json`
Nodes: Form Trigger → Clean Data (Set) → Save to Sheets → Notify by Email.
1. Create a Google Sheet named `Leads - Demo` with header row:
   `Timestamp | Name | Phone | Business | Message`
2. In n8n: **Credentials → Google Sheets OAuth2** → connect your Google account
   (OAuth2 only — never paste a password or an app password anywhere).
3. In n8n: **Credentials → Gmail OAuth2** → connect the same / your Gmail account.
4. Open the imported workflow, click **Save to Sheets** → set Document to your
   `Leads - Demo` sheet (replace `REPLACE_WITH_SHEET_ID`).
5. Click **Notify by Email** → set Send To to your email
   (replace `REPLACE_WITH_OWNER_EMAIL`).
6. Save, click **Active**, open the form's **Production** URL (not the Test URL),
   submit a test entry, and check: a new row in Sheets + an email in your inbox.
   n8n's **Executions** page shows exactly which node failed, if any.

### Inbox Triage — `inbox-triage-workflow.json`
Nodes: Gmail Trigger → Classify Email (Code) → Log to Sheets → Send Reply.
1. Create a Google Sheet with header row:
   `Timestamp | From | Subject | Category | Draft Reply`
2. Connect Google Sheets + Gmail OAuth2 as above.
3. The classifier is rule-based (keywords in subject + body, Arabic + English):
   `urgent` (urgent/complaint/refund/مشكلة/شكوى/عاجل) → `sales`
   (price/quote/order/سعر/طلب/شراء) → `support` (help/how/دعم/مساعدة/كيف)
   → otherwise `general`. Each category has a ready draft reply.
4. **IMPORTANT — the "Send Reply" node ships DISABLED on purpose.**
   For a real client, first run it with only the Sheets log active for a week,
   review the drafts, then enable sending — or switch the Gmail node to the
   "create draft" operation so a human approves every reply. Never auto-send
   to a client's customers without their explicit approval.
5. The Gmail Trigger polls every minute; for a client, switch it to every
   5–15 minutes to save executions.

## Local test (no Google account needed)
`lead-capture-test-workflow.json` is a Webhook version of Demo 1:
Webhook Trigger → Clean Data → Respond to Webhook. Import it, activate it,
then run:
```bash
curl -X POST http://localhost:5678/webhook-test/lead-capture \
  -H 'Content-Type: application/json' \
  -d '{"name":"Test User","phone":"771 123 456","business":"Shop","message":"Hello"}'
```
You should get back the cleaned row as JSON. That proves the trigger +
cleaning chain works end-to-end on this machine; the Sheets/Gmail nodes are
the only part that needs the owner's OAuth.

## What is NOT in this repo
- No credentials, no tokens, no API keys, no passwords — ever.
- No client data. All demo data is fictional test data.

## Files
- `lead-capture-workflow.json` — Demo 1 (production shape)
- `inbox-triage-workflow.json` — Demo 2 (production shape)
- `lead-capture-test-workflow.json` — Demo 1 test version (webhook, local)
- `excel-to-report/` — Demo 3 (Python script + demo inputs + verified output)
- `demo-scripts.md` — 3 demo video scripts (60–90s, Arabic, masculine)
- `showcase/` — one-page showcase site (RTL HTML)
