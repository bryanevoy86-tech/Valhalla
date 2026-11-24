// Bind the existing WeWeb access-token getter. Never pass a Prime or provider key.
export function mountResearchPanel(root, {roundId, apiOrigin, getSession}) {
    const validRound = /^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/i;
    const origin = new URL(apiOrigin);
    if (!validRound.test(roundId) || origin.origin !== apiOrigin ||
        (origin.protocol !== "https:" &&
            !(origin.protocol === "http:" && origin.hostname === "127.0.0.1" && origin.origin === location.origin))) {
        throw new Error("Invalid research configuration");
    }
    const path = origin.origin + "/api/weweb/customer-research/" + roundId.toLowerCase();
    const labels = {yes:"Yes", no:"No", skip:"Skip", unsure:"Unsure", under_1h:"Under 1 hour",
        "1_to_4h":"1 to 4 hours", over_4h:"More than 4 hours"};
    let running = false;
    let sequence = 0;
    const text = (tag, value) => {
        const node = document.createElement(tag);
        node.textContent = value;
        root.appendChild(node);
        return node;
    };
    const button = (label, click) => {
        const node = text("button", label);
        node.type = "button";
        node.addEventListener("click", click);
        return node;
    };

    function render(data) {
        root.replaceChildren();
        text("h2", "Research interview");
        if (data.status === "CONSENT_REQUIRED") {
            text("p", data.notice.text);
            const label = text("label", "I consent to this research round. ");
            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            label.prepend(checkbox);
            const proceed = button("Start interview", () => request("/enroll", {
                consent: checkbox.checked, notice_version: data.notice.version, notice_sha256: data.notice_sha256,
            }));
            proceed.disabled = true;
            checkbox.addEventListener("change", () => { proceed.disabled = !checkbox.checked; });
        } else if (data.status === "INTERVIEW") {
            text("p", data.question);
            for (const answer of data.options.filter(option => Object.hasOwn(labels, option))) {
                button(labels[answer], () => request("/answer", {step: data.step, answer}));
            }
        } else {
            const status = {
                COMPLETED:"Interview complete. Thank you for taking part.",
                WITHDRAWN:"You withdrew. Your research answers were removed.",
                PAUSED:"Research is paused.", CLOSED:"This round is closed.",
                DENIED:"This invitation is unavailable for your account.",
                SIGN_IN:"Sign in to open your research invitation.",
                UNAVAILABLE:"Research is unavailable. Refresh to try again.",
            };
            text("p", status[data.status] ?? status.UNAVAILABLE);
        }
        if (["CONSENT_REQUIRED", "INTERVIEW", "COMPLETED", "PAUSED", "CLOSED"].includes(data.status)) {
            button("Withdraw and erase answers", () => request("/withdraw"));
        }
        button("Refresh interview", () => request(""));
    }

    async function request(action, body) {
        if (running) return;
        const session = getSession();
        if (!session) return render({status:"SIGN_IN"});
        const version = ++sequence;
        running = true;
        root.querySelectorAll("button").forEach(node => { node.disabled = true; });
        try {
            const headers = {Authorization:"Bearer " + session};
            if (body) headers["Content-Type"] = "application/json";
            const res = await fetch(path + action, {
                method:action ? "POST" : "GET", headers, body:body && JSON.stringify(body), cache:"no-store",
                credentials:"omit", redirect:"error", signal:AbortSignal.timeout(15000),
            });
            const result = res.ok ? await res.json() : {
                status:({401:"SIGN_IN", 403:"DENIED", 404:"DENIED", 410:"CLOSED", 503:"PAUSED"})[res.status] || "UNAVAILABLE",
            };
            if (sequence === version) render(getSession() === session ? result : {status:"SIGN_IN"});
        } catch {
            if (sequence === version) render({status:getSession() === session ? "UNAVAILABLE" : "SIGN_IN"});
        } finally {
            if (sequence === version) running = false;
        }
    }

    render({status:"SIGN_IN"});
    return {
        refresh: () => request(""),
        clear: () => { ++sequence; running = false; render({status:"SIGN_IN"}); },
    };
}
