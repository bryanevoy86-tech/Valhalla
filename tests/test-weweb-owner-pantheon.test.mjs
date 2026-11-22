import test from "node:test";
import assert from "node:assert/strict";
import {runOwnerPantheon} from "../web/weweb-widgets/owner-pantheon.mjs";

const origin="https://preview.example.invalid";
const assignment="5df708e6-d759-444b-a1d0-f6768f39db3e";
const token="a."+Buffer.from(JSON.stringify({jti:"owner-fixture",exp:Math.floor(Date.now()/1000)+300})).toString("base64url")+".b";
const input={isOwner:true,bearer:token,apiBase:origin,previewOrigin:origin,role:"tyr"};
const item={assignment_id:assignment,role:"TYR",state:"VERIFIED_RECEIPT",report_event_id:"GOD-"+"a".repeat(64),
    report_sha256:"b".repeat(64),scope:{legacy_instance_id:"test-legacy",business_id:"test-shop",engine_id:"test-engine",
        jurisdiction:"test-scope"},observed_at:"2026-11-22T12:00:00Z",trigger:"CADENCE",assignment_state:"active",
    lens:"approval_evidence",report_status:"observed",observation_categories:["scoped_approvals"],
    independent_loki:{review_id:assignment,status:"completed",reconsideration_status:"required",findings:["<material finding>"]}};
const response=(reports,next_after=null)=>({status:200,ok:true,json:async()=>({reports,next_after,execution_authorized:false})});

test("paginates digest-verified scoped reports and displays independent findings as plain text", async()=>{
    const first=await runOwnerPantheon(input,async(url,req)=>{
        assert.equal(url,origin+"/api/weweb/owner-pantheon/reports?role=TYR");
        assert.equal(req.cache,"no-store");
        return response([item],assignment);
    });
    assert.match(first.text,/Reconsideration · required\n&lt;material finding&gt;/);
    const next=await runOwnerPantheon({...input,next:true,prior:first},async(url)=>{
        assert.equal(new URL(url).searchParams.get("after"),assignment);
        return response([{assignment_id:assignment,role:"TYR",state:"INTEGRITY_HOLD"}]);
    });
    assert.match(next.text,/Report integrity hold/);
    assert.equal(next.nextAfter,null);
    assert.equal((await runOwnerPantheon({...input,role:"NJORD",next:true,prior:first},
        async()=>assert.fail("Cursor used with a changed filter"))).status,"reload_required");
});

test("withholds malformed or out-of-role records and denies subscribers before transport", async()=>{
    assert.equal((await runOwnerPantheon(input,async()=>response([{...item,role:"NJORD"}]))).status,"unavailable");
    assert.equal((await runOwnerPantheon(input,async()=>response([{...item,report_sha256:"invalid"}]))).status,"unavailable");
    assert.equal((await runOwnerPantheon({...input,isOwner:false},async()=>assert.fail("Transport used"))).status,"denied");
});
