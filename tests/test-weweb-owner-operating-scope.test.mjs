import test from "node:test";
import assert from "node:assert/strict";
import {runOwnerOperatingScope,runOwnerStripeOrder} from "../web/weweb-widgets/owner-operating-scope.mjs";

const origin = "https://staging.example.invalid";
const token = "a." + Buffer.from(JSON.stringify({jti:"owner",exp:Math.floor(Date.now()/1000)+300})).toString("base64url") + ".b";
const scope = {legacy_instance_id:"scope-1",business_id:"shop-1",engine_id:"test-engine",jurisdiction:"CA-MB"};
const input = {scope,bearer:token,isOwner:true,apiBase:origin,previewOrigin:origin};
const empty = {status:"NO_SCOPED_FIXTURES",accounts:[],actual_accessible_funds_minor:null};
const body = {scope,execution_authorized:false,actual_accessible_funds_minor:null,
    legacy:{display_name:"<Legacy>",status:"PASS"},capital_fixture:null,
    statement_fixtures:{BUSINESS:empty,HOUSEHOLD:empty,OPERATING_RESERVE:empty}};
const respond = data => async () => ({status:200,ok:true,json:async()=>data});

test("the exact owner scope request renders separate statement purposes",async()=>{
    const outcome = await runOwnerOperatingScope(input,async(url,opts)=>{
        assert.equal(url,origin+"/api/weweb/owner-operating-scope");
        assert.equal(opts.cache,"no-store");
        assert.deepEqual(JSON.parse(opts.body),scope);
        return respond(body)();
    });
    assert.equal(outcome.status,"ready");
    assert.match(outcome.text,/&lt;Legacy&gt;/);
    assert.match(outcome.text,/Business treasury[\s\S]*Household budget[\s\S]*Protected operating reserves/);
});

test("the owner view refuses an authority claim, a scope mismatch or subscriber access",async()=>{
    assert.equal((await runOwnerOperatingScope(input,respond({...body,actual_accessible_funds_minor:1}))).status,"unavailable");
    assert.equal((await runOwnerOperatingScope(input,respond({...body,scope:{...scope,jurisdiction:"CA-ON"}}))).status,"unavailable");
    assert.equal((await runOwnerOperatingScope({...input,isOwner:false},()=>assert.fail("subscriber transport"))).status,"denied");
});

test("checks exact owner Stripe lookup and separates processor evidence from accessible cash",async()=>{
    const orderId = "59411e80-50d4-475f-b210-c20d07528154";
    const params = {...input,orderId};
    const projection = {order:{order_id:orderId,livemode:false,currency:"cad",amount_minor:1000},
        status:"MATCHED_PROCESSOR_EVIDENCE",bank_settlement_verified:false,available_cash_minor:null,
        fulfillment_authorized:false,entitlement_granted:false,
        processor_evidence:{basis:"STRIPE_TEST_PROCESSOR_BALANCE",bank_settlement_verified:false,
            ledger_posting_created:false,entitlement_granted:false,currency:"cad",gross_minor:1000,fee_minor:40,net_minor:960}};
    const result = await runOwnerStripeOrder(params,async(url,opts)=>{
        assert.equal(url,origin+"/api/weweb/owner-stripe-orders/"+orderId);
        assert.equal(opts.method,"GET");
        assert.equal(opts.cache,"no-store");
        return respond(projection)();
    });
    assert.equal(result.status,"ready");
    assert.match(result.text,/Test order[\s\S]*CAD\s9\.60[\s\S]*Bank settlement outstanding/);
    const bank = {basis:"SYNTHETIC_BANK_REHEARSAL",status:"RECONCILIATION_RECORDED",currency:"CAD",
        batch_minor:1920,order_contribution_minor:960,ledger_entry_id:null,available_cash_minor:null};
    const reconciled = await runOwnerStripeOrder(params,respond({...projection,bank_batch:bank}));
    assert.match(reconciled.text,/Bank reconciliation rehearsal recorded[\s\S]*CAD\s19\.20[\s\S]*CAD\s9\.60/);
    assert.equal((await runOwnerStripeOrder(params,respond({...projection,
        bank_batch:{...bank,ledger_entry_id:1}}))).status,"unavailable");
    assert.equal((await runOwnerStripeOrder(params,respond({...projection,entitlement_granted:true}))).status,"unavailable");
    assert.equal((await runOwnerStripeOrder(params,respond({...projection,order:{order_id:"wrong"}}))).status,"unavailable");
    assert.equal((await runOwnerStripeOrder({...params,isOwner:false},()=>assert.fail("subscriber transport"))).status,"denied");
});
