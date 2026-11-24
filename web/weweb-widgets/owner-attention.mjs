const labels = Object.freeze({
    integrity: "Integrity alert",
    prime_integrity: "Prime evidence needs verification",
    review: "Independent Loki review",
    prime_advisory: "Prime advisory",
    economic: "Economic alert",
    discovery: "Discovery alert",
    schedule: "Specialist schedule alert",
});

export function ownerAttentionSession(bearer, now = Date.now()) {
    try {
        const pieces = bearer.split(".");
        if (pieces.length !== 3) return null;
        const claims = JSON.parse(atob(pieces[1].replace(/-/g, "+").replace(/_/g, "/")));
        if (typeof claims.jti !== "string" || !claims.jti || !Number.isFinite(claims.exp) || claims.exp * 1000 <= now) {
            return null;
        }
        return claims.jti;
    } catch {
        return null;
    }
}

export function projectOwnerAttention(body, session) {
    if (body?.view !== "PRIVATE_IN_APP" || body.execution_authorized !== false
        || !Array.isArray(body.entries) || !Array.isArray(body.acknowledged_ids)) {
        throw new Error("Unexpected owner attention response");
    }
    const acknowledged = new Set(body.acknowledged_ids);
    const pending = body.entries.filter((item) => !acknowledged.has(item?.notification_id));
    for (const item of pending) {
        if (!item || !Object.hasOwn(labels, item.category) || typeof item.reference !== "string"
            || !/^[A-Za-z0-9_.:-]{1,120}$/.test(item.reference)
            || item.notification_id !== item.category + ":" + item.reference) {
            throw new Error("Unexpected owner attention item");
        }
    }
    const next = pending[0];
    return {status: "ready", session, count: pending.length, nextId: next?.notification_id ?? null,
        nextLabel: next ? labels[next.category] + " · " + next.reference : null};
}

export async function runOwnerAttention({apiBase, previewOrigin, bearer, prior, acknowledge = false}, transport = fetch) {
    const session = ownerAttentionSession(bearer);
    if (!session) return {status: "signed_out"};
    const failure = (status) => ({status, session});
    const fetchAttention = async (suffix, request = {}) => transport(origin + "/api/weweb/owner-attention" + suffix, {
        ...request, headers: {...request.headers, Authorization: "Bearer " + bearer},
        cache: "no-store", credentials: "omit", redirect: "error", signal: AbortSignal.timeout(12000),
    });

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
    let recorded = false;
    try {
        if (acknowledge) {
            if (prior?.session !== session || !prior.nextId) return failure("refresh_required");
            const receipt = await fetchAttention("/acknowledge", {
                method: "POST", headers: {"Content-Type": "application/json"},
                body: JSON.stringify({notification_id: prior.nextId}),
            });
            if (receipt.status === 401) return failure("signed_out");
            if (receipt.status === 403) return failure("denied");
            if (receipt.status === 404) return failure("refresh_required");
            if (!receipt.ok) return failure("unavailable");
            const result = await receipt.json();
            if (result?.notification_id !== prior.nextId || result.acknowledged !== true
                || result.execution_authorized !== false || result.delivery_attempted !== false) {
                return failure("refresh_required");
            }
            recorded = true;
        }
        const response = await fetchAttention("");
        if (response.status === 401) return failure("signed_out");
        if (response.status === 403) return failure("denied");
        if (!response.ok) return failure(recorded ? "acknowledged_refresh_required" : "unavailable");
        return projectOwnerAttention(await response.json(), session);
    } catch {
        return failure(recorded ? "acknowledged_refresh_required" : "unavailable");
    }
}
