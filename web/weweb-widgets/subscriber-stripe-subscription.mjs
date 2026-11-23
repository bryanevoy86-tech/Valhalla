import {ownerAttentionSession} from "./owner-attention.mjs";

const tenantId = /^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$/;
const actions = {load:"", checkout:"/checkout", cancel:"/cancel-at-period-end"};

export async function runSubscriberStripeSubscription(input, transport = fetch) {
    const session = ownerAttentionSession(input.bearer);
    if (!session) return {status:"signed_out"};
    const tenant = String(input.tenant ?? "").trim().toLowerCase();
    const subscription = Number(input.subscription);
    const result = (status, detail = {}) => ({status, session, tenant, subscription, ...detail});
    if (!tenantId.test(tenant) || !/^[1-9][0-9]*$/.test(String(input.subscription))
        || !Number.isSafeInteger(subscription) || !Object.hasOwn(actions, input.action)) return result("invalid");
    if (input.action === "cancel" && (input.confirm !== true || input.prior?.session !== session
        || input.prior?.subscription !== subscription || input.prior?.tenant !== tenant
        || input.prior?.status !== "PAID")) return result("confirm");
    let endpoint;
    try {
        const base = new URL(input.apiBase);
        const approved = new URL(input.previewOrigin);
        if (approved.protocol !== "https:" || approved.origin !== input.previewOrigin
            || base.origin !== approved.origin || base.username || base.password) return result("unconfigured");
        endpoint = approved.origin + "/api/weweb/stripe-subscriptions/" + tenant + "/" + subscription + actions[input.action];
    } catch {
        return result("unconfigured");
    }
    try {
        const response = await transport(endpoint, {
            method: input.action === "load" ? "GET" : "POST",
            headers: {Authorization:"Bearer " + input.bearer},
            cache:"no-store", credentials:"omit", redirect:"error", signal:AbortSignal.timeout(15000),
        });
        if (response.status === 401) return result("signed_out");
        if (response.status === 403 || response.status === 404) return result("denied");
        if (response.status === 409) return result("held");
        if (!response.ok || response.headers.get("content-type")?.split(";")[0] !== "application/json") return result("unavailable");
        const body = await response.json();
        if (body.subscription_id !== subscription) return result("unavailable");
        if (input.action === "checkout") {
            if (!["STRIPE_TEST_CHECKOUT", "STRIPE_LIVE_CHECKOUT"].includes(body.basis)
                || body.payment_verified !== false) return result("unavailable");
            if (["complete", "expired"].includes(body.checkout_status) && body.checkout_url === null) {
                return result(body.checkout_status, {basis:body.basis});
            }
            const url = new URL(body.checkout_url);
            if (body.checkout_status !== "open" || url.origin !== "https://checkout.stripe.com"
                || url.username || url.password) return result("unavailable");
            return result("checkout_ready", {basis:body.basis, checkoutUrl:url.href});
        }
        if (body.tenant_id !== tenant || !["PAID", "EVIDENCE_HELD", "NO_CURRENT_PAID_PERIOD"].includes(body.status)
            || !["STRIPE_TEST_SUBSCRIPTION", "STRIPE_LIVE_SUBSCRIPTION"].includes(body.basis)
            || body.available_cash_minor !== null || body.recognized_revenue_minor !== null
            || !["PAYMENT_RECOVERY", "NO_UNRESOLVED_FAILURE"].includes(body.collection_status)
            || (input.action === "cancel" && body.cancel_at_period_end !== true)) return result("unavailable");
        const paidUntil = body.status === "PAID" && Number.isSafeInteger(body.paid_until) ? body.paid_until : null;
        if (body.status === "PAID" && !paidUntil) return result("unavailable");
        return result(body.status, {basis:body.basis, paidUntil, cancellationScheduled:body.cancel_at_period_end === true,
            paymentRecovery:body.collection_status === "PAYMENT_RECOVERY"});
    } catch {
        return result("unavailable");
    }
}
