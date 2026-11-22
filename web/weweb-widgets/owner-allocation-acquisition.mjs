import {ownerAttentionSession} from "./owner-attention.mjs";
import {escapeOwnerReviewText} from "./owner-review-portal.mjs";

const scopeKeys = ["legacy_instance_id", "business_id", "engine_id", "jurisdiction"];
const money = new Intl.NumberFormat("en-CA", {style:"currency",currency:"CAD",currencyDisplay:"code"});

function formatMinor(value) {
    if (value === null) return "Unavailable";
    if (!Number.isSafeInteger(value)) throw new Error("Invalid amount");
    return money.format(value / 100);
}

function present(mode, body, payload, campaign) {
    const scope = mode === "allocation" ? payload.scope : payload;
    if (body?.currency !== "CAD" || !/^[a-f0-9]{64}$/.test(body.sha256)
        || !scopeKeys.every(key => body.scope?.[key] === scope[key])) throw new Error("Unexpected scope receipt");
    if (mode === "allocation") {
        if (body.basis !== "RECONCILIATION_FIXTURE" || body.funds_movement_authorized !== false
            || body.standing_mandate_approved !== false || body.actual_accessible_funds_minor !== null
            || body.statement?.id !== payload.statement_id) throw new Error("Unexpected allocation authority");
        return [
            "Allocation rehearsal · " + body.period,
            "Eligible fixture profit · " + formatMinor(body.eligible_distributable_profit_minor),
            "Personal recommendation · " + formatMinor(body.recommended_personal_minor),
            "Household essentials from that amount · " + formatMinor(body.personal_breakdown.essentials_minor),
            "Personal emergency reserve from that amount · " + formatMinor(body.personal_breakdown.reserve_minor),
            "Remaining eligible for reinvestment · " + formatMinor(body.remaining_eligible_for_reinvestment_minor),
            "Household shortfall · " + formatMinor(body.shortfalls.essentials_minor),
            ...body.blockers.map(blocker => "Hold · " + blocker),
            "Evidence SHA-256 · " + body.sha256,
        ];
    }
    if (body.basis !== "SETTLED_ACQUISITION_FIXTURE_ONLY" || body.campaign_id !== campaign
        || body.external_action_authorized !== false || body.verified_commercial_revenue !== false) {
        throw new Error("Unexpected campaign authority");
    }
    return [
        "Settled acquisition rehearsal · " + body.recommendation,
        "Attributed visits · " + body.visits,
        "Settled captures · " + body.settled_captures,
        "Positive-net orders · " + body.positive_net_orders,
        "Unresolved orders · " + body.unresolved_orders,
        "Complete order contribution · " + formatMinor(body.contribution_minor),
        "Evidence SHA-256 · " + body.sha256,
    ];
}

export async function runOwnerAllocationAcquisition(input, transport = fetch) {
    const session = ownerAttentionSession(input.bearer);
    if (!session) return {status:"signed_out"};
    const result = (status, data = {}) => ({status, session, ...data});
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
    const isAllocation = input.mode === "allocation";
    const campaign = Number(input.campaign?.trim());
    try {
        if (!isAllocation && (input.mode !== "acquisition" || !Number.isSafeInteger(campaign) || campaign <= 0
            || !/^\d+$/.test(input.campaign?.trim()))) throw new Error("Invalid campaign");
        if (!input.request || input.request.length > 24000) throw new Error("Invalid request");
        payload = JSON.parse(input.request);
        const scope = isAllocation ? payload?.scope : payload;
        if (!scopeKeys.every(key => typeof scope?.[key] === "string" && scope[key] === scope[key].trim()
            && scope[key].length >= 2 && scope[key].length <= 120)) throw new Error("Invalid scope");
        if (isAllocation && !/^[0-9a-f-]{36}$/.test(payload.statement_id)) throw new Error("Invalid statement");
    } catch {
        return result("invalid");
    }
    const path = isAllocation ? "owner-personal-allocation" : "owner-acquisition/" + campaign + "/settled-review";
    try {
        const response = await transport(origin + "/api/weweb/" + path, {
            method:"POST", headers:{Authorization:"Bearer " + input.bearer,"Content-Type":"application/json"},
            body:JSON.stringify(payload), cache:"no-store", credentials:"omit", redirect:"error",
            signal:AbortSignal.timeout(15000),
        });
        if (response.status === 401) return result("signed_out");
        if (response.status === 403) return result("denied");
        if (response.status === 404 || response.status === 409) return result("held");
        if (response.status === 422) return result("invalid");
        if (!response.ok) return result("unavailable");
        return result("ready", {text:present(input.mode, await response.json(), payload, campaign)
            .map(escapeOwnerReviewText).join("\n")});
    } catch {
        return result("unavailable");
    }
}
