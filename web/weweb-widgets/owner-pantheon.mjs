import {ownerAttentionSession} from "./owner-attention.mjs";
import {escapeOwnerReviewText} from "./owner-review-portal.mjs";

const uuid = /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i;
const reportId = /^GOD-[0-9a-f]{64}$/;

function projectReport(item) {
    if (!uuid.test(item.assignment_id) || !/^[A-Z]{2,40}$/.test(item.role)) throw new Error("Unexpected assignment");
    if (item.state === "INTEGRITY_HOLD") return item.role + " · " + item.assignment_id + " · Report integrity hold";
    if (item.state !== "VERIFIED_RECEIPT" || !reportId.test(item.report_event_id)
        || !/^[a-f0-9]{64}$/.test(item.report_sha256)) throw new Error("Unexpected receipt");
    const scope = item.scope;
    const text = [
        item.role + " · " + item.lens + " · " + item.report_status,
        [scope.legacy_instance_id, scope.business_id, scope.engine_id, scope.jurisdiction].join(" / "),
        item.observed_at + " · " + item.trigger + " · Assignment " + item.assignment_state,
        item.report_event_id,
    ];
    if (item.observation_categories.length) text.push("Observed categories · " + item.observation_categories.join(", "));
    const loki = item.independent_loki;
    if (loki === null) {
        text.push("Independent Loki review · No matching receipt");
    } else {
        if (!uuid.test(loki.review_id)) throw new Error("Unexpected challenge reference");
        text.push("Independent Loki review · " + loki.status + " · " + loki.review_id);
        if (loki.status === "completed") {
            text.push("Reconsideration · " + loki.reconsideration_status, ...loki.findings.slice(0, 10));
        }
    }
    return text.map(escapeOwnerReviewText).join("\n");
}

export async function runOwnerPantheon(input, transport = fetch) {
    const session = ownerAttentionSession(input.bearer);
    if (!session) return {status: "signed_out"};
    const result = (status, data = {}) => ({session, status, ...data});
    if (input.isOwner !== true) return result("denied");
    let endpoint;
    try {
        const api = new URL(input.apiBase);
        const approved = new URL(input.previewOrigin);
        if (api.protocol !== "https:" || api.username || api.password || approved.origin !== input.previewOrigin
            || approved.origin !== api.origin) return result("unconfigured");
        endpoint = new URL("/api/weweb/owner-pantheon/reports", approved);
    } catch {
        return result("unconfigured");
    }
    const role = input.role?.trim().toUpperCase() ?? "";
    if (role && !/^[A-Z]{2,40}$/.test(role)) return result("invalid_role");
    if (role) endpoint.searchParams.set("role", role);
    if (input.next) {
        const prior = input.prior;
        if (prior?.session !== session || prior.role !== role || !uuid.test(prior.nextAfter)) {
            return result("reload_required");
        }
        endpoint.searchParams.set("after", prior.nextAfter);
    }
    try {
        const response = await transport(endpoint.toString(), {
            method: "GET", headers: {Authorization: "Bearer " + input.bearer},
            cache: "no-store", credentials: "omit", redirect: "error", signal: AbortSignal.timeout(15000),
        });
        if (response.status === 401) return result("signed_out");
        if (response.status === 403) return result("denied");
        if (response.status === 422) return result("invalid_role");
        if (!response.ok) return result("unavailable");
        const body = await response.json();
        if (body?.execution_authorized !== false || !Array.isArray(body.reports) || body.reports.length > 10
            || (body.next_after !== null && !uuid.test(body.next_after))
            || (role && body.reports.some(item => item.role !== role))) return result("unavailable");
        return result("ready", {role, text: body.reports.map(projectReport).join("\n\n"), nextAfter: body.next_after});
    } catch {
        return result("unavailable");
    }
}
