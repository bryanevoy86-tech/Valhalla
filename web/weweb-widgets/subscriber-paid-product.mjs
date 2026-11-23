import {ownerAttentionSession} from "./owner-attention.mjs";

const identifier = /^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$/;
const digest = /^[0-9a-f]{64}$/;
const deliveryBasis = new Set(["SYNTHETIC_DELIVERY_REHEARSAL", "PAID_ONE_TIME_PRODUCT"]);

export async function runSubscriberPaidProduct(input, transport = fetch, saveFile) {
    const session = ownerAttentionSession(input.bearer);
    if (!session) return {status:"signed_out"};
    const result = (status, details = {}) => ({status,session,...details});
    const tenant = typeof input.tenant === "string" ? input.tenant.trim().toLowerCase() : "";
    const order = typeof input.order === "string" ? input.order.trim().toLowerCase() : "";
    if (!identifier.test(tenant) || !identifier.test(order)) return result("invalid");
    let endpoint;
    try {
        const base = new URL(input.apiBase);
        const approved = new URL(input.previewOrigin);
        if (approved.protocol !== "https:" || approved.origin !== input.previewOrigin
            || base.origin !== approved.origin || base.username || base.password) return result("unconfigured");
        endpoint = approved.origin + "/api/weweb/paid-products/" + tenant + "/" + order;
    } catch {
        return result("unconfigured");
    }
    const acknowledge = input.action === "acknowledge";
    if (input.action !== "load" && !acknowledge) return result("invalid");
    if (acknowledge && (input.prior?.session !== session || input.prior?.tenant !== tenant
        || input.prior?.order !== order || !digest.test(input.prior?.grant))) return result("invalid");
    try {
        const options = {method:acknowledge ? "POST" : "GET", headers:{Authorization:"Bearer " + input.bearer},
            cache:"no-store", credentials:"omit", redirect:"error", signal:AbortSignal.timeout(15000)};
        if (acknowledge) {
            endpoint += "/acknowledge";
            options.headers["Content-Type"] = "application/json";
            options.body = JSON.stringify({grant_sha256:input.prior.grant});
        }
        const response = await transport(endpoint, options);
        if (response.status === 401) return result("signed_out");
        if (response.status === 403 || response.status === 404) return result("denied");
        if (response.status === 409) return result("held");
        if (!response.ok) return result("unavailable");
        const type = response.headers?.get("content-type")?.split(";")[0]?.trim();
        if (!acknowledge && type === "application/octet-stream") {
            const grant = response.headers.get("X-Delivery-Grant");
            if (!digest.test(grant) || typeof saveFile !== "function") return result("unavailable");
            const bytes = await response.blob();
            if (bytes.size < 1 || bytes.size > 5 * 1024 * 1024) return result("unavailable");
            if (await saveFile(bytes, order + ".bin") !== true) return result("unavailable");
            return result("offered", {tenant,order,grant});
        }
        if (type !== "application/json") return result("unavailable");
        const body = await response.json();
        if (body.order_id !== order || body.tenant_id !== tenant || !deliveryBasis.has(body.basis)
            || !digest.test(body.grant_sha256)) return result("unavailable");
        if (!acknowledge) {
            if (body.basis !== "SYNTHETIC_DELIVERY_REHEARSAL" || body.download_enabled !== false) {
                return result("unavailable");
            }
            return result("rehearsal", {tenant,order,grant:body.grant_sha256});
        }
        if (body.grant_sha256 !== input.prior.grant || body.buyer_acknowledged !== true
            || body.recognized_revenue_minor !== null || body.available_cash_minor !== null) return result("unavailable");
        return result(body.basis === "SYNTHETIC_DELIVERY_REHEARSAL" ? "rehearsal_acknowledged" : "acknowledged");
    } catch {
        return result("unavailable");
    }
}
