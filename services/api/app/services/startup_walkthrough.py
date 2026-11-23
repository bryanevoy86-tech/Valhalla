"""Owner-guided startup preparation using the existing private conversation history."""
from datetime import date, timedelta
import re

from fastapi import HTTPException
from sqlalchemy import func, select

from app.models.owner_conversation import OwnerTurn
from app.services.owner_startup import StartupPlanIn, prepare_startup

COMMAND = "I am ready to register Valhalla Legacy Inc. Walk me through everything and help me find the professionals I need."
GUIDE_VERSION = 1
EVIDENCE_RECHECK_DAYS = 90
STEPS = {
    "name": ("Name and incorporation route",
             "List the proposed name and alternatives. Manitoba incorporation establishes a Manitoba company. Federal incorporation is a separate route, and a company operating in Manitoba still needs Manitoba registration. Check name availability and discuss both routes before choosing."),
    "structure": ("Ownership and operating structure",
                  "Ask counsel and the accountant to compare one operating company with a HoldCo, OpCo, subsidiaries and any trust. Map ownership, IP, liability, group accounting and future acquisitions."),
    "professionals": ("Lawyer and accountant shortlist",
                      "Compare current regulator status, scope, experience and written fees. Approve the shortlist locally before any outreach or disclosure. See the professional research handoff in the startup runbook."),
    "reporting": ("EIA notification and reporting",
                  "Record your written case instructions privately. Confirm the registration notification trigger, due date, channel and ongoing reporting before relying on any schedule. Prepare business and personal income, expenses, assets, contributions, retained earnings, distributions and funding records."),
    "registration": ("Incorporation and registrations",
                     "Confirm the name, jurisdiction, ownership, directors and registered office with counsel. Retain the filing receipt and verify business number and corporate income tax account. Identify any applicable GST/HST, payroll, Manitoba tax, permits and annual filings with qualified advisers."),
    "accounts": ("Banking, bookkeeping and payments",
                 "Confirm the business account and signing authority, open the books with a qualified accountant, and approve a separate Stripe sandbox for one CAD offer. Verify settlement independently before relying on funds."),
    "staging": ("Staging acceptance",
                "Approve exact HTTPS origins, isolated API, worker and database, reviewer identity and restore target. Review the 24-hour trial, rollback and sandbox receipts."),
    "launch": ("First legitimate business approval",
               "Review the exact offer, operating scope, customer rights, support and refund terms. Obtain separate owner approval after independent evidence, professional gates and staging acceptance are reviewed."),
}
COMMANDS = {COMMAND.casefold().rstrip("?! ."), "startup walkthrough", "startup progress", "startup professionals"}
RESEARCH = (
    ("Danielle Grzybowski, Fillmore Riley", "Software, SaaS licensing and technology transactions",
     "https://www.fillmoreriley.com/our-people/bio/danielle-grzybowski"),
    ("Leilani Kagan, TDS", "Corporate reorganizations, acquisitions, cross-border tax and trusts",
     "https://www.tdslaw.com/lawyers/leilani-kagan/"),
    ("Nicole Perras, MNP Winnipeg", "Owner-manager corporate tax, estates and trusts",
     "https://www.mnp.ca/en/personnel/nicole-perras"),
    ("Brenda Toles, BDO Winnipeg", "Accounting and tax for private companies",
     "https://www.bdo.ca/our-people/brenda-toles"),
)
DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
RECORD_USAGE = "Record startup <step> | YYYY-MM-DD | private evidence reference | decision or outcome"


def _is_update(message: str) -> bool:
    return message.casefold().split()[:2] in (["record", "startup"], ["reopen", "startup"])


def is_startup_turn(normalized: str) -> bool:
    return normalized in COMMANDS or _is_update(normalized)


def _record(message: str, today: date) -> dict:
    fields = [part.strip() for part in message.split("|")]
    heading = fields[0].casefold().split()
    if (len(fields) != 4 or len(heading) != 3 or heading[:2] not in (["record", "startup"], ["reopen", "startup"])
            or heading[2] not in STEPS or not DATE_PATTERN.fullmatch(fields[1])
            or not 1 <= len(fields[2]) <= 160 or not 1 <= len(fields[3]) <= 400):
        raise HTTPException(422, f"Use {RECORD_USAGE}. Reopen startup uses the same fields.")
    try:
        observed = date.fromisoformat(fields[1])
    except ValueError:
        raise HTTPException(422, "Use a valid evidence date") from None
    if observed > today:
        raise HTTPException(422, "Evidence cannot be dated in the future")
    return {"step": heading[2], "observed_on": fields[1], "reference": fields[2], "statement": fields[3],
            "reopened": heading[0] == "reopen", "guide_version": GUIDE_VERSION}


