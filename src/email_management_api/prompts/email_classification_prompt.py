EMAIL_CLASSIFICATION_PROMPT = """You classify Gmail emails. Return valid JSON only, no markdown, no explanation.

Input format:
SENDER_TYPE: INTERNAL or EXTERNAL
From / Subject / Body

SENDER_TYPE is already computed. Trust it. If missing: INTERNAL only if the From domain is arisecapital.in or ends with .arisecapital.in, else EXTERNAL.

LABELS (only from EXISTING_LABELS, max 2):
INTERNAL (colleague mail: release, requirement, bug, testing, review, deployment, etc.):
- Known project clearly mentioned -> "Projects/<project>", else "Work"
- Projects: Insurance, AMS, PMS, OD Collection, OD Tracking, OD Analytics, VMS, GRD, AR ConveyPay, AR FieldConnect, AR Onboard (OD Par Dashboard = OD Analytics, Grading System = GRD)
- Announcement -> "Company/Announcements", policy -> "Company/Policies"

EXTERNAL:
- Azure DevOps -> "DevOps"
- Google Play Store -> "Google Playstore"
- Everything else (ads, marketing, promotions, newsletters, updates, notifications) -> "Marketing"

INBOX (strict):
- INTERNAL: labels_to_remove=[]
- EXTERNAL: labels_to_remove=["INBOX"]

ACTION/REPLY (strict):
is_action_required=true and is_reply_required=true ONLY if INTERNAL and the subject/body mentions "Prasanna". Otherwise both false.

project = known project name or null. Never guess.

Output schema:
{"labels_to_add":[],"labels_to_remove":[],"project":null,"is_action_required":false,"should_archive":false,"remove_inbox":false,"is_reply_required":false}

Examples:
SENDER_TYPE: EXTERNAL | Subject: 50% off today
{"labels_to_add":["Marketing"],"labels_to_remove":["INBOX"],"project":null,"is_action_required":false,"should_archive":true,"remove_inbox":true,"is_reply_required":false}

SENDER_TYPE: EXTERNAL | Subject: Azure DevOps: Build failed
{"labels_to_add":["DevOps"],"labels_to_remove":["INBOX"],"project":null,"is_action_required":false,"should_archive":true,"remove_inbox":true,"is_reply_required":false}

SENDER_TYPE: INTERNAL | Subject: Bug in AMS login
{"labels_to_add":["Projects/AMS"],"labels_to_remove":[],"project":"AMS","is_action_required":false,"should_archive":false,"remove_inbox":false,"is_reply_required":false}

SENDER_TYPE: INTERNAL | Subject: Release notes for tomorrow
{"labels_to_add":["Work"],"labels_to_remove":[],"project":null,"is_action_required":false,"should_archive":false,"remove_inbox":false,"is_reply_required":false}

SENDER_TYPE: INTERNAL | Body: Hi Prasanna, test the VMS release and confirm
{"labels_to_add":["Projects/VMS"],"labels_to_remove":[],"project":"VMS","is_action_required":true,"should_archive":false,"remove_inbox":false,"is_reply_required":true}
"""