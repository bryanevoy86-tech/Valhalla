import assert from "node:assert/strict";
import test from "node:test";
import {runSubscriberStripeSubscription} from "../web/weweb-widgets/subscriber-stripe-subscription.mjs";

const claims = Buffer.from(JSON.stringify({jti:"stripe-test-session", exp:Math.floor(Date.now() / 1000) + 3600})).toString("base64url");
const input = {bearer:"example." + claims + ".mock", tenant:"a7ddd860-2e74-4e31-82c5-2376f817eff4", subscription:"7",
    apiBase:"https://preview.example.invalid", previewOrigin:"https://preview.example.invalid", action:"load"};
const reply = (body, status = 200) => new Response(JSON.stringify(body), {
    status, headers:{"Content-Type":"application/json", "Cache-Control":"no-store"},
});
const paid = {subscription_id:7, tenant_id:input.tenant, status:"PAID", basis:"STRIPE_TEST_SUBSCRIPTION",
    paid_until:1800000000, cancel_at_period_end:false, collection_status:"PAYMENT_RECOVERY",
    available_cash_minor:null, recognized_revenue_minor:null};

test("subscription status is private, scoped, and reports the existing paid period during recovery", async () => {
    const fixture = await runSubscriberStripeSubscription(input, async (url, options) => {
        assert.equal(url, input.apiBase + "/api/weweb/stripe-subscriptions/" + input.tenant + "/7");
        assert.equal(options.cache, "no-store");
        assert.equal(options.credentials, "omit");
        assert.equal(options.redirect, "error");
        return reply(paid);
    });
    assert.equal(fixture.status, "PAID");
    assert.equal(fixture.paymentRecovery, true);
    assert.equal(fixture.paidUntil, paid.paid_until);
    assert.equal((await runSubscriberStripeSubscription(input, async () => reply({...paid, tenant_id:"other"}))).status, "unavailable");
    assert.equal((await runSubscriberStripeSubscription(input, async () => reply({}, 404))).status, "denied");
    assert.equal((await runSubscriberStripeSubscription({...input, apiBase:"https://stolen.example.invalid"}, () => assert.fail())).status, "unconfigured");
});

test("checkout is an explicit hosted link and cancellation requires same-session confirmation", async () => {
    const checkout = {subscription_id:7, checkout_status:"open", checkout_url:"https://checkout.stripe.com/c/pay/demo",
        basis:"STRIPE_TEST_CHECKOUT", payment_verified:false};
    const starting = {...input, action:"checkout"};
    const opened = await runSubscriberStripeSubscription(starting, async (url, options) => {
        assert.match(url, /\/checkout$/);
        assert.equal(options.method, "POST");
        return reply(checkout);
    });
    assert.equal(opened.checkoutUrl, checkout.checkout_url);
    assert.equal((await runSubscriberStripeSubscription(starting, async () => reply({
        ...checkout, checkout_url:"https://checkout.stripe.com.example.invalid/c/pay/demo",
    }))).status, "unavailable");
    const prior = await runSubscriberStripeSubscription(input, async () => reply(paid));
    const cancel = {...input, action:"cancel", prior};
    assert.equal((await runSubscriberStripeSubscription(cancel, () => assert.fail())).status, "confirm");
    const canceled = await runSubscriberStripeSubscription({...cancel, confirm:true}, async (url, options) => {
        assert.match(url, /\/cancel-at-period-end$/);
        assert.equal(options.method, "POST");
        return reply({...paid, cancel_at_period_end:true});
    });
    assert.equal(canceled.cancellationScheduled, true);
    assert.equal(canceled.paidUntil, paid.paid_until);
});

test("owned-subscription inventory is read-only, session bound, and rejects extra financial fields", async () => {
    const listing = {...input, action:"list", subscription:null};
    const {tenant_id, available_cash_minor, recognized_revenue_minor, ...item} = paid;
    const record = {tenant_id, subscriptions:[item], external_effects:0, next_before:null};
    const read = await runSubscriberStripeSubscription(listing, async (url, options) => {
        assert.equal(url, input.apiBase + "/api/weweb/stripe-subscriptions/" + input.tenant);
        assert.equal(options.method, "GET");
        assert.equal(options.cache, "no-store");
        return reply(record);
    });
    assert.equal(read.status, "listed");
    assert.equal(read.session, "stripe-test-session");
    assert.equal(read.subscriptions[0].subscription_id, 7);
    assert.equal((await runSubscriberStripeSubscription(listing, async () => reply({
        ...record, subscriptions:[{...item, available_cash_minor}],
    }))).status, "unavailable");
    assert.equal((await runSubscriberStripeSubscription(listing, async () => reply({
        ...record, tenant_id:"elsewhere",
    }))).status, "unavailable");
});

test("completed service acknowledgment requires an exact session-bound invoice and prior digest", async () => {
    const period = {invoice_id:"in_paid", period_start:1770000000, period_end:1772419200,
        paid_period_sha256:"a".repeat(64)};
    const body = {tenant_id:input.tenant, subscription_id:7, basis:paid.basis, external_effects:0,
        completed_paid_periods:[period]};
    const history = await runSubscriberStripeSubscription({...input, action:"history"}, async (url, options) => {
        assert.match(url, /\/7\/service-history$/);
        assert.equal(options.method, "GET");
        assert.equal(options.cache, "no-store");
        return reply(body);
    });
    assert.equal(history.status, "service_history");
    assert.deepEqual(history.periods, [period]);
    const action = {...input, action:"acknowledge", invoice:"in_paid", prior:history};
    assert.equal((await runSubscriberStripeSubscription(action, () => assert.fail())).status, "confirm");
    const confirmed = {...action, confirm:true};
    assert.equal((await runSubscriberStripeSubscription({...confirmed, invoice:"in_other"},
        () => assert.fail())).status, "confirm");
    assert.equal((await runSubscriberStripeSubscription({...confirmed, prior:{...history, session:"changed"}},
        () => assert.fail())).status, "confirm");
    const receipt = {tenant_id:input.tenant, subscription_id:7, invoice_id:period.invoice_id,
        paid_period_sha256:period.paid_period_sha256, basis:"SYNTHETIC_SERVICE_ACK",
        sha256:"b".repeat(64), acknowledged_at:"2026-11-21T18:00:00Z"};
    const acknowledgment = await runSubscriberStripeSubscription(confirmed, async (url, options) => {
        assert.match(url, /\/7\/paid-period\/in_paid\/acknowledge$/);
        assert.equal(options.method, "POST");
        assert.deepEqual(JSON.parse(options.body), {paid_period_sha256:period.paid_period_sha256});
        return reply(receipt);
    });
    assert.equal(acknowledgment.status, "service_acknowledged");
    assert.equal(acknowledgment.basis, "SYNTHETIC_SERVICE_ACK");
    assert.equal((await runSubscriberStripeSubscription(confirmed, async () => reply({
        ...receipt, basis:"BUYER_SERVICE_ASSERTION",
    }))).status, "unavailable");
    assert.equal((await runSubscriberStripeSubscription(confirmed, async () => reply({}, 409))).status, "held");
});
