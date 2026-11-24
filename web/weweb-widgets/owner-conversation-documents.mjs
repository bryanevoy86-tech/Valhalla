import {ownerAttentionSession} from "./owner-attention.mjs";
import {runOwnerConversations} from "./owner-conversations.mjs";

const attachmentTypes = new Set(["application/pdf", "image/jpeg", "image/png", "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]);
const attachmentIdentifier = /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i;

export async function runOwnerDocuments(input, transport = fetch, cryptography = globalThis.crypto) {
    const session = ownerAttentionSession(input.bearer);
    if (!session) return {status: "signed_out"};
    const prior = input.prior?.session === session ? input.prior : {};
    const result = (documentStatus, extra = {}) => ({...prior, ...extra, status: "ready", session, documentStatus});
    let origin;
    try {
        const api = new URL(input.apiBase);
        const approved = new URL(input.previewOrigin);
        if (api.protocol !== "https:" || api.username || api.password || approved.origin !== input.previewOrigin
            || approved.origin !== api.origin) return {status: "unconfigured", session};
        origin = approved.origin;
    } catch {
        return {status: "unconfigured", session};
    }
    if (!attachmentIdentifier.test(prior.selected)) return result("select_thread");
    const path = origin + "/api/weweb/owner-conversations/" + prior.selected + "/attachments";
    let pendingUpload = prior.pendingUpload ?? null;
    let storedUpload = prior.storedUpload ?? null;

    const request = async (suffix, method, body) => {
        const response = await transport(path + suffix, {method, headers: {
            Authorization: "Bearer " + input.bearer, ...(body ? {"Content-Type": "application/json"} : {}),
        }, body: body ? JSON.stringify(body) : undefined, cache: "no-store", credentials: "omit",
        redirect: "error", signal: AbortSignal.timeout(20000)});
        if (response.status === 401) throw new Error("signed_out");
        if (response.status === 403) throw new Error("denied");
        if (response.status === 409 || response.status === 410) throw new Error("document_conflict");
        if (response.status === 503) throw new Error("document_paused");
        if (!response.ok) throw new Error("document_unavailable");
        return response.json();
    };

    try {
        if (input.documentAction === "extract") {
            const target = prior.attachments?.find(item => item.state === "ACCEPT_LOCAL");
            if (!target || !attachmentIdentifier.test(target.id)) return result("review_required");
            const current = await request("?limit=10", "GET");
            const verified = Array.isArray(current) && current.find(item => item.attachment_id === target.id
                && item.conversation_id === prior.selected && item.state === "ACCEPT_LOCAL");
            if (!verified || !/^[0-9a-f]{64}$/.test(verified.sha256)) return result("review_required");
            const receipt = await request("/" + target.id + "/extract", "POST");
            if (receipt?.attachment_id !== target.id || receipt.source_sha256 !== verified.sha256
                || receipt.sent_to_provider !== false || receipt.execution_authorized !== false
                || receipt.evidence_class !== "UNTRUSTED_ATTACHMENT") return result("document_unavailable");
            return result("extracted", {extractionRef: target.id});
        }

        if (input.documentAction !== "upload") return result("document_unavailable");
        const files = input.files;
        const file = Array.isArray(files) && files.length === 1 ? files[0] : null;
        if (!file || !attachmentTypes.has(file.type) || typeof file.arrayBuffer !== "function"
            || typeof file.name !== "string" || !file.name || file.name.length > 180
            || !Number.isInteger(file.size) || file.size < 1 || file.size > 5 * 1024 * 1024) {
            return result("invalid_file");
        }
        const bytes = new Uint8Array(await file.arrayBuffer());
        if (bytes.length !== file.size) return result("invalid_file");
        const digest = [...new Uint8Array(await cryptography.subtle.digest("SHA-256", bytes))]
            .map(byte => byte.toString(16).padStart(2, "0")).join("");
        const key = JSON.stringify([prior.selected, file.name, file.type, digest]);
        if (storedUpload === key) return result("already_uploaded");
        if (pendingUpload && pendingUpload.key !== key) return result("retry_upload");
        pendingUpload = {key, id: pendingUpload?.id ?? cryptography.randomUUID()};
        let binary = "";
        for (let offset = 0; offset < bytes.length; offset += 8192) {
            binary += String.fromCharCode(...bytes.subarray(offset, offset + 8192));
        }
        const saved = await request("", "POST", {attachment_id: pendingUpload.id, filename: file.name,
            media_type: file.type, sha256: digest, content_base64: btoa(binary)});
        if (saved?.attachment_id !== pendingUpload.id || saved.conversation_id !== prior.selected
            || saved.sha256 !== digest || saved.analysis_complete !== false) return result("document_unavailable", {pendingUpload});
        pendingUpload = null;
        storedUpload = key;
        const refreshed = await runOwnerConversations({...input, prior, operation: "refresh"}, transport);
        if (["signed_out", "denied"].includes(refreshed.status)) return refreshed;
        return {...refreshed, pendingUpload, storedUpload,
            documentStatus: refreshed.status === "ready" ? "uploaded" : "uploaded_refresh"};
    } catch (error) {
        if (["signed_out", "denied"].includes(error.message)) return {status: error.message, session};
        const status = ["document_conflict", "document_paused"].includes(error.message) ? error.message : "document_unavailable";
        const blocked = status === "document_paused" || status === "document_conflict";
        return result(status, {pendingUpload: status === "document_conflict" ? null : pendingUpload, storedUpload,
            ...(blocked ? {attachments: [], attachmentStatus: "unavailable", extractionRef: null} : {})});
    }
}
