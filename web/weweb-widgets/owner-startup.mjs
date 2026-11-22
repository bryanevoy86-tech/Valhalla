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

export async function runOwnerStartup(input, transport = fetch) {
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
        payload = startupPayload(input);
    } catch {
        return result("invalid");
    }
    try {
        const reply = await transport(origin + "/api/weweb/owner-startup/compare", {
            method: "POST", headers: {Authorization: "Bearer " + input.bearer, "Content-Type": "application/json"},
            body: JSON.stringify(payload), cache: "no-store", credentials: "omit", redirect: "error",
            signal: AbortSignal.timeout(15000),
        });
        if (reply.status === 401) return result("signed_out");
        if (reply.status === 403) return result("denied");
        if (reply.status === 422) return result("invalid");
        if (!reply.ok) return result("unavailable");
        return result("ready", formatStartupComparison(await reply.json(), payload.international_jurisdiction,
            payload.professional_review?.length ?? 0));
    } catch {
        return result("unavailable");
    }
}
