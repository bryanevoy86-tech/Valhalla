if (!["127.0.0.1", "localhost", "[::1]"].includes(location.hostname)) {
    throw new Error("The acceptance client requires a loopback origin");
}

const get = (id) => document.getElementById(id);
const status = get("status");
const result = get("result");
const api = "/api/weweb";
const conversations = api + "/owner-conversations";
let token;

async function request(path, method = "GET", data) {
    const headers = {};
    if (token) headers.Authorization = `Bearer ${token}`;
    if (data) headers["Content-Type"] = "application/json";
    const response = await fetch(path, {
        method, headers, credentials: "omit", cache: "no-store", redirect: "error",
        body: data ? JSON.stringify(data) : undefined,
    });
    return {code: response.status, data: await response.json()};
}

async function show(action) {
    status.textContent = "Working";
    result.textContent = "";
    try {
        const {code, data} = await action();
        if (code === 401) token = undefined;
        result.textContent = JSON.stringify(data, null, 2);
        status.textContent = `HTTP ${code}`;
    } catch {
        status.textContent = "Request failed";
    }
}

get("login").addEventListener("submit", (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form));
    form.elements.password.value = "";
    token = undefined;
    void show(async () => {
        const {code, data: reply} = await request(api + "/login", "POST", data);
        if (code === 200 && typeof reply.access_token === "string") token = reply.access_token;
        return {code, data: {signed_in: Boolean(token)}};
    });
});

get("briefing").onclick = () => show(() => request(api + "/owner-briefing?mode=driving"));
get("decision").onclick = () => show(() => request(api + "/owner-prime-decisions/" +
    encodeURIComponent(get("decision-id").value)));
get("stop").onclick = () => show(() => request("/governance/go-live/kill-switch/engage", "POST", {
    changed_by: "disposable-browser", reason: "Browser session must lack operator authority",
}));
get("startup").addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const id = data.get("id");
    if (event.submitter.name === "send") {
        void show(() => request(conversations + "/" + encodeURIComponent(id) + "/turns", "POST", {
            turn_id: crypto.randomUUID(), message: data.get("message"),
        }));
    } else {
        void show(() => request(conversations, "POST", {conversation_id: id, title: "Browser startup fixture"}));
    }
});
get("logout").onclick = () => show(async () => {
    const reply = await request(api + "/logout", "POST");
    token = undefined;
    return reply;
});
