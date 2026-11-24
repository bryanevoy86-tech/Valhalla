import test from "node:test";
import assert from "node:assert/strict";
import {projectOwnerAttention, runOwnerAttention} from "../web/weweb-widgets/owner-attention.mjs";

const origin = "https://staging.example.invalid";
const token = (jti, exp = Math.ceil(Date.now() / 1000) + 600) =>
    "a." + Buffer.from(JSON.stringify({jti, exp})).toString("base64url") + ".b";
const input = {apiBase: origin + "/api", previewOrigin: origin, bearer: token("owner-session")};
const item = {notification_id: "review:reference-1", category: "review", reference: "reference-1"};
const inbox = (acknowledged_ids = []) => ({
    view: "PRIVATE_IN_APP", execution_authorized: false, entries: [item], acknowledged_ids,
});
const response = (status, body) => ({status, ok: status >= 200 && status < 300, json: async () => body});

test("requires an approved matching preview origin and an unexpired session before using a bearer", async () => {
    const never = () => { throw new Error("A request should not happen"); };
    assert.equal((await runOwnerAttention({...input, previewOrigin: ""}, never)).status, "unconfigured");
    assert.equal((await runOwnerAttention({...input, previewOrigin: "https://other.example.invalid"}, never)).status, "unconfigured");
    assert.equal((await runOwnerAttention({...input, bearer: token("expired", 0)}, never)).status, "signed_out");
});

test("maps private results and clears existing results on denial or malformed data", async () => {
    const ready = await runOwnerAttention(input, async (url, options) => {
        assert.equal(url, origin + "/api/weweb/owner-attention");
        assert.equal(options.headers.Authorization, "Bearer " + input.bearer);
        assert.equal(options.cache, "no-store");
        assert.equal(options.credentials, "omit");
        assert.equal(options.redirect, "error");
        return response(200, inbox());
    });
    assert.deepEqual(ready, {status: "ready", session: "owner-session", count: 1,
        nextId: item.notification_id, nextLabel: "Independent Loki review · reference-1"});
    assert.deepEqual(await runOwnerAttention({...input, prior: ready}, async () => response(403)), {
        status: "denied", session: "owner-session",
    });
    assert.equal((await runOwnerAttention(input, async () => response(401))).status, "signed_out");
    assert.equal((await runOwnerAttention(input, async () => response(200, {ok: true}))).status, "unavailable");
    assert.throws(() => projectOwnerAttention({...inbox(), entries: [{...item, reference: "<script>"}]}, "session"));
});

test("acknowledges one current item and refreshes only after a matching receipt", async () => {
    const prior = projectOwnerAttention(inbox(), "owner-session");
    assert.equal((await runOwnerAttention({...input, prior: {...prior, session: "old"}, acknowledge: true})).status,
        "refresh_required");
    const receipt = {notification_id: item.notification_id, acknowledged: true, execution_authorized: false,
        delivery_attempted: false};
    let calls = 0;
    const result = await runOwnerAttention({...input, prior, acknowledge: true}, async (url, options) => {
        calls += 1;
        if (calls === 1) {
            assert.equal(options.method, "POST");
            assert.ok(url.endsWith("/owner-attention/acknowledge"));
            assert.deepEqual(JSON.parse(options.body), {notification_id: item.notification_id});
            return response(200, receipt);
        }
        return response(200, inbox([item.notification_id]));
    });
    assert.equal(calls, 2);
    assert.equal(result.status, "ready");
    assert.equal(result.count, 0);
    assert.equal(result.nextId, null);
    assert.equal((await runOwnerAttention({...input, prior, acknowledge: true}, async () =>
        response(200, {...receipt, notification_id: "other"}))).status, "refresh_required");
});
