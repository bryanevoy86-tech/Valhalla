import {ownerAttentionSession} from "./owner-attention.mjs";

const uuidPattern = /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i;

export function escapeConversationText(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[character]);
}

export async function runOwnerConversations(input, transport = fetch, createId = () => crypto.randomUUID()) {
    const {apiBase, previewOrigin, bearer, operation} = input;
    const session = ownerAttentionSession(bearer);
    if (!session) return {status: "signed_out"};
    const failure = (status) => ({status, session});
    const prior = input.prior?.session === session ? input.prior : {};
    let origin;
    try {
        const api = new URL(apiBase);
        const approved = new URL(previewOrigin);
        if (api.protocol !== "https:" || api.username || api.password || approved.origin !== previewOrigin
            || approved.origin !== api.origin) return failure("unconfigured");
        origin = approved.origin;
    } catch {
        return failure("unconfigured");
    }

    let pending = prior.pending ?? null;
    let writeRecorded = false;
    const base = origin + "/api/weweb/owner-conversations";
    const request = async (suffix, body) => {
        const response = await transport(base + suffix, {
            method: body ? "POST" : "GET", headers: {
                Authorization: "Bearer " + bearer, ...(body ? {"Content-Type": "application/json"} : {}),
            },
            body: body ? JSON.stringify(body) : undefined, cache: "no-store", credentials: "omit",
            redirect: "error", signal: AbortSignal.timeout(15000),
        });
        if (response.status === 401) throw new Error("signed_out");
        if (response.status === 403) throw new Error("denied");
        if (response.status === 404 || response.status === 409) throw new Error("conflict");
        if (body && response.status === 422) throw new Error("invalid_message");
        if (!response.ok) throw new Error("unavailable");
        return response.json();
    };
    const projectThread = (item) => {
        if (!item || !uuidPattern.test(item.conversation_id) || typeof item.title !== "string") {
            throw new Error("unavailable");
        }
        return {id: item.conversation_id, title: item.title};
    };
    const projectTurn = (item, cid) => {
        if (!item || item.conversation_id !== cid || !uuidPattern.test(item.turn_id)
            || typeof item.message !== "string" || typeof item.reply !== "string"
            || item.execution_authorized !== false || item.external_effects !== 0
            || !["DETERMINISTIC_READ_ONLY", "MODEL_ADVISORY_ONLY"].includes(item.response_mode)) {
            throw new Error("unavailable");
        }
        return {id: item.turn_id, message: item.message, reply: item.reply, mode: item.response_mode};
    };
    const writeId = (kind, key, details) => {
        if (pending && (pending.kind !== kind || pending.key !== key || pending.details !== details)) {
            throw new Error("retry_original");
        }
        pending = {kind, key, details, id: pending?.id ?? createId()};
        return pending.id;
    };

    let selected = prior.selected ?? null;
    let sent = prior.sent ?? null;
    try {
        if (operation === "create") {
            const title = input.title?.trim();
            if (!title || title.length > 160) return {...prior, status: "invalid_title", session};
            const id = writeId("create", "", title);
            const result = projectThread(await request("", {conversation_id: id, title}));
            if (result.id !== id || result.title !== title) throw new Error("unavailable");
            selected = result.id;
            pending = null;
            writeRecorded = true;
        }
        if (operation === "send") {
            const message = input.message?.trim();
            const decision = input.decision?.trim() || null;
            if (!message || message.length > 8000 || !uuidPattern.test(selected)
                || (decision && !uuidPattern.test(decision))) return {...prior, status: "invalid_message", session};
            const details = JSON.stringify({message, decision});
            if (sent?.thread === selected && sent.details === details) {
                return {...prior, status: "already_sent", session};
            }
            const id = writeId("send", selected, details);
            const result = projectTurn(await request("/" + selected + "/turns", {
                turn_id: id, message, provider_data_class: "PRIVATE", ...(decision ? {prime_decision_id: decision} : {}),
            }), selected);
            if (result.id !== id || result.message !== message || result.mode !== "DETERMINISTIC_READ_ONLY") {
                throw new Error("unavailable");
            }
            sent = {thread: selected, details};
            pending = null;
            writeRecorded = true;
        }

        const list = await request("?limit=20");
        if (!Array.isArray(list)) throw new Error("unavailable");
        const threads = list.map(projectThread);
        if (!threads.some(({id}) => id === selected)) selected = threads[0]?.id ?? null;
        if (operation === "next" && threads.length > 1) {
            const index = threads.findIndex(({id}) => id === selected);
            selected = threads[(index + 1) % threads.length].id;
        }
        if (!selected) return {status: "ready", session, threads, selected, turns: [], attachments: [], pending, sent};

        const history = await request("/" + selected + "/turns?limit=20");
        if (!Array.isArray(history)) throw new Error("unavailable");
        const turns = history.map(t => projectTurn(t, selected));
        let attachments = [], attachmentStatus = "ready";
        try {
            const inventory = await request("/" + selected + "/attachments?limit=10");
            if (!Array.isArray(inventory)) throw new Error("unavailable");
            attachments = inventory.map(file => {
                if (!file || file.conversation_id !== selected || !uuidPattern.test(file.attachment_id)
                    || typeof file.filename !== "string" || typeof file.state !== "string") {
                    throw new Error("unavailable");
                }
                return {id: file.attachment_id, filename: file.filename, state: file.state};
            });
        } catch (error) {
            if (["signed_out", "denied"].includes(error.message)) throw error;
            attachmentStatus = "unavailable";
        }
        return {status: "ready", session, threads, selected, turns, attachments, attachmentStatus, pending, sent};
    } catch (error) {
        if (["signed_out", "denied"].includes(error.message)) return failure(error.message);
        if (error.message === "retry_original") return {...prior, status: "retry_original", session};
        if (error.message === "invalid_message") return {...prior, status: "invalid_message", session, pending: null};
        return {status: writeRecorded ? "saved_refresh_required" : error.message === "conflict" ? "conflict" : "unavailable",
            session, threads: prior.threads ?? [], selected, pending: error.message === "conflict" ? null : pending, sent};
    }
}
