const assert = require("node:assert/strict");
const {readFileSync} = require("node:fs");
const {chromium} = require("playwright");

async function run() {
    const fixture = JSON.parse(readFileSync(0, "utf8"));
    const origin = new URL(fixture.origin);
    assert.equal(origin.hostname, "127.0.0.1");
    assert.equal(origin.protocol, "http:");
    assert.equal(origin.href, origin.origin + "/");
    const browser = await chromium.launch();
    try {
        const blocked = [];
        // Insert synthetic fixture values without relying on a desktop keyboard.
        const field = (page, label, value) => page.getByLabel(label).evaluate((input, fixtureValue) => {
            input.value = fixtureValue;
        }, value);
        async function pageFor(email) {
            const context = await browser.newContext({serviceWorkers: "block"});
            await context.route("**/*", route => {
                if (new URL(route.request().url()).origin === origin.origin) return route.continue();
                blocked.push("Unexpected off-origin request");
                return route.abort();
            });
            const page = await context.newPage();
            page.on("pageerror", error => console.error(error.message));
            await page.goto(origin.href + "__acceptance/");
            await field(page, "Fixture email", email);
            await field(page, "Fixture password", fixture.password);
            assert.equal(await page.getByLabel("Fixture email").inputValue(), email);
            assert.equal(await page.getByLabel("Fixture password").inputValue() === fixture.password, true);
            return page;
        }

        async function action(page, name, expected) {
            await page.getByRole("button", {name, exact: true}).click();
            try {
                await page.locator("#status").filter({hasText: new RegExp(`^HTTP ${expected}$`)}).waitFor({
                    state: "attached", timeout: 8000,
                });
            } catch (error) {
                const actual = await page.locator("#status").textContent();
                throw new Error(`${name} expected HTTP ${expected}, observed ${actual}`, {cause: error});
            }
            return JSON.parse(await page.locator("#result").textContent());
        }

        const owner = await pageFor(fixture.owner);
        const buyer = await pageFor(fixture.buyer);
        await action(owner, "Read owner briefing", 401);
        assert.equal((await action(owner, "Sign in", 200)).signed_in, true);
        assert.equal((await action(buyer, "Sign in", 200)).signed_in, true);
        const briefing = await action(owner, "Read owner briefing", 200);
        assert.equal(briefing.emergency_stop, fixture.phase === "stopped");
        await action(buyer, "Read owner briefing", 403);
        const stop = fixture.phase === "stopped"
            ? await action(owner, "Check stop authority", 401)
            : null;

        const report = {phase: fixture.phase, anonymous: 401, owner: 200, buyer: 403,
            emergency_stop: briefing.emergency_stop};
        if (stop) {
            report.owner_session_stop_mutation = 401;
        } else {
            for (const page of [owner, buyer]) await field(page, "Prime decision ID", fixture.decision);
            const decision = await action(owner, "Read reviewed decision", 200);
            assert.equal(decision.prime_decision_id, fixture.decision);
            assert.equal(decision.independent_loki.review_id, fixture.review);
            assert.equal(decision.independent_loki.result_sha256, fixture.result_digest);
            assert.deepEqual(decision.reviewed_mimir_outcomes, fixture.mimir);
            assert.equal(decision.execution_authorized, false);
            await action(buyer, "Read reviewed decision", 403);

            for (const page of [owner, buyer]) await field(page, "Conversation ID", fixture.conversation);
            await action(buyer, "Create startup conversation", 403);
            await action(owner, "Create startup conversation", 201);
            async function turn(message, expected = 201) {
                await field(owner, "Startup message", message);
                return action(owner, "Send startup message", expected);
            }
            const first = await turn(fixture.startup_command);
            assert.equal(first.evidence.next_step, "name");
            assert.equal(first.evidence.progress.length, 8);
            assert.equal(first.execution_authorized, false);
            assert.equal(first.external_effects, 0);
            assert.equal(first.evidence.activation_authorized, false);
            await turn("record startup name", 422);
            const recorded = await turn(`Record startup name | ${fixture.today} | fixture:browser | Synthetic name recorded`);
            assert.equal(recorded.evidence.next_step, "structure");

            const logoutRequest = owner.waitForRequest(req => req.url().endsWith("/api/weweb/logout"));
            assert.equal((await action(owner, "Sign out", 200)).ok, true);
            const revoked = (await (await logoutRequest).allHeaders()).authorization;
            assert.ok(revoked);
            const replayStatus = await owner.evaluate(async authorization => (await fetch("/api/weweb/owner-briefing", {
                headers: {authorization}, redirect: "error", credentials: "omit", cache: "no-store",
            })).status, revoked);
            assert.equal(replayStatus, 401);
            await action(owner, "Read owner briefing", 401);

            const resumed = await pageFor(fixture.owner);
            await action(resumed, "Sign in", 200);
            await field(resumed, "Conversation ID", fixture.conversation);
            await field(resumed, "Startup message", "Startup progress");
            const progress = await action(resumed, "Send startup message", 201);
            assert.equal(progress.evidence.next_step, "structure");
            report.decision = decision.prime_decision_id;
            report.loki_receipt = decision.independent_loki.review_id;
            report.loki_result_sha256 = decision.independent_loki.result_sha256;
            report.mimir_receipts = decision.reviewed_mimir_outcomes.length;
            report.startup = {initial: "name", resumed: "structure", malformed_turn: 422, external_effects: 0};
            report.revoked_session = replayStatus;
        }
        assert.deepEqual(blocked, []);
        console.log(JSON.stringify(report));
    } finally {
        await browser.close();
    }
}

run().catch(error => {
    console.error(error);
    process.exitCode = 1;
});
