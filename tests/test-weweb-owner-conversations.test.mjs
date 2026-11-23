import test from "node:test";
import assert from "node:assert/strict";
import {escapeConversationText, runOwnerConversations} from "../web/weweb-widgets/owner-conversations.mjs";

const origin = "https://preview.example.invalid";
const input = {apiBase: origin + "/api", previewOrigin: origin,
    bearer: "a." + Buffer.from(JSON.stringify({jti: "owner", exp: Math.ceil(Date.now() / 1000) + 300})).toString("base64url") + ".b"};
const thread = {conversation_id: "12345678-1234-4234-9234-123456789000", title: "Private fixture"};
const turnId = "12345678-1234-4234-9234-123456789001";
const decision = "12345678-1234-4234-9234-123456789002";
const turn = {conversation_id: thread.conversation_id, turn_id: turnId, message: "Review this decision",
    reply: "Local evidence", execution_authorized: false, external_effects: 0, response_mode: "DETERMINISTIC_READ_ONLY"};
const response = (status, body) => ({status, ok: status >= 200 && status < 300, json: async () => body});

function readFixtures(url, options) {
    assert.ok(url.startsWith(origin + "/api/weweb/owner-conversations"));
    assert.equal(options.headers.Authorization, "Bearer " + input.bearer);
    assert.equal(options.cache, "no-store");
    assert.equal(options.redirect, "error");
    if (url.endsWith("/turns?limit=20")) return response(200, [turn]);
    if (url.endsWith("/attachments?limit=10")) return response(503);
    return response(200, [thread]);
}

test("creates a thread and retrieves persistent history even when attachments are held", async () => {
    const value = await runOwnerConversations({...input, operation: "create", title: thread.title}, async (url, options) => {
        if (options.method === "POST") {
            assert.deepEqual(JSON.parse(options.body), thread);
            return response(201, thread);
        }
        return readFixtures(url, options);
    }, () => thread.conversation_id);
    assert.equal(value.status, "ready");
    assert.equal(value.selected, thread.conversation_id);
    assert.equal(value.turns[0].reply, turn.reply);
    assert.equal(value.attachmentStatus, "unavailable");
    assert.deepEqual(value.attachments, []);
    assert.equal(escapeConversationText("<img onerror='bad'>&"), "&lt;img onerror=&#39;bad&#39;&gt;&amp;");
});

test("retries a lost private turn using the same id and sends the exact Prime reference", async () => {
    const draft = {...input, operation: "send", prior: {session: "owner", selected: thread.conversation_id},
        message: turn.message, decision};
    const interrupted = await runOwnerConversations(draft, async () => { throw new Error("network"); }, () => turnId);
    assert.equal(interrupted.pending.id, turnId);
    assert.equal((await runOwnerConversations({...draft, message: "different", prior: interrupted},
        async () => { assert.fail("Must resolve original send first"); })).status, "retry_original");
    const saved = await runOwnerConversations({...draft, prior: interrupted}, async (url, options) => {
        if (options.method === "POST") {
            assert.deepEqual(JSON.parse(options.body), {turn_id: turnId, message: turn.message,
                provider_data_class: "PRIVATE", prime_decision_id: decision});
            return response(201, turn);
        }
        return readFixtures(url, options);
    }, () => assert.fail("Must reuse recorded request ID"));
    assert.equal(saved.pending, null);
    assert.equal(saved.turns.length, 1);
    assert.equal((await runOwnerConversations({...draft, prior: saved}, async () => {
        assert.fail("An unchanged sent draft must not be dispatched twice");
    })).status, "already_sent");
});

test("fails closed on revoked and subscriber sessions, cross-origin routing and untrusted history", async () => {
    const prior = {session: "owner", selected: thread.conversation_id, turns: [turn]};
    for (const [status, expected] of [[401, "signed_out"], [403, "denied"]]) {
        const result = await runOwnerConversations({...input, prior}, async () => response(status));
        assert.deepEqual(result, {status: expected, session: "owner"});
    }
    assert.equal((await runOwnerConversations({...input, previewOrigin: "https://other.example.invalid"}, async () => {
        assert.fail("Never send a private bearer to an unapproved origin");
    })).status, "unconfigured");
    const corrupted = await runOwnerConversations({...input, prior}, async (url, options) =>
        url.includes("/turns?") ? response(200, [{...turn, conversation_id: decision}]) : readFixtures(url, options));
    assert.equal(corrupted.status, "unavailable");
    assert.equal(corrupted.turns, undefined);
});

test("allows correction after the server rejects an incomplete startup checkpoint", async () => {
    const draft = {...input, operation: "send", prior: {session: "owner", selected: thread.conversation_id},
        message: "Record startup name"};
    const invalid = await runOwnerConversations(draft, async () => response(422), () => turnId);
    assert.equal(invalid.status, "invalid_message");
    assert.equal(invalid.pending, null);
    const message = "Record startup name | 2026-11-23 | fixture | Compare Manitoba";
    const saved = await runOwnerConversations({...draft, message, prior: invalid}, async (url, options) => {
        if (options.method === "POST") {
            assert.equal(JSON.parse(options.body).turn_id, decision);
            return response(201, {...turn, turn_id: decision, message});
        }
        return readFixtures(url, options);
    }, () => decision);
    assert.equal(saved.status, "ready");
    assert.equal(saved.pending, null);
});
