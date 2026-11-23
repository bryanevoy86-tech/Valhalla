import test from "node:test";
import assert from "node:assert/strict";
import {runOwnerIndependence, runOwnerStartup} from "../web/weweb-widgets/owner-startup.mjs";

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

test("binds the private startup independence form and refuses unsupported cash and authority", async()=>{
    const review = {
        currency:"CAD",basis:"PRIVATE_STARTUP_PLANNING",external_action_authorized:false,
        borrowing_authorized:false,transfers_authorized:false,contingency_activation_authorized:false,
        verified_available_cash_minor:null,verified_after_tax_income_minor:null,support_forecast_minor:null,
        stretch_guaranteed:false,registration_date:"2026-11-08",
        reviews:[{day:15,due:"2026-11-23",focus:"PILOT_READINESS",status:"UPCOMING"}],
        capital_scenarios:[{hypothetical_extra_contribution_minor:0,total_plan_gap_minor:17000,experiment_headroom_minor:0}],
        funding:[{kind:"GRANT",status:"APPROVED",amount_minor:10000,included_in_spendable_cash_minor:0}],
        reporting:{official_or_case_evidence_verified:false,status:"DRAFT_REQUIRES_OFFICIAL_AND_CASE_REVIEW",checklist:[]},
    };
    const form = {...input,details:'{"registration_date":"2026-11-08"}'};
    const result = await runOwnerIndependence(form,async(url,req)=>{
        assert.equal(url,origin+"/api/weweb/owner-startup/independence-review");
        assert.equal(req.cache,"no-store");
        assert.equal(req.redirect,"error");
        assert.equal(req.headers.Authorization,"Bearer " + token);
        assert.deepEqual(JSON.parse(req.body),{registration_date:"2026-11-08"});
        return ok(review);
    });
    assert.equal(result.status,"ready");
    assert.match(result.summary,/Day 15 · 2026-11-23/);
    assert.match(result.summary,/CAD\s0\.00 extra contribution · gap CAD\s170\.00/);
    assert.match(result.summary,/grant · approved/);
    const response = data => async()=>ok(data);
    assert.equal((await runOwnerIndependence(form,response({...review,verified_available_cash_minor:10000}))).status,"unavailable");
    assert.equal((await runOwnerIndependence(form,response({...review,borrowing_authorized:true}))).status,"unavailable");
    const none = async()=>assert.fail("Unexpected network request");
    assert.equal((await runOwnerIndependence({...form,isOwner:false},none)).status,"denied");
    assert.equal((await runOwnerIndependence({...form,previewOrigin:""},none)).status,"unconfigured");
    assert.equal((await runOwnerIndependence({...form,details:"[]"},none)).status,"invalid");
});

test("shows dependencies by gate and rejects fabricated completion", async () => {
    const item = {service:"Stripe <test>",gate:"FIRST_REVENUE",why:"Verify exact payments",when:"During commissioning",
        setup_cost:"Confirm setup cost",ongoing_cost:"Confirm tariff",permissions:"Restricted read",
        alternative:"Test mode",owner_action:"Approve sandbox",verification:"Replay the signed event",
        evidence_status:"UNVERIFIED_IN_THIS_VIEW"};
    const dependencies = {basis:"PRIVATE_STARTUP_DEPENDENCY_GUIDANCE",activation_authorized:false,external_effects:0,
        lane:"ONE_TIME_CAD",dependencies:[item]};
    const result = await runOwnerStartup(input, async () => ok({...fixture,startup_dependencies:dependencies}));
    assert.equal(result.status,"ready");
    assert.match(result.summary,/Before first revenue · Stripe &lt;test&gt;/);
    assert.match(result.summary,/Owner action · Approve sandbox/);
    const forged = {...dependencies,dependencies:[{...item,evidence_status:"VERIFIED"}]};
    assert.equal((await runOwnerStartup(input, async () => ok({...fixture,startup_dependencies:forged}))).status,"unavailable");
});
