import test from "node:test";
import assert from "node:assert/strict";
import {runOwnerStartup} from "../web/weweb-widgets/owner-startup.mjs";

const origin = "https://staging.example.invalid";
const token = "a." + Buffer.from(JSON.stringify({jti:"owner-fixture",exp:Math.floor(Date.now()/1000)+300})).toString("base64url") + ".b";
const input = {isOwner:true,bearer:token,apiBase:origin,previewOrigin:origin,manitoba:true,named:false,jurisdiction:"Panama"};
const fixture = {
    currency:"CAD",as_of:"2026-11-22",selected_jurisdiction:null,activation_authorized:false,external_effects:0,
    options:["MANITOBA","FEDERAL_CANADA","INTERNATIONAL_FIRST"].map((route,i)=>({
        route,jurisdiction:["Manitoba","Canada (federal)","Panama"][i],route_review:"Qualified review required",objectives:{},
        activation:{items:[{label:"Public filing",amount_minor:35000,basis:"VERIFIED_GOVERNMENT_FEE"}],
            known_and_estimated_minor:35000,additional_capital_floor_minor:0,minimum_additional_capital_minor:null,
            unpriced_keys:["legal"]},
        operating:{incremental_recurring_items:[],existing_committed_monthly_minor:5000,known_annual_cost_minor:60000,
            reserve_gap_minor:200000,known_cost_runway_months:4},
    })),
    checklist:[{sequence:1,step:"Review scenario",requires:["OWNER"]}],professional_review_packets:[],
};
const ok = data => ({status:200,ok:true,json:async()=>data});

test("runs read-only startup comparison with the exact CAD budget and source boundary", async()=>{
    const outcome=await runOwnerStartup({...input,details:'{"startup_cash_available_minor": 50000}'},async(url,req)=>{
        assert.equal(url,origin+"/api/weweb/owner-startup/compare");
        assert.equal(req.cache,"no-store");
        assert.deepEqual(JSON.parse(req.body),{manitoba_operations:true,named_corporation:false,
            international_jurisdiction:"Panama",startup_cash_available_minor:50000});
        return ok(fixture);
    });
    assert.equal(outcome.status,"ready");
    assert.match(outcome.summary,/Minimum additional capital · Unavailable/);
    assert.match(outcome.summary,/Known and estimated activation subtotal · CAD\s350\.00/);
    assert.match(outcome.summary,/Known annual operating costs · CAD\s600\.00/);
    assert.match(outcome.summary,/Startup checklist/);
});

test("preserves draft provenance and rejects an asserted approval, disclosure or stale session", async()=>{
    const packet={status:"DRAFT_AWAITING_QUALIFIED_REVIEW",professional_signoff:null,opinion_reference:null,
        reliance_authorized:false,jurisdiction:"Panama",topic:"TAX_RESIDENCY",
        facts:[{basis:"OWNER_REPORTED",label:"Fixture",statement:"<script>",observed_on:"2026-11-22",source_reference:"owner:fixture"}],
        questions:["What evidence is required?"]};
    const form={...input,details:'{"professional_review":[{}]}'};
    const response=professional=>async()=>ok({...fixture,professional_review_packets:[professional]});
    const draft=await runOwnerStartup(form,response(packet));
    assert.match(draft.professional,/Owner-reported.*&lt;script&gt;/);
    assert.equal((await runOwnerStartup(form,response({...packet,reliance_authorized:true}))).status,"unavailable");
    assert.equal((await runOwnerStartup(input,async()=>({status:401}))).status,"signed_out");
    const none=async()=>assert.fail("Unexpected network request");
    assert.equal((await runOwnerStartup({...input,isOwner:false},none)).status,"denied");
    assert.equal((await runOwnerStartup({...input,previewOrigin:""},none)).status,"unconfigured");
    assert.equal((await runOwnerStartup({...input,details:'{"selected_jurisdiction":"MANITOBA"}'},none)).status,"invalid");
});
