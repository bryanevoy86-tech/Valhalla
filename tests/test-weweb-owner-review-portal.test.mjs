import test from "node:test";
import assert from "node:assert/strict";
import {escapeOwnerReviewText, runOwnerReviewPortal} from "../web/weweb-widgets/owner-review-portal.mjs";

const origin = "https://staging.example.invalid";
const id = "39209f48-f466-4451-8d5c-8186c97f23fb";
const cid = "35f566ee-cc8d-4cad-94c6-1fc08cf397e8";
const aid = "84cef018-cf79-4ebf-97c8-d1a169f63584";
const digest = "a".repeat(64);
const owner = "a." + Buffer.from(JSON.stringify({jti: "owner", exp: Math.ceil(Date.now()/1000) + 300})).toString("base64url") + ".b";
const base = {apiBase: origin + "/api", previewOrigin: origin, bearer: owner, isOwner: true};
const response = (status, body) => ({status, ok: status >= 200 && status < 300, json: async () => body});
const pendingReceipt = {status:"PENDING_MANDATE",request_sha256:digest,receipt:null,execution_authorized:false,
    provider_forwarding_authorized:false,request:{request_id:id,attachment_id:aid,conversation_id:cid,
        source_sha256:digest,operation:"DISPOSE"}};

test("a disposal click only journals an exact owner request", async () => {
    let calls=0;
    const intent={...base,operation:"dispose",attachment:aid,reason:"reviewed fixture",
        conversation:{session:"owner",selected:cid}};
    const send=async (url, opts) => {
        calls++;
        assert.equal(opts.headers.Authorization, "Bearer "+owner);
        assert.equal(opts.cache, "no-store");
        assert.equal(Object.keys(opts.headers).length, opts.method==="GET" ? 1 : 2);
        if (opts.method==="GET") return response(200,[{conversation_id:cid,attachment_id:aid,sha256:digest,state:"ACCEPT_LOCAL"}]);
        assert.equal(url, origin+"/api/weweb/owner-conversations/"+cid+"/attachments/"+aid+"/requests");
        assert.deepEqual(JSON.parse(opts.body), {request_id:id,source_sha256:digest,operation:"DISPOSE",reason:"reviewed fixture"});
        return response(201,pendingReceipt);
    };
    const recorded=await runOwnerReviewPortal(intent,send,()=>id);
    assert.equal(calls,2);
    assert.equal(recorded.document.state,"PENDING_MANDATE");
    const conflicting=await runOwnerReviewPortal({...base,operation:"status",reference:id}, async () =>
        response(200,{...pendingReceipt,status:"APPLIED",receipt:{state:"DELETED",attachment_id:aid,sha256:"b".repeat(64)}}));
    assert.equal(conflicting.status,"unavailable");
    const verified=await runOwnerReviewPortal({...base,operation:"status",reference:id}, async () =>
        response(200,{...pendingReceipt,status:"APPLIED",receipt:{state:"DELETED",attachment_id:aid,sha256:digest}}));
    assert.equal(verified.document.state,"APPLIED");
});

test("reads only matching Prime and specialist records while protecting the owner boundary", async () => {
    const prime={execution_authorized:false,prime_decision_id:id,evidence_class:"REVIEWED_INTERNAL_RECOMMENDATION",
        heimdall_decision:"HOLD",independent_loki:{review_id:cid,proposal_sha256:digest,ok_to_proceed:false,
            reconsideration_status:"required",findings:["<script>"]},reviewed_mimir_outcomes:[{}]};
    const view=await runOwnerReviewPortal({...base,operation:"prime",reference:id}, async () => response(200,prime));
    assert.equal(view.evidence.mimir,1);
    assert.equal(view.evidence.cleared,false);
    assert.equal(escapeOwnerReviewText(view.evidence.findings[0]),"&lt;script&gt;");
    assert.equal((await runOwnerReviewPortal({...base,operation:"prime",reference:aid},
        async () => response(200,prime))).status,"unavailable");
    assert.equal((await runOwnerReviewPortal({...base,isOwner:false},async()=>assert.fail("subscriber fetched"))).status,"denied");
    assert.equal((await runOwnerReviewPortal({...base,previewOrigin:""},async()=>assert.fail("unconfigured fetch"))).status,"unconfigured");
    const specialist={schedule_id:id,evidence_class:"INTERNAL_ADVISORY",report_event_id:"GOD-fixture",
        execution_authorized:false,independent_loki_cleared:false,status:"observed",operating_reassessment:{blockers:["CHECKOUT_HOLD"]}};
    assert.deepEqual((await runOwnerReviewPortal({...base,operation:"specialist",reference:id},
        async()=>response(200,specialist))).evidence.blockers,["CHECKOUT_HOLD"]);
});
