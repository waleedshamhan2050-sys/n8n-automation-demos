#!/usr/bin/env python3
"""Generate the two n8n workflow JSON files (valid n8n import format).
Writes lead-capture-workflow.json and inbox-triage-workflow.json.
Node types/versions match n8n (npm) current releases; credentials are
placeholders — the owner links their own Google/Gmail OAuth in the UI.
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
N8N = "n8n-nodes-base."

def node(nid, name, ntype, version, pos, params=None, creds=None, disabled=False):
    n = {"id": nid, "name": name, "type": N8N + ntype,
         "typeVersion": version, "position": list(pos), "parameters": params or {}}
    if creds:
        n["credentials"] = creds
    if disabled:
        n["disabled"] = True
    return n

# ---------------------------------------------------------------- lead capture
lead = {
    "name": "Lead Capture — Form to Sheets + Email",
    "nodes": [
        node("a1-form-trigger", "Form Trigger", "formTrigger", 2.2, [0, 0], {
            "formTitle": "Contact Form",
            "formDescription": "Leave your details and we will call you back.",
            "formFields": {"values": [
                {"fieldLabel": "Name", "fieldType": "text", "requiredField": True},
                {"fieldLabel": "Phone", "fieldType": "text", "requiredField": True},
                {"fieldLabel": "Business", "fieldType": "dropdown", "requiredField": True,
                 "fieldOptions": [{"option": "Restaurant"}, {"option": "Clinic"},
                                  {"option": "Shop"}, {"option": "Services"}]},
                {"fieldLabel": "Message", "fieldType": "textarea"},
            ]},
            "options": {"formSubmissionText": "Thank you! We received your message."},
        }),
        node("a2-clean", "Clean Data", "set", 3.4, [240, 0], {
            "mode": "manual",
            "assignments": {"assignments": [
                {"id": "s1", "name": "name", "type": "string",
                 "value": "={{ $json.Name.trim() }}"},
                {"id": "s2", "name": "phone", "type": "string",
                 "value": "={{ $json.Phone.trim().replaceAll(' ', '') }}"},
                {"id": "s3", "name": "business", "type": "string",
                 "value": "={{ $json.Business }}"},
                {"id": "s4", "name": "message", "type": "string",
                 "value": "={{ $json.Message }}"},
            ]},
            "options": {},
        }),
        node("a3-sheets", "Save to Sheets", "googleSheets", 4.2, [480, 0], {
            "operation": "append",
            "documentId": {"__rl": True, "value": "REPLACE_WITH_SHEET_ID", "mode": "url"},
            "sheetName": {"__rl": True, "value": "Sheet1", "mode": "list", "cachedResultName": "Sheet1"},
            "columns": {"mappingMode": "defineBelow", "value": {
                "Timestamp": "={{ $now.toISO() }}",
                "Name": "={{ $json.name }}",
                "Phone": "={{ $json.phone }}",
                "Business": "={{ $json.business }}",
                "Message": "={{ $json.message }}",
            }, "matchingColumns": ["Timestamp", "Name", "Phone", "Business", "Message"]},
            "options": {},
        }, creds={"googleSheetsOAuth2": {"id": None, "name": "Google Sheets account"}}),
        node("a4-gmail", "Notify by Email", "gmail", 2.1, [720, 0], {
            "resource": "message",
            "operation": "send",
            "sendTo": "REPLACE_WITH_OWNER_EMAIL",
            "subject": "=New lead: {{ $('Clean Data').item.json.name }} — {{ $('Clean Data').item.json.business }}",
            "emailBody": "=New lead from your website form:\n\nName: {{ $('Clean Data').item.json.name }}\nPhone/WhatsApp: {{ $('Clean Data').item.json.phone }}\nBusiness type: {{ $('Clean Data').item.json.business }}\nMessage: {{ $('Clean Data').item.json.message }}\n\nSaved automatically to Google Sheets.",
            "options": {},
        }, creds={"gmailOAuth2": {"id": None, "name": "Gmail account"}}),
    ],
    "connections": {
        "Form Trigger": {"main": [[{"node": "Clean Data", "type": "main", "index": 0}]]},
        "Clean Data": {"main": [[{"node": "Save to Sheets", "type": "main", "index": 0}]]},
        "Save to Sheets": {"main": [[{"node": "Notify by Email", "type": "main", "index": 0}]]},
    },
    "active": False,
    "settings": {"executionOrder": "v1"},
    "pinData": {},
}

# ---------------------------------------------------------------- inbox triage
triage = {
    "name": "Inbox Triage — Classify Gmail + Log to Sheets",
    "nodes": [
        node("b1-gmail-trigger", "Gmail Trigger", "gmailTrigger", 1.2, [0, 0], {
            "pollTimes": {"item": [{"mode": "everyMinute"}]},
            "filters": {},
            "options": {"downloadAttachments": False},
        }, creds={"gmailOAuth2": {"id": None, "name": "Gmail account"}}),
        node("b2-classify", "Classify Email", "code", 2, [240, 0], {
            "mode": "runOnceForEachItem",
            "jsCode": (
                "const subject = ($json.subject || '').toLowerCase();\n"
                "const body = (($json.snippet || '') + ' ' + ($json.text || '')).toLowerCase();\n"
                "const text = subject + ' ' + body;\n"
                "let category = 'general';\n"
                "if (/urgent|complaint|refund|angry|مشكلة|شكوى|عاجل/.test(text)) category = 'urgent';\n"
                "else if (/price|quote|order|buy|سعر|طلب|شراء/.test(text)) category = 'sales';\n"
                "else if (/help|how|support|دعم|مساعدة|كيف/.test(text)) category = 'support';\n"
                "const replies = {\n"
                "  urgent: 'Thank you for writing — we have flagged your message as urgent and a team member will reply within 2 hours.',\n"
                "  sales: 'Thank you for your interest! Here is our price list — tell us which option suits you and we will prepare an offer.',\n"
                "  support: 'Thank you for reaching out. Could you share a screenshot or the exact steps? We will guide you from there.',\n"
                "  general: 'Thank you for your message. We have received it and will reply within one working day.',\n"
                "};\n"
                "return [{ json: { from: $json.from?.value || $json.from || '', subject: $json.subject || '',\n"
                "  snippet: $json.snippet || '', category, draftReply: replies[category], receivedAt: $now.toISO() } }];"
            ),
        }),
        node("b3-sheets", "Log to Sheets", "googleSheets", 4.2, [480, 0], {
            "operation": "append",
            "documentId": {"__rl": True, "value": "REPLACE_WITH_SHEET_ID", "mode": "url"},
            "sheetName": {"__rl": True, "value": "Sheet1", "mode": "list", "cachedResultName": "Sheet1"},
            "columns": {"mappingMode": "defineBelow", "value": {
                "Timestamp": "={{ $json.receivedAt }}",
                "From": "={{ $json.from }}",
                "Subject": "={{ $json.subject }}",
                "Category": "={{ $json.category }}",
                "Draft Reply": "={{ $json.draftReply }}",
            }, "matchingColumns": ["Timestamp", "From", "Subject", "Category", "Draft Reply"]},
            "options": {},
        }, creds={"googleSheetsOAuth2": {"id": None, "name": "Google Sheets account"}}),
        node("b4-gmail", "Send Reply", "gmail", 2.1, [720, 0], {
            "resource": "message",
            "operation": "send",
            "sendTo": "={{ $('Classify Email').item.json.from }}",
            "subject": "=Re: {{ $('Classify Email').item.json.subject }}",
            "emailBody": "=Hi,\n\n{{ $('Classify Email').item.json.draftReply }}\n\nBest regards",
            "options": {},
        }, creds={"gmailOAuth2": {"id": None, "name": "Gmail account"}}, disabled=True),
    ],
    "connections": {
        "Gmail Trigger": {"main": [[{"node": "Classify Email", "type": "main", "index": 0}]]},
        "Classify Email": {"main": [[{"node": "Log to Sheets", "type": "main", "index": 0}]]},
        "Log to Sheets": {"main": [[{"node": "Send Reply", "type": "main", "index": 0}]]},
    },
    "active": False,
    "settings": {"executionOrder": "v1"},
    "pinData": {},
}

for name, wf in (("lead-capture-workflow.json", lead), ("inbox-triage-workflow.json", triage)):
    p = OUT / name
    p.write_text(json.dumps(wf, indent=2, ensure_ascii=False), encoding="utf-8")
    json.loads(p.read_text(encoding="utf-8"))  # validate
    print("wrote + validated", p, "| nodes:", len(wf["nodes"]))
