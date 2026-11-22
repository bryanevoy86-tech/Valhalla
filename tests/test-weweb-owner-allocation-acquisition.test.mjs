import test from "node:test";
import assert from "node:assert/strict";
import {runOwnerAllocationAcquisition} from "../web/weweb-widgets/owner-allocation-acquisition.mjs";

const origin="https://staging.example.invalid";
const bearer="a."+Buffer.from(JSON.stringify({jti:"fixture",exp:Math.floor(Date.now()/1000)+300})).toString("base64url")+".b";
const scope={legacy_instance_id:"legacy-01",business_id:"business-01",engine_id:"digital-engine",jurisdiction:"CA-MB"};
const base={isOwner:true,apiBase:origin,previewOrigin:origin,bearer};
const sha256="a".repeat(64);
const response=body=>({ok:true,status:200,json:async()=>body});

test("acquisition uses exact scoped campaign and rejects an asserted commercial result",async()=>{
    const input={...base,mode:"acquisition",campaign:"1",request:JSON.stringify(scope)};
    const receipt={scope,campaign_id:1,sha256,currency:"CAD",basis:"SETTLED_ACQUISITION_FIXTURE_ONLY",
        recommendation:"RECOMMEND_PAUSE",visits:2,settled_captures:1,positive_net_orders:0,unresolved_orders:0,
        verified_commercial_revenue:false,external_action_authorized:false,contribution_minor:-175};
    const result=await runOwnerAllocationAcquisition(input,async(url,options)=>{
        assert.equal(url,origin+"/api/weweb/owner-acquisition/1/settled-review");
        assert.equal(options.cache,"no-store");
        assert.deepEqual(JSON.parse(options.body),scope);
        return response(receipt);
    });
    assert.match(result.text,/RECOMMEND_PAUSE/);
    assert.equal((await runOwnerAllocationAcquisition(input,async()=>response({...receipt,verified_commercial_revenue:true}))).status,"unavailable");
});

test("allocation refuses authority claims and keeps subscribers outside the preview",async()=>{
    const statement_id="ab4c02da-4d31-4f92-949e-de1ad64aec66";
    const input={...base,mode:"allocation",request:JSON.stringify({scope,statement_id})};
    const receipt={scope,statement:{id:statement_id},sha256,currency:"CAD",basis:"RECONCILIATION_FIXTURE",
        actual_accessible_funds_minor:null,funds_movement_authorized:false,standing_mandate_approved:false,period:"2026-10-01",
        eligible_distributable_profit_minor:1000000,recommended_personal_minor:400000,
        remaining_eligible_for_reinvestment_minor:600000,personal_breakdown:{essentials_minor:300000,reserve_minor:100000},
        shortfalls:{essentials_minor:0},blockers:[]};
    const result=await runOwnerAllocationAcquisition(input,async(url)=>{
        assert.equal(url,origin+"/api/weweb/owner-personal-allocation");
        return response(receipt);
    });
    assert.match(result.text,/Personal recommendation · CAD\s4,000.00/);
    assert.equal((await runOwnerAllocationAcquisition(input,async()=>response({...receipt,standing_mandate_approved:true}))).status,"unavailable");
    assert.equal((await runOwnerAllocationAcquisition({...input,isOwner:false},()=>assert.fail("subscriber transport"))).status,"denied");
});
