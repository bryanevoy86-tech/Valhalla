import {ownerAttentionSession} from "./owner-attention.mjs";
import {escapeOwnerReviewText} from "./owner-review-portal.mjs";

const routes = ["MANITOBA", "FEDERAL_CANADA", "INTERNATIONAL_FIRST"];
const extraKeys = [
    "funded_infrastructure", "costs", "surplus_assets", "professional_review",
    "startup_cash_available_minor", "operating_cash_available_minor", "operating_reserve_target_minor",
];

function startupPayload({manitoba, named, jurisdiction, details}) {
    if (typeof manitoba !== "boolean" || typeof named !== "boolean") throw new Error("invalid");
    const candidate = jurisdiction?.trim();
    if (!candidate || candidate.length > 120 || (details?.length ?? 0) > 60000) throw new Error("invalid");
    const extra = details?.trim() ? JSON.parse(details) : {};
    if (!extra || typeof extra !== "object" || Array.isArray(extra)
        || Object.keys(extra).some(key => !extraKeys.includes(key))) throw new Error("invalid");
    return {...extra, manitoba_operations: manitoba, named_corporation: named, international_jurisdiction: candidate};
}

const amount = (minor) => Number.isSafeInteger(minor) && minor >= 0
    ? new Intl.NumberFormat("en-CA", {style: "currency", currency: "CAD", currencyDisplay: "code"}).format(minor / 100)
    : "Unavailable";

function safeText(value) {
    if (typeof value !== "string") throw new Error("Invalid planning record");
    return escapeOwnerReviewText(value);
}

function formatLine(item) {
    const sources = [item.source_checked_on, item.reference].filter(Boolean).map(safeText);
    return "• " + safeText(item.label) + " — " + amount(item.amount_minor) + " · " + safeText(item.basis)
        + (sources.length ? " · " + sources.join(" · ") : "");
}

export function formatStartupComparison(data, candidate, expectedPackets) {
    if (data?.currency !== "CAD" || data.activation_authorized !== false || data.external_effects !== 0
        || data.selected_jurisdiction !== null || !Array.isArray(data.options)
        || data.options.length !== routes.length || !Array.isArray(data.professional_review_packets)
        || data.professional_review_packets.length !== expectedPackets
        || !Array.isArray(data.checklist)) throw new Error("Unexpected planning response");
    const summary = data.options.map(({route, jurisdiction, activation, operating, route_review, objectives}, index) => {
        if (route !== routes[index] || (route === "INTERNATIONAL_FIRST" && jurisdiction !== candidate)) {
            throw new Error("Comparison scenario changed");
        }
        return [
            safeText(jurisdiction),
            "Incremental activation",
            ...activation.items.map(formatLine),
            "Known and estimated activation subtotal · " + amount(activation.known_and_estimated_minor),
            "Additional capital floor · " + amount(activation.additional_capital_floor_minor),
            "Minimum additional capital · " + amount(activation.minimum_additional_capital_minor),
            "Open activation items · " + (activation.unpriced_keys.length || "none"),
            "Operating costs and reserves (separate from activation)",
            ...operating.incremental_recurring_items.map(formatLine),
            "Already committed monthly · " + amount(operating.existing_committed_monthly_minor),
            "Known annual operating costs · " + amount(operating.known_annual_cost_minor),
            "Reserve gap · " + amount(operating.reserve_gap_minor),
            "Runway at known costs · " + (Number.isFinite(operating.known_cost_runway_months)
                ? operating.known_cost_runway_months + " months" : "Unavailable"),
            safeText(route_review),
            ...Object.values(objectives).map(safeText),
        ].join("\n");
    });
    const packets = data.professional_review_packets.map(packet => {
        if (packet.status !== "DRAFT_AWAITING_QUALIFIED_REVIEW" || packet.professional_signoff !== null
            || packet.opinion_reference !== null || packet.reliance_authorized !== false) {
            throw new Error("Unexpected professional authority");
        }
        return [
            safeText(packet.jurisdiction) + " · " + safeText(packet.topic),
            "Draft awaiting qualified review",
            ...packet.facts.map(fact => {
                if (fact.basis !== "OWNER_REPORTED") throw new Error("Unexpected fact provenance");
                return "• Owner-reported · " + safeText(fact.label) + " · " + safeText(fact.statement)
                    + " · " + safeText(fact.observed_on) + " · " + safeText(fact.source_reference);
            }),
            ...packet.questions.map(question => "? " + safeText(question)),
        ].join("\n");
    });
    const checklist = data.checklist.map(step => step.sequence + ". " + safeText(step.step)
        + " · " + step.requires.map(safeText).join(", "));
    return {
        summary: ["Compared as of " + safeText(data.as_of), ...summary, "Startup checklist\n" + checklist.join("\n")].join("\n\n"),
        professional: packets.length ? packets.join("\n\n") : "No professional review packet was requested.",
    };
}

