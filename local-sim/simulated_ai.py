"""Deterministic, explainable rules that simulate the AI proposal."""

from __future__ import annotations

import re


CATEGORY_RULES = (
    (
        "Access",
        (
            "access", "permission", "sign in", "sign-in", "login", "log in",
            "password", "locked out", "account locked", "mfa", "shared mailbox",
        ),
    ),
    (
        "Network",
        ("wi-fi", "wifi", "vpn", "network", "internet", "dns", "connectivity"),
    ),
    (
        "Hardware",
        (
            "laptop", "desktop", "monitor", "screen", "keyboard", "mouse",
            "printer", "headset", "battery", "dock", "webcam", "device",
        ),
    ),
    (
        "Microsoft 365",
        (
            "teams", "outlook", "sharepoint", "onedrive", "one drive", "excel",
            "word", "powerpoint", "exchange", "microsoft 365", "office 365",
        ),
    ),
    (
        "Software",
        ("software", "application", "app", "install", "crash", "license", "browser"),
    ),
)


# Priority is based on observable impact and timing, not a requested label,
# emotional wording, or requester seniority. Patterns are deliberately grouped
# by business signal so future changes remain reviewable.
SEVERE_RISK_PATTERNS = (
    r"\bransomware\b",
    r"\bdata breach\b",
    r"\bcredentials? (?:were |was )?(?:stolen|exposed)\b",
    r"\baccount (?:was )?(?:hacked|compromised)\b",
    r"\bconfirmed unauthori[sz]ed access\b",
    r"\b(?:immediate|serious) safety risk\b",
)

SECURITY_RISK_PATTERNS = (
    r"\bsecurity incident\b",
    r"\bphishing\b",
    r"\bsuspicious (?:sign-in|login|account activity)\b",
    r"\bunexpected (?:mfa|authentication) (?:prompt|request)s?\b",
    r"\bmfa\b.{0,40}\b(?:did not|didn't|not) (?:initiate|request|approve)\b",
    r"\b(?:lost|stolen) (?:company )?(?:laptop|device|phone)\b",
)

ROUTINE_SECURITY_PATTERNS = (
    r"\b(?:phishing|security|cyber(?:security)?) (?:awareness )?"
    r"(?:training|exercise|simulation|drill)\b",
    r"\b(?:training|exercise|simulation|drill)\b.{0,40}"
    r"\b(?:phishing|security|cyber(?:security)?)\b",
)

ACTIVE_SECURITY_PATTERNS = (
    r"\b(?:clicked|opened|responded to) (?:a )?(?:phishing|suspicious) "
    r"(?:email|link|message)\b",
    r"\bentered (?:my |their |company )?(?:password|credentials)\b",
    r"\bsuspicious (?:sign-in|login|account activity)\b",
    r"\bunexpected (?:mfa|authentication) (?:prompt|request)s?\b",
)

WIDESPREAD_PATTERNS = (
    r"\b(?:everyone|all users|all staff|all employees)\b",
    r"\ball \d+ (?:users|staff|employees|people)\b",
    r"\b(?:entire|whole) (?:office|site|company|organization|organisation|department|team)\b",
    r"\b(?:company|site|office)[ -]wide\b",
    r"\bmultiple sites\b",
)

MULTI_USER_PATTERNS = (
    r"\b(?:several|multiple|many) (?:users|staff|employees|people|colleagues|teams?)\b",
    r"\b(?:\d+|two|three|four|five|six|seven|eight|nine|ten|dozens? of) "
    r"(?:users|staff|employees|people|colleagues|agents|workers|analysts|dispatchers)\b",
)

OUTAGE_PATTERNS = (
    r"\b(?:outage|offline|unavailable|down)\b",
    r"\b(?:cannot|can't|unable to|could not) (?:connect|open|access|use|log in|sign in)\b",
    r"\blost (?:wired and wireless )?(?:network )?access\b",
    r"\bwill not open\b",
)

PLANNED_MAINTENANCE_PATTERNS = (
    r"\b(?:planned|scheduled|routine)\b.{0,40}"
    r"\b(?:maintenance|upgrade|outage|downtime|work)\b",
    r"\b(?:maintenance|upgrade|outage|downtime) (?:is |has been )?scheduled\b",
)

