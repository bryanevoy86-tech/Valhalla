import test from "node:test";
import assert from "node:assert/strict";
import {webcrypto} from "node:crypto";
import {runOwnerDocuments} from "../web/weweb-widgets/owner-conversation-documents.mjs";

const origin = "https://preview.example.invalid";
const thread = "12345678-1234-4234-9234-123456789000";
const attachment = "12345678-1234-4234-9234-123456789001";
const input = {apiBase: origin + "/api", previewOrigin: origin,
    bearer: "a." + Buffer.from(JSON.stringify({jti: "owner", exp: Math.ceil(Date.now() / 1000) + 300})).toString("base64url") + ".b",
    prior: {selected: thread, session: "owner", attachments: [{id: attachment, state: "ACCEPT_LOCAL"}]}};
const response = (status, body) => ({status, ok: status < 300, json: async () => body});
const digest = "a".repeat(64);

test("prepares and retries an exact private file without sending it outside the approved origin", async () => {
    const bytes = new TextEncoder().encode("fixture");
    const upload = {...input, documentAction: "upload", files: [{
        name: "fixture.txt", type: "text/plain", size: bytes.length, arrayBuffer: async () => bytes.buffer,
    }]};
    const unavailable = await runOwnerDocuments(upload, async () => { throw new Error("interrupted"); }, webcrypto);
    assert.equal(unavailable.documentStatus, "document_unavailable");
    const id = unavailable.pendingUpload.id;
    const saved = await runOwnerDocuments({...upload, prior: unavailable}, async (url, options) => {
        assert.ok(url.startsWith(origin + "/api/weweb/owner-conversations"));
        assert.equal(options.cache, "no-store");
        if (options.method === "POST") {
            const payload = JSON.parse(options.body);
            assert.equal(payload.attachment_id, id);
            assert.equal(payload.content_base64, Buffer.from("fixture").toString("base64"));
            assert.match(payload.sha256, /^[0-9a-f]{64}$/);
            return response(201, {...payload, conversation_id: thread, analysis_complete: false});
        }
        return response(200, []);
    }, webcrypto);
    assert.equal(saved.documentStatus, "uploaded");
    assert.equal(saved.pendingUpload, null);
    assert.equal((await runOwnerDocuments({...upload, previewOrigin:"https://other.example.invalid"}, async () => {
        assert.fail("Unexpected request");
    }, webcrypto)).status, "unconfigured");
});

test("extracts only a current reviewed source and clears file metadata on restore hold", async () => {
    const extract = {...input, documentAction: "extract"};
    let calls = 0;
    const approved = await runOwnerDocuments(extract, async (url, options) => {
        calls++;
        if (options.method === "GET") return response(200, [{attachment_id: attachment,
            conversation_id: thread, state: "ACCEPT_LOCAL", sha256: digest}]);
        assert.ok(url.endsWith("/" + attachment + "/extract"));
        return response(200, {attachment_id: attachment, source_sha256: digest, sent_to_provider: false,
            execution_authorized: false, evidence_class: "UNTRUSTED_ATTACHMENT"});
    });
    assert.equal(calls, 2);
    assert.equal(approved.documentStatus, "extracted");
    assert.equal(approved.extractionRef, attachment);
    const denied = await runOwnerDocuments(extract, async (url, options) => {
        assert.equal(options.method, "GET");
        return response(200, [{attachment_id: attachment, conversation_id: thread, state: "RETENTION_EXPIRED"}]);
    });
    assert.equal(denied.documentStatus, "review_required");
    const paused = await runOwnerDocuments(extract, async () => response(503));
    assert.equal(paused.documentStatus, "document_paused");
    assert.deepEqual(paused.attachments, []);
    assert.equal(paused.extractionRef, null);
});
