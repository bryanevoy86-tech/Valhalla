import assert from "node:assert/strict";
import test from "node:test";
import {runSubscriberPaidProduct} from "../web/weweb-widgets/subscriber-paid-product.mjs";

const tenant = "59411e80-50d4-475f-b210-c20d07528154";
const order = "914112fb-b634-4dc2-be12-e426e0fcd912";
const grant = "a".repeat(64);
const origin = "https://staging.example.invalid";
const bearer = "a." + Buffer.from(JSON.stringify({jti:"buyer",exp:Math.floor(Date.now()/1000)+300})).toString("base64url") + ".b";
const input = {tenant,order,bearer,apiBase:origin,previewOrigin:origin,action:"load"};
const sample = {order_id:order,tenant_id:tenant,grant_sha256:grant,basis:"SYNTHETIC_DELIVERY_REHEARSAL",download_enabled:false};
const response = body => ({status:200,ok:true,headers:new Headers({"Content-Type":"application/json"}),json:async()=>body});

test("authenticated subscriber checks exact payer order and rehearses separate acknowledgment", async()=>{
    const view = await runSubscriberPaidProduct(input,async(url,options)=>{
        assert.equal(url,origin+"/api/weweb/paid-products/"+tenant+"/"+order);
        assert.equal(options.headers.Authorization,"Bearer "+bearer);
        assert.equal(options.cache,"no-store");
        return response(sample);
    },()=>assert.fail("Rehearsal transferred bytes"));
    assert.equal(view.status,"rehearsal");
    const result = await runSubscriberPaidProduct({...input,action:"acknowledge",prior:view},async(url,options)=>{
        assert.match(url,/\/acknowledge$/);
        assert.equal(options.method,"POST");
        assert.deepEqual(JSON.parse(options.body),{grant_sha256:grant});
        return response({...sample,buyer_acknowledged:true,available_cash_minor:null,recognized_revenue_minor:null});
    });
    assert.equal(result.status,"rehearsal_acknowledged");
    assert.equal((await runSubscriberPaidProduct({...input,apiBase:"https://another.example.invalid"},
        ()=>assert.fail("Cross-origin transport"))).status,"unconfigured");
    assert.equal((await runSubscriberPaidProduct(input,async()=>response({...sample,tenant_id:order}))).status,"unavailable");
    assert.equal((await runSubscriberPaidProduct(input,async()=>({status:404}))).status,"denied");
});

test("offers only verified binary content and rejects a cross-order acknowledgment",async()=>{
    const binary = new Response(new Blob(["fixture"]),{headers:{"Content-Type":"application/octet-stream","X-Delivery-Grant":grant}});
    const result = await runSubscriberPaidProduct(input,async()=>binary,async(bytes,name)=>{
        assert.equal(await bytes.text(),"fixture");
        assert.equal(name,order+".bin");
        return true;
    });
    assert.equal(result.status,"offered");
    assert.equal((await runSubscriberPaidProduct({...input,order:tenant,action:"acknowledge",prior:result},
        ()=>assert.fail("Cross-order request"))).status,"invalid");
});