CURRENT_INCIDENT_PATTERNS = (
    r"\b(?:is|are|remains?|went|has gone) "
    r"(?:currently |still |completely |now )*(?:down|offline|unavailable)\b",
    r"\b(?:currently|now|right now) (?:completely )?"
    r"(?:down|offline|unavailable|blocked)\b",
    r"\b(?:operations?|production|processing) (?:has |have |is |are )?"
    r"(?:now |currently )?(?:stopped|halted)\b",
    r"\b(?:all users|all employees|all staff|everyone|multiple users)\b "
    r"(?:are )?(?:currently |now )?(?:unable to|cannot|can't) "
    r"(?:connect|open|access|use|work|log in|sign in)\b",
)

BLOCKING_PATTERNS = OUTAGE_PATTERNS + (
    r"\bblocked\b",
    r"\baccess denied\b",
    r"\b(?:cannot|can't|unable to) work\b",
    r"\b(?:fails?|failed)\b",
)

STOPPED_OPERATION_PATTERNS = (
    r"\b(?:business|operations?|production|processing|payment run) (?:has |have )?(?:stopped|halted)\b",
    r"\b(?:customer calls?|orders?|payments?|requests?) cannot be (?:logged|processed|completed)\b",
    r"\bunable to (?:process|operate|continue)\b",
)

NO_WORKAROUND_PATTERNS = (
    r"\bno (?:available |adequate |manual |other )?(?:workaround|alternative(?: connection)?|fallback|backup)\b",
    r"\bwithout (?:a |an )?(?:workaround|alternative|fallback|backup)\b",
    r"\bno (?:one|colleague|coworker|co-worker|team member) can\b",
    r"\bnothing else (?:works|is available)\b",
)

NEAR_DEADLINE_PATTERNS = (
    r"\b(?:today|tonight|this morning|this afternoon|by noon|before noon)\b",
    r"\b(?:in|within) (?:the next )?"
    r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve) "
    r"(?:minutes?|hours?)\b",
    r"\bby \d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?)?\b",
)

NEGATED_CURRENT_IMPACT_PATTERNS = (
    r"\b(?:nothing|nobody|no one) (?:is |are )?(?:currently )?blocked (?:today|now)\b",
    r"\bnot (?:currently )?blocked (?:today|now)\b",
    r"\bno (?:current |immediate )?(?:impact|deadline)\b",
    r"\b(?:is|are|was|were) not (?:currently )?(?:down|offline|unavailable)\b",
    r"\bno (?:current |active |ongoing )?(?:outage|security incident|data breach)\b",
)

NEGATED_SIGNAL_PATTERNS = (
    r"\b(?:is|are|was|were) not (?:currently )?(?:down|offline|unavailable)\b",
    r"\bno (?:current |active |ongoing )?(?:outage|security incident|data breach)\b",
    r"\b(?:outage|security incident|data breach) (?:is |was )?"
    r"(?:not active|resolved|over)\b",
    r"\b(?:credentials?|account) (?:are |is |were |was )?not "
    r"(?:stolen|exposed|compromised)\b",
)

DISTANT_DEADLINE_PATTERNS = (
    r"\bnext (?:week|month|quarter)\b",
    r"\bin (?:two|three|four|five|six|\d+) (?:business )?(?:days?|weeks?|months?)\b",
)

STRONG_WORKAROUND_PATTERNS = (
    r"\bspare\b.{0,50}\bworks?\b",
    r"\bcan (?:still )?use\b.{0,50}\b(?:until|instead|meanwhile)\b",
    r"\b(?:alternative|backup|spare)\b.{0,40}\b(?:works?|available)\b",
    r"\b(?:another|second|nearby)\b.{0,40}\b(?:works?|available)\b",
    r"\b(?:can|is able to)\b.{0,40}\b(?:cover|continue)\b",
)

LOW_URGENCY_PATTERNS = (
    r"\bhow (?:do i|to)\b",
    r"\bwould (?:like|prefer)\b",
    r"\bwhen possible\b",
    r"\b(?:cosmetic|optional|routine|planned)\b",
    r"\bno deadline\b",
    r"\bplease install\b",
)


def classify(title: str, description: str) -> dict[str, str]:
    """Return the same four-field contract used by the Microsoft 365 design."""
    text = f"{title} {description}".lower()
    category = _category(title.lower(), description.lower())
    priority = _priority(text)
    summary = _summary(title, description)
    suggested_reply = _reply(category)
    return {
        "category": category,
        "priority": priority,
        "summary": summary,
        "suggested_reply": suggested_reply,
    }


