import {ownerAttentionSession} from "./owner-attention.mjs";

const tenantId = /^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$/;
const actions = {list:"", load:"", checkout:"/checkout", cancel:"/cancel-at-period-end",
    history:"/service-history", acknowledge:""};
const states = ["PAID", "EVIDENCE_HELD", "NO_CURRENT_PAID_PERIOD"];
const bases = ["STRIPE_TEST_SUBSCRIPTION", "STRIPE_LIVE_SUBSCRIPTION"];
const collections = ["PAYMENT_RECOVERY", "NO_UNRESOLVED_FAILURE"];
const validId = value => typeof value === "number" && Number.isSafeInteger(value) && value > 0;
const listFields = ["subscription_id", "status", "basis", "paid_until", "cancel_at_period_end", "collection_status"];
const digest = /^[0-9a-f]{64}$/;
const invoiceId = /^in_[A-Za-z0-9_]{1,120}$/;
const completion = period => period && Object.keys(period).length === 4
    && typeof period.invoice_id === "string" && invoiceId.test(period.invoice_id)
    && typeof period.paid_period_sha256 === "string" && digest.test(period.paid_period_sha256)
    && validId(period.period_start) && validId(period.period_end) && period.period_start < period.period_end;

export async function runSubscriberStripeSubscription(input, transport = fetch) {
    const session = ownerAttentionSession(input.bearer);
    if (!session) return {status:"signed_out"};
    const tenant = String(input.tenant ?? "").trim().toLowerCase();
    const listing = input.action === "list";
    const subscription = listing ? null : Number(input.subscription);
    const result = (status, detail = {}) => ({status, session, tenant, subscription, ...detail});
    if (!tenantId.test(tenant) || !Object.hasOwn(actions, input.action)
        || (!listing && (!/^[1-9][0-9]*$/.test(String(input.subscription)) || !validId(subscription)))
        || (listing && input.before != null && !validId(input.before))) return result("invalid");
    if (input.action === "cancel" && (input.confirm !== true || input.prior?.session !== session
        || input.prior?.subscription !== subscription || input.prior?.tenant !== tenant
        || input.prior?.status !== "PAID")) return result("confirm");
    let confirmedPeriod;
    if (input.action === "acknowledge") {
        const prior = input.prior;
        if (input.confirm !== true || prior?.status !== "service_history" || prior.session !== session
            || prior.subscription !== subscription || prior.tenant !== tenant || !bases.includes(prior.basis)
            || !Array.isArray(prior.periods)) return result("confirm");
        confirmedPeriod = prior.periods.find(period => period?.invoice_id === input.invoice);
        if (!completion(confirmedPeriod)) return result("confirm");
    }
    let endpoint;
    try {
        const base = new URL(input.apiBase);
        const approved = new URL(input.previewOrigin);
        if (approved.protocol !== "https:" || approved.origin !== input.previewOrigin
            || base.origin !== approved.origin || base.username || base.password) return result("unconfigured");
        endpoint = approved.origin + "/api/weweb/stripe-subscriptions/" + tenant;
        if (listing && input.before != null) endpoint += "?before=" + input.before;
        if (!listing) endpoint += "/" + subscription + actions[input.action];
        if (confirmedPeriod) endpoint += "/paid-period/" + confirmedPeriod.invoice_id + "/acknowledge";
    } catch {
        return result("unconfigured");
    }
    try {
        const response = await transport(endpoint, {
            method: listing || input.action === "load" || input.action === "history" ? "GET" : "POST",
            headers: {Authorization:"Bearer " + input.bearer,
                ...(confirmedPeriod ? {"Content-Type":"application/json"} : {})},
            ...(confirmedPeriod ? {body:JSON.stringify({paid_period_sha256:confirmedPeriod.paid_period_sha256})} : {}),
            cache:"no-store", credentials:"omit", redirect:"error", signal:AbortSignal.timeout(15000),
        });
        if (response.status === 401) return result("signed_out");
        if (response.status === 403 || response.status === 404) return result("denied");
        if (response.status === 409) return result("held");
        if (!response.ok || response.headers.get("content-type")?.split(";")[0] !== "application/json") return result("unavailable");
        const body = await response.json();
        if (listing) {
            const items = body.subscriptions;
            if (body.tenant_id !== tenant || body.external_effects !== 0
                || !Array.isArray(items) || items.length > 20
                || !items.every((item, index) => item && validId(item.subscription_id)
                    && (index ? item.subscription_id < items[index - 1].subscription_id
                        : input.before == null || item.subscription_id < input.before)
                    && Object.keys(item).length === listFields.length
                    && listFields.every(field => Object.hasOwn(item, field))
                    && states.includes(item.status) && bases.includes(item.basis)
                    && collections.includes(item.collection_status) && typeof item.cancel_at_period_end === "boolean"
                    && (item.status !== "PAID" && item.paid_until === null || validId(item.paid_until)))
                || (body.next_before !== null && (items.length !== 20
                    || body.next_before !== items.at(-1).subscription_id))) return result("unavailable");
            return result("listed", {subscriptions:items, nextBefore:body.next_before});
        }
        if (body.subscription_id !== subscription) return result("unavailable");
        if (input.action === "history") {
            const periods = body.completed_paid_periods;
            if (body.tenant_id !== tenant || !bases.includes(body.basis) || body.external_effects !== 0
                || Object.keys(body).length !== 5 || !Array.isArray(periods) || periods.length > 20
                || !periods.every(completion) || new Set(periods.map(period => period.invoice_id)).size !== periods.length) {
                return result("unavailable");
            }
            return result("service_history", {basis:body.basis, periods});
        }
        if (confirmedPeriod) {
            const expectedBasis = input.prior.basis === "STRIPE_TEST_SUBSCRIPTION"
                ? "SYNTHETIC_SERVICE_ACK" : "BUYER_SERVICE_ASSERTION";
            if (body.tenant_id !== tenant || body.invoice_id !== confirmedPeriod.invoice_id
                || body.paid_period_sha256 !== confirmedPeriod.paid_period_sha256 || body.basis !== expectedBasis
                || typeof body.sha256 !== "string" || !digest.test(body.sha256)
                || !Number.isFinite(Date.parse(body.acknowledged_at))) return result("unavailable");
            return result("service_acknowledged", {basis:body.basis, invoice:body.invoice_id,
                acknowledgedAt:body.acknowledged_at});
        }
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
        if (body.tenant_id !== tenant || !states.includes(body.status)
            || !bases.includes(body.basis)
            || body.available_cash_minor !== null || body.recognized_revenue_minor !== null
            || !collections.includes(body.collection_status)
            || (input.action === "cancel" && body.cancel_at_period_end !== true)) return result("unavailable");
        const paidUntil = body.status === "PAID" && Number.isSafeInteger(body.paid_until) ? body.paid_until : null;
        if (body.status === "PAID" && !paidUntil) return result("unavailable");
        return result(body.status, {basis:body.basis, paidUntil, cancellationScheduled:body.cancel_at_period_end === true,
            paymentRecovery:body.collection_status === "PAYMENT_RECOVERY"});
    } catch {
        return result("unavailable");
    }
}