def _prior_records(db, conversation_id) -> dict:
    record = OwnerTurn.evidence["startup_record"]
    step = record["step"].as_string()
    latest = select(
        record.label("receipt"), func.row_number().over(
            partition_by=step, order_by=(OwnerTurn.created_at.desc(), OwnerTurn.id.desc())
        ).label("position"),
    ).where(OwnerTurn.conversation_id == conversation_id, step.in_(tuple(STEPS))).subquery()
    return {receipt["step"]: receipt for receipt in db.scalars(
        select(latest.c.receipt).where(latest.c.position == 1)
    )}


def _status(record: dict | None, today: date) -> str:
    if not record or record["reopened"]:
        return "OPEN"
    observed = date.fromisoformat(record["observed_on"])
    if record["guide_version"] != GUIDE_VERSION or not observed <= today <= observed + timedelta(days=EVIDENCE_RECHECK_DAYS):
        return "RECHECK"
    return "OWNER_RECORDED"


def walkthrough(db, conversation_id, message: str, today: date) -> tuple[str, dict]:
    evidence = {"source": "private_startup_walkthrough", "model_connected": False,
                "government_or_professional_verification": False, "activation_authorized": False,
                "as_of": today.isoformat()}
    records = _prior_records(db, conversation_id)
    if _is_update(message):
        record = _record(message, today)
        records[record["step"]] = record
        evidence["startup_record"] = record
    progress = [
        {"key": key, "title": title, "action": action, "status": _status(records.get(key), today),
         "owner_evidence": ({field: records[key][field] for field in ("observed_on", "reference", "guide_version")}
                            if key in records else None)}
        for key, (title, action) in STEPS.items()
    ]
    next_step = next((step for step in progress if step["status"] != "OWNER_RECORDED"), None)
    budget = prepare_startup(StartupPlanIn(manitoba_operations=True, named_corporation=True), today=today)
    filing_estimates = []
    for option in budget["options"][:2]:
        fees = [item for item in option["activation"]["items"] if item["key"].startswith("registry:")]
        government_total = sum(item["amount_minor"] for item in fees) if all(
            item["amount_minor"] is not None for item in fees
        ) else None
        filing_estimates.append({"route": option["route"], "government_minor": government_total, "items": fees})
    evidence.update(progress=progress, next_step=next_step["key"] if next_step else None,
                    planning_assumptions={"manitoba_operations": True, "named_corporation": True},
                    filing_estimates=filing_estimates, professional_fees="WRITTEN_QUOTES_PENDING",
                    dependencies=budget["startup_dependencies"],
                    professional_candidates=[{"name": name, "fit": fit, "source": source,
                                              "approval": "PENDING", "current_registry_status": "UNVERIFIED",
                                              "fee_status": "WRITTEN_QUOTE_PENDING"} for name, fit, source in RESEARCH])
    reply = ["I can walk you through a Manitoba-based startup. We’ll review the evidence together before each decision."]
    if "startup_record" in evidence:
        reply.append("I saved your update in this private conversation as owner-reported evidence.")
    reply.extend(f"{step['title']} [{step['key']}] ({step['status'].replace('_', ' ').lower()}). {step['action']}" for step in progress)
    normalized = " ".join(message.casefold().rstrip("?! .").split())
    if normalized in {COMMAND.casefold().rstrip("?! ."), "startup professionals"}:
        reply.append("Candidates to review. " + " | ".join(f"{name} · {fit} · {source}" for name, fit, source in RESEARCH)
                     + ". Current registration, fit, conflicts, fees and your approval are still open."
                     + " Use the regulator directories at https://portal.lawsociety.mb.ca/lookup/ and"
                       " https://cpamb.ca/main/main/find-a-cpa/find-a-firms-tc.aspx.")
    costs = [f"{name} CAD {item['government_minor'] / 100:,.2f}" if item["government_minor"] is not None
             else f"{name} fees need rechecking" for name, item in zip(("Manitoba", "Federal plus Manitoba"), filing_estimates)]
    reply.append("Planning budget for a named Manitoba operation. " + " | ".join(costs)
                 + ". Professional quotes, tax, operating costs and reserves are still separate.")
    reply.append("Next safe action. " + (next_step["action"] if next_step else
                 "Review the recorded references and obtain independent acceptance and a separate launch decision."))
    if next_step:
        reply.append("To save this checkpoint, use " + RECORD_USAGE.replace("<step>", next_step["key"]) + ".")
    reply.append("Say Startup progress to resume or Startup professionals to see the shortlist.")
    return "\n\n".join(reply), evidence