def _category(title: str, description: str) -> str:
    # A title normally names the affected service, while descriptions often mention
    # incidental devices. Weight title evidence so "Outlook ... on my laptop" maps
    # to Microsoft 365 rather than Hardware. Tuple order resolves equal scores.
    scored = []
    for category, keywords in CATEGORY_RULES:
        title_hits = sum(keyword in title for keyword in keywords)
        description_hits = sum(keyword in description for keyword in keywords)
        scored.append((title_hits * 3 + description_hits, category))
    best_score = max(score for score, _ in scored)
    if best_score == 0:
        return "Other"
    return next(category for score, category in scored if score == best_score)


def _priority(text: str) -> str:
    text = re.sub(r"\s+", " ", text.lower()).strip()
    negated_current_impact = _matches(text, NEGATED_CURRENT_IMPACT_PATTERNS)
    signal_text = _without_matches(
        text, NEGATED_SIGNAL_PATTERNS + NEGATED_CURRENT_IMPACT_PATTERNS
    )
    planned_maintenance = _matches(signal_text, PLANNED_MAINTENANCE_PATTERNS)
    current_incident = _matches(signal_text, CURRENT_INCIDENT_PATTERNS)
    planned_only = planned_maintenance and not current_incident
    routine_security = _matches(signal_text, ROUTINE_SECURITY_PATTERNS)
    active_security = _matches(signal_text, ACTIVE_SECURITY_PATTERNS)
    routine_security_only = routine_security and not active_security

    severe_risk = _matches(signal_text, SEVERE_RISK_PATTERNS)
    security_risk = (
        _matches(signal_text, SECURITY_RISK_PATTERNS) and not routine_security_only
    )
    widespread = _matches(signal_text, WIDESPREAD_PATTERNS)
    multiple_users = widespread or _matches(signal_text, MULTI_USER_PATTERNS)
    outage = _matches(signal_text, OUTAGE_PATTERNS) and not planned_only
    blocking = _matches(signal_text, BLOCKING_PATTERNS) and not planned_only
    stopped_operation = (
        _matches(signal_text, STOPPED_OPERATION_PATTERNS) and not planned_only
    )
    no_workaround = _matches(signal_text, NO_WORKAROUND_PATTERNS)
    near_deadline = (
        _matches(text, NEAR_DEADLINE_PATTERNS) and not negated_current_impact
    )
    distant_deadline = _matches(text, DISTANT_DEADLINE_PATTERNS)
    strong_workaround = _matches(text, STRONG_WORKAROUND_PATTERNS)
    low_urgency = _matches(text, LOW_URGENCY_PATTERNS)

    # Critical signals take precedence over reassuring or cosmetic wording.
    if severe_risk or (widespread and outage) or (stopped_operation and no_workaround):
        return "Critical"

    # High requires evidence beyond an urgency word: a credible security risk,
    # or blocked work paired with either a near deadline or several affected users.
    if security_risk or (blocking and no_workaround and (near_deadline or multiple_users)):
        return "High"

    # Explicitly negated incidents are not emergencies. Planned future maintenance
    # and routine security exercises are Low when the text also supplies a distant
    # date, a working fallback, or other low-urgency evidence.
    if negated_current_impact and not any(
        (severe_risk, security_risk, outage, blocking, stopped_operation)
    ):
        return "Low"
    if (planned_only or routine_security_only) and (
        strong_workaround or low_urgency or distant_deadline
    ):
        return "Low"

    # A strong workaround can make a small issue Low, but not when several people
    # are affected. Planned, distant, or cosmetic work is Low unless stronger
    # impact signals above already applied.
    if (
        (strong_workaround and not multiple_users and not near_deadline)
        or ((low_urgency or distant_deadline) and not multiple_users and not near_deadline)
    ):
        return "Low"
    return "Medium"


def _matches(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def _without_matches(text: str, patterns: tuple[str, ...]) -> str:
    for pattern in patterns:
        text = re.sub(pattern, " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _summary(title: str, description: str) -> str:
    clean_description = re.sub(r"\s+", " ", description).strip()
    first_sentence = re.split(r"(?<=[.!?])\s+", clean_description, maxsplit=1)[0]
    summary = f"{title.strip()}: {first_sentence}"
    return summary[:300].rstrip()


def _reply(category: str) -> str:
    focus = {
        "Access": "account or permission details",
        "Hardware": "device and impact details",
        "Software": "application and error details",
        "Microsoft 365": "Microsoft 365 service details",
        "Network": "connection and affected-user details",
        "Other": "request details",
    }[category]
    return (
        "Thanks for contacting the service desk. "
        f"An agent will review the {focus} and confirm the next step."
    )
