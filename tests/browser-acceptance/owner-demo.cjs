const assert = require("node:assert/strict");
const {readFileSync} = require("node:fs");
const {chromium} = require("playwright");

async function run() {
    const {origin, password} = JSON.parse(readFileSync(0, "utf8"));
    const browser = await chromium.launch({executablePath: process.env.VALHALLA_BROWSER_EXECUTABLE});
    try {
        const page = await browser.newPage({serviceWorkers: "block"});
        const blocked = [];
        await page.route("**/*", route => {
            if (new URL(route.request().url()).origin === origin) return route.continue();
            blocked.push(new URL(route.request().url()).origin);
            return route.abort();
        });
        await page.goto(origin + "/demo/");
        assert.match(await page.locator(".notice").textContent(), /Synthetic records only/);

        async function act(name, endpoint, status) {
            const response = page.waitForResponse(res => res.url().includes(endpoint));
            await page.getByRole("button", {name, exact: true}).click();
            const result = await response;
            assert.equal(result.status(), status, name);
            return result.json();
        }

        async function signIn() {
            await page.getByLabel("One-run password").evaluate((input, value) => { input.value = value; }, password);
            await act("Sign in", "/owner-conversations", 201);
        }

        await signIn();
        const steps = ["name", "structure", "professionals", "reporting", "registration", "accounts", "staging", "launch"];
        const opening = await act("Start walkthrough", "/turns", 201);
        assert.deepEqual(opening.evidence.progress.map(step => step.key), steps);
        const shortlist = await act("Review shortlist", "/turns", 201);
        assert.equal(shortlist.evidence.professional_candidates.length, 4);
        assert.ok(shortlist.evidence.professional_candidates.every(row => row.approval === "PENDING"));
        for (let index = 0; index < steps.length; index++) {
            const progress = await act("Record next stage as practice", "/turns", 201);
            assert.equal(progress.evidence.startup_record.step, steps[index]);
            assert.equal(progress.evidence.startup_record.reference, "demo:practice-" + steps[index]);
            assert.equal(progress.evidence.next_step, steps[index + 1] ?? null);
            assert.equal(progress.evidence.activation_authorized, false);
            assert.equal(progress.external_effects, 0);
        }
        const loki = await act("Read Loki evidence", "/owner-pantheon/reports", 200);
        assert.equal(loki.reports[0].independent_loki.status, "completed");
        assert.equal(loki.execution_authorized, false);
        await page.getByText("Loki · synthetic review", {exact: true}).waitFor({state: "attached"});
        await act("Sign out", "/logout", 200);
        await page.reload();
        await signIn();
        const restored = await act("Show saved progress", "/turns", 201);
        assert.ok(restored.evidence.progress.every(step => step.status === "OWNER_RECORDED"));
        const mimir = await act("Recall Mimir note", "/turns", 201);
        assert.equal(mimir.evidence.knowledge.facts.length, 0);
        assert.equal(mimir.evidence.knowledge.assumptions[0].item_id, "demo-incorporation-note");
        await page.getByText("Mimir · synthetic records", {exact: true}).waitFor({state: "attached"});
        assert.deepEqual(blocked, []);
        console.log(JSON.stringify({stages: steps, professional_candidates: 4, restored_stages: 8,
            loki_status: "completed", mimir_class: "synthetic_assumption", external_effects: 0}));
    } finally {
        await browser.close();
    }
}

run().catch(error => { console.error(error); process.exitCode = 1; });
