import {ownerAttentionSession} from "./owner-attention.mjs";
import {escapeOwnerReviewText} from "./owner-review-portal.mjs";

const scopeKeys = ["legacy_instance_id", "business_id", "engine_id", "jurisdiction"];
const purposes = {BUSINESS: "Business treasury", HOUSEHOLD: "Household budget", OPERATING_RESERVE: "Protected operating reserves"};

function amount(value, currency) {
    if (value === null) return "Unavailable";
    if (!Number.isSafeInteger(value)) throw new Error("Invalid fixture amount");
    return new Intl.NumberFormat("en-CA", {style:"currency", currency, currencyDisplay:"code"}).format(value / 100);
}

function formatOperatingScope(body, scope) {
    if (body?.execution_authorized !== false || body.actual_accessible_funds_minor !== null
        || !scopeKeys.every(key => body.scope?.[key] === scope[key])) throw new Error("Invalid scope receipt");
    const lines = [body.legacy.display_name + " · " + body.legacy.status, "Fixture evidence only"];
    const capital = body.capital_fixture;
    if (capital === null) {
        lines.push("No economic mandate is enrolled for this scope.");
    } else {
        if (capital.basis !== "RECONCILIATION_FIXTURE") throw new Error("Invalid capital evidence");
        lines.push("Economic decision · " + capital.suggested_action,
            "Period net · " + amount(capital.period_net_minor, capital.currency),
            "Recorded loss · " + amount(capital.cumulative_loss_minor, capital.currency),
            "Open obligations · " + amount(capital.open_obligations_minor, capital.currency),
            "Simulated exposure headroom · " + amount(capital.new_exposure_available_minor, capital.currency),
            ...capital.blockers.map(code => "Hold · " + code));
    }
    for (const [key, label] of Object.entries(purposes)) {
        const sample = body.statement_fixtures[key];
        if (sample.actual_accessible_funds_minor !== null) throw new Error("Unexpected funds claim");
        lines.push("", label);
        if (sample.status === "UNAVAILABLE") {
            lines.push("Fixture storage unavailable.");
            continue;
        }
        if (!Array.isArray(sample.accounts) || sample.accounts.length > 20) throw new Error("Invalid statement results");
        if (!sample.accounts.length) lines.push("No scoped statement fixtures.");
        for (const account of sample.accounts) {
            if (account.status === "EVIDENCE_CONFLICT") {
                lines.push("Statement integrity hold");
                continue;
            }
            if (account.status !== "MATCHED_FIXTURE") throw new Error("Unexpected statement status");
            const currency = account.currency;
            lines.push(account.statement_id, "Closing fixture balance · " + amount(account.closing_minor, currency),
                "Liabilities · " + amount(account.outstanding_liabilities_minor, currency),
                "Expenses · " + amount(account.expense_minor, currency),
                "Budget variance · " + amount(account.budget_variance_minor, currency),
                "Protected balance · " + amount(account.protected_balance_minor, currency));
        }
        if (sample.truncated) lines.push("More fixture statements exist in this scope.");
    }
    return lines.map(escapeOwnerReviewText).join("\n");
}

export async function runOwnerOperatingScope(input, transport = fetch) {
    const session = ownerAttentionSession(input.bearer);
    if (!session) return {status: "signed_out"};
    const result = (status, data = {}) => ({status, session, ...data});
    if (input.isOwner !== true) return result("denied");
    let endpoint;
    try {
        const api = new URL(input.apiBase);
        const approved = new URL(input.previewOrigin);
        if (api.protocol !== "https:" || api.username || api.password || approved.origin !== input.previewOrigin
            || approved.origin !== api.origin) return result("unconfigured");
        endpoint = approved.origin + "/api/weweb/owner-operating-scope";
    } catch {
        return result("unconfigured");
    }
    const scope = Object.fromEntries(scopeKeys.map(key => [key, input.scope?.[key]?.trim() ?? ""]));
    if (!scopeKeys.every(key => scope[key].length >= (key === "jurisdiction" ? 2 : 3)
        && scope[key].length <= (key === "business_id" ? 120 : 80))) return result("invalid_scope");
    try {
        const response = await transport(endpoint, {
            method:"POST", headers:{Authorization:"Bearer "+input.bearer,"Content-Type":"application/json"},
            body:JSON.stringify(scope), cache:"no-store", credentials:"omit", redirect:"error",
            signal:AbortSignal.timeout(15000),
        });
        if (response.status === 401) return result("signed_out");
        if (response.status === 403) return result("denied");
        if (response.status === 409) return result("scope_held");
        if (response.status === 422) return result("invalid_scope");
        if (!response.ok) return result("unavailable");
        return result("ready", {text:formatOperatingScope(await response.json(), scope)});
    } catch {
        return result("unavailable");
    }
}
