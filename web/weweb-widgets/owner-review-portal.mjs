import {ownerAttentionSession} from "./owner-attention.mjs";

const referencePattern = /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i;
const sha256Pattern = /^[0-9a-f]{64}$/;

export function escapeOwnerReviewText(value) {
    return String(value).replace(/[&<>"']/g, (ch) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[ch]);
}

export async function runOwnerReviewPortal(input, transport = fetch, createId = () => crypto.randomUUID()) {
    const session = ownerAttentionSession(input.bearer);
    if (!session) return {status: "signed_out"};
    const result = (status, payload = {}) => ({session, status, ...payload});
    if (!input.isOwner) return result("denied");
    let origin;
    try {
        const api = new URL(input.apiBase);
        const approved = new URL(input.previewOrigin);
        if (api.protocol !== "https:" || api.username || api.password
            || approved.origin !== api.origin || approved.origin !== input.previewOrigin) return result("unconfigured");
        origin = approved.origin;
    } catch {
        return result("unconfigured");
    }

    const request = async (path, body) => {
        const response = await transport(origin + "/api/weweb/" + path, {
            method: body ? "POST" : "GET", headers: {
                Authorization: "Bearer " + input.bearer, ...(body ? {"Content-Type": "application/json"} : {}),
            },
            body: body ? JSON.stringify(body) : undefined, cache: "no-store", credentials: "omit",
            redirect: "error", signal: AbortSignal.timeout(15000),
        });
        if (response.status === 401) throw new Error("signed_out");
        if (response.status === 403) throw new Error("denied");
        if (response.status === 404) throw new Error("not_found");
        if (response.status === 409 || response.status === 410) throw new Error("changed");
        if (!response.ok) throw new Error("unavailable");
        return response.json();
    };

    function projectRequest(payload, id) {
        const item = payload?.request;
        if (item?.request_id !== id || !referencePattern.test(item.attachment_id)
            || !["ACCEPT_LOCAL", "REJECT", "DISPOSE"].includes(item.operation)
            || !sha256Pattern.test(payload.request_sha256)
            || !["PENDING_MANDATE", "APPLIED"].includes(payload.status)
            || payload.execution_authorized !== false || payload.provider_forwarding_authorized !== false) {
            throw new Error("unavailable");
        }
        if (payload.status === "APPLIED") {
            const receipt = payload.receipt;
            const matches = item.operation === "DISPOSE"
                ? receipt?.state === "DELETED" && receipt.sha256 === item.source_sha256
                : receipt?.disposition === item.operation && receipt.source_sha256 === item.source_sha256;
            if (!matches || receipt.attachment_id !== item.attachment_id) throw new Error("unavailable");
        } else if (payload.receipt !== null) {
            throw new Error("unavailable");
        }
        return result("ready", {kind: "document", document: {id, attachmentId: item.attachment_id,
            operation: item.operation, state: payload.status, sha256: payload.request_sha256}});
    }

    let pending = input.prior?.session === session ? input.prior.pending : null;
    try {
        const {operation} = input;
        const id = input.reference?.trim();
        if (["prime", "specialist", "status"].includes(operation)) {
            if (!referencePattern.test(id)) return result("invalid_reference", {pending});
            if (operation === "status") return {...projectRequest(await request("owner-document-requests/" + id), id), pending};
            const path = operation === "prime" ? "owner-prime-decisions/" : "owner-specialist-schedules/";
            const data = await request(path + id);
            if (data?.execution_authorized !== false) throw new Error("unavailable");
            if (operation === "prime") {
                const loki = data.independent_loki;
                if (data.prime_decision_id !== id || data.evidence_class !== "REVIEWED_INTERNAL_RECOMMENDATION"
                    || !referencePattern.test(loki?.review_id) || !sha256Pattern.test(loki?.proposal_sha256)
                    || !Array.isArray(loki?.findings) || typeof loki.ok_to_proceed !== "boolean") throw new Error("unavailable");
                return result("ready", {kind: "prime", pending, evidence: {id, decision: data.heimdall_decision,
                    loki: loki.review_id, proposal: loki.proposal_sha256, cleared: loki.ok_to_proceed,
                    reconsideration: loki.reconsideration_status, findings: loki.findings.slice(0, 12),
                    mimir: data.reviewed_mimir_outcomes?.length ?? 0}});
            }
            if (data.schedule_id !== id || data.evidence_class !== "INTERNAL_ADVISORY"
                || typeof data.report_event_id !== "string" || data.independent_loki_cleared !== false) {
                throw new Error("unavailable");
            }
            return result("ready", {kind:"specialist", pending, evidence: {id, report: data.report_event_id,
                state: data.status, recorded: data.observed_at, decision: data.heimdall_decision,
                blockers: data.operating_reassessment?.blockers ?? []}});
        }

        const documentOperation = {approve: "ACCEPT_LOCAL", reject: "REJECT", dispose: "DISPOSE"}[operation];
        const cid = input.conversation?.session === session ? input.conversation.selected : null;
        const attachmentId = input.attachment?.trim();
        const reason = input.reason?.trim();
        if (!documentOperation || !referencePattern.test(cid) || !referencePattern.test(attachmentId)
            || !reason || reason.length > 1400) return result("invalid_document", {pending});
        const path = "owner-conversations/" + cid + "/attachments";
        const metadata = await request(path + "?limit=100");
        const item = Array.isArray(metadata) && metadata.find(entry => entry.attachment_id === attachmentId
            && entry.conversation_id === cid && entry.state !== "DELETED");
        if (!item || !sha256Pattern.test(item.sha256)) return result("changed", {pending});
        const key = JSON.stringify([cid, attachmentId, documentOperation, item.sha256, reason]);
        if (pending && pending.key !== key) return result("retry_original", {pending});
        pending = {key, id: pending?.id ?? createId()};
        const recorded = await request(path + "/" + attachmentId + "/requests", {
            request_id: pending.id, source_sha256: item.sha256, operation: documentOperation, reason,
        });
        if (recorded?.request?.conversation_id !== cid || recorded.request.attachment_id !== attachmentId
            || recorded.request.operation !== documentOperation || recorded.request.source_sha256 !== item.sha256) {
            throw new Error("unavailable");
        }
        return projectRequest(recorded, pending.id);
    } catch (error) {
        if (["signed_out", "denied"].includes(error.message)) return result(error.message);
        if (["changed", "not_found"].includes(error.message)) return result(error.message);
        return result("unavailable", {pending});
    }
}
