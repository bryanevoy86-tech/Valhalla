import test from "node:test";
import assert from "node:assert/strict";
import {runOwnerOperatingScope} from "../web/weweb-widgets/owner-operating-scope.mjs";

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
