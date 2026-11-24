const assert = require("node:assert/strict");
const {readFileSync} = require("node:fs");
const {chromium} = require("playwright");

async function run() {
    const fixture = JSON.parse(readFileSync(0, "utf8"));
    const origin = new URL(fixture.origin);
    assert.equal(origin.hostname, "127.0.0.1");
    const browser = await chromium.launch({executablePath:process.env.VALHALLA_BROWSER_EXECUTABLE});
    try {
        const context = await browser.newContext({serviceWorkers:"block"});
        await context.route("**/*", route =>
            new URL(route.request().url()).origin === origin.origin ? route.continue() : route.abort());
        const requests = [];
        const page = await context.newPage();
        const diagnostics = [];
        page.on("pageerror", error => diagnostics.push(error.message));
        page.on("console", message => { if (message.type() === "error") diagnostics.push(message.text()); });
        page.on("response", response => diagnostics.push([new URL(response.url()).pathname,
            response.status(), response.headers()["content-type"]]));
        page.on("request", request => {
            if (request.url().includes("/api/weweb/customer-research/")) requests.push(request);
        });
        await page.goto(new URL("/__acceptance/research.html?round=" + fixture.round, origin).href);
        const panel = page.locator("#research");
        const control = name => panel.locator("button").filter({hasText:new RegExp("^" + name + "$")});
        const click = locator => locator.evaluate(node => node.click());
        const start = control("Start interview");
        const attached = locator => locator.waitFor({state:"attached", timeout:8000});
        try {
            await attached(panel.getByText("Sign in to open your research invitation."));
            await page.getByLabel("Fixture email").evaluate((input, value) => { input.value = value; }, fixture.email);
            await page.getByLabel("Fixture password").evaluate((input, value) => { input.value = value; }, fixture.password);
            await page.locator("form").evaluate(form => form.requestSubmit());
            await attached(start);
        } catch (error) {
            throw new Error(JSON.stringify({diagnostics, status:await page.locator("#research").innerText(),
                login:await page.locator("#login-status").textContent()}), {cause:error});
        }
        assert.equal(await start.isDisabled(), true);
        await click(panel.locator("input[type=checkbox]"));
        await click(start);
        await attached(panel.getByText(/Did this workflow cause recurring work/));
        await click(control("No"));
        await attached(panel.getByText(/Interview complete/));
        await click(control("Withdraw and erase answers"));
        await attached(panel.getByText(/Your research answers were removed/));
        await click(page.locator("#signout"));
        await attached(panel.getByText(/Sign in to open your research invitation/));
        assert.ok(requests.length >= 4);
        for (const request of requests) {
            const headers = await request.allHeaders();
            assert.ok(headers.authorization.startsWith("Bearer "));
            assert.ok(!headers["x-prime-control-key"]);
            assert.ok(!headers["x-owner-mandate-key"]);
            assert.ok(!request.postData()?.includes('"token"'));
        }
        console.log(JSON.stringify({voluntary_consent:true, branched_question:true, withdrawn:true, prime_key_exposed:false}));
    } finally {
        await browser.close();
    }
}
run().catch(error => {console.error(error); process.exitCode = 1;});