async function requestStartupReview(input, transport, route, prepare, format) {
    const session = ownerAttentionSession(input.bearer);
    if (!session) return {status: "signed_out"};
    const result = (status, payload = {}) => ({status, session, ...payload});
    if (input.isOwner !== true) return result("denied");
    let origin;
    try {
        const api = new URL(input.apiBase);
        const approved = new URL(input.previewOrigin);
        if (api.protocol !== "https:" || api.username || api.password || approved.origin !== input.previewOrigin
            || approved.origin !== api.origin) return result("unconfigured");
        origin = approved.origin;
    } catch {
        return result("unconfigured");
    }
    let payload;
    try {
        payload = prepare(input);
    } catch {
        return result("invalid");
    }
    try {
        const reply = await transport(origin + "/api/weweb/owner-startup/" + route, {
            method: "POST", headers: {Authorization: "Bearer " + input.bearer, "Content-Type": "application/json"},
            body: JSON.stringify(payload), cache: "no-store", credentials: "omit", redirect: "error",
            signal: AbortSignal.timeout(15000),
        });
        if (reply.status === 401) return result("signed_out");
        if (reply.status === 403) return result("denied");
        if (reply.status === 422) return result("invalid");
        if (!reply.ok) return result("unavailable");
        return result("ready", format(await reply.json(), payload));
    } catch {
        return result("unavailable");
    }
}

export function runOwnerStartup(input, transport = fetch) {
    return requestStartupReview(input, transport, "compare", startupPayload, (data, payload) =>
        formatStartupComparison(data, payload.international_jurisdiction, payload.professional_review?.length ?? 0));
}

function independencePayload({details}) {
    if (typeof details !== "string" || !details.trim() || details.length > 60000) throw new Error("Invalid plan");
    const plan = JSON.parse(details);
    if (!plan || typeof plan !== "object" || Array.isArray(plan)) throw new Error("Invalid plan");
    return plan;
}

function formatIndependence(data) {
    if (data?.currency !== "CAD" || data.basis !== "PRIVATE_STARTUP_PLANNING"
        || data.external_action_authorized !== false || data.borrowing_authorized !== false
        || data.transfers_authorized !== false || data.contingency_activation_authorized !== false
        || data.verified_available_cash_minor !== null || data.verified_after_tax_income_minor !== null
        || data.support_forecast_minor !== null || data.stretch_guaranteed !== false
        || data.reporting?.official_or_case_evidence_verified !== false
        || data.capital_scenarios?.[0]?.hypothetical_extra_contribution_minor !== 0) {
        throw new Error("Unexpected independence review");
    }
    const {financing_screen: financing} = data;
    if (financing && (financing.basis !== "SYNTHETIC_FIXTURE" || financing.new_revenue_assumed_minor !== 0
        || financing.borrowing_authorized !== false || financing.requires_reconciled_balances_and_review !== true)) {
        throw new Error("Unexpected financing review");
    }
    const label = value => safeText(value.replaceAll("_", " ").toLowerCase());
    const checkpoints = data.reviews.map(review =>
        "Day " + review.day + " · " + safeText(review.due) + " · " + label(review.focus) + " · " + label(review.status));
    const capital = data.capital_scenarios.map(scenario =>
        amount(scenario.hypothetical_extra_contribution_minor) + " extra contribution · gap "
        + amount(scenario.total_plan_gap_minor) + " · experiment headroom " + amount(scenario.experiment_headroom_minor));
    const funding = data.funding.map(item => {
        if (item.included_in_spendable_cash_minor !== 0) throw new Error("Unexpected funding availability");
        return label(item.kind) + " · " + label(item.status) + " · " + amount(item.amount_minor);
    });
    return {summary: [
        "Registration · " + (data.registration_date ? safeText(data.registration_date) : "Awaiting evidence"),
        ...checkpoints,
        "Synthetic capital scenarios",
        ...capital,
        ...funding,
        "Personal emergency reserve gap · " + amount(data.personal_reserve_gap_minor),
        "Estimated household shortfall · " + amount(data.household_estimated_shortfall_minor),
        "Draft reporting · " + label(data.reporting.status),
        ...data.reporting.checklist.map(label),
        ...(financing ? ["Synthetic financing screen · " + label(financing.screen),
            "Stressed monthly debt service · " + amount(financing.stressed_total_monthly_debt_service_minor),
            "Opening unrestricted cash gap · " + amount(financing.opening_unrestricted_cash_gap_minor),
            ...financing.reasons.map(label)] : []),
    ].join("\n")};
}

export function runOwnerIndependence(input, transport = fetch) {
    return requestStartupReview(input, transport, "independence-review", independencePayload, formatIndependence);
}
