const get = (id) => document.getElementById(id);
const login = get("login");
const workspace = get("workspace");
const status = get("status");
const conversation = get("conversation");
const record = get("record");
const root = "/api/weweb";
const thread = "3ceff11c-acde-4c88-91f8-05e7c9325366";
const command = "I am ready to register Valhalla Legacy Inc. Walk me through everything and help me find the professionals I need.";
let token, checkpoint;

async function request(route, body) {
    const headers = {};
    if (token) headers.Authorization = `Bearer ${token}`;
    if (body) headers["Content-Type"] = "application/json";
    const response = await fetch(root + route, {method: body ? "POST" : "GET", headers,
        credentials: "omit", cache: "no-store", redirect: "error", body: body && JSON.stringify(body)});
    if (response.status === 401) signedOut();
    if (!response.ok) {
        const fallback = response.status === 401 ? "Sign in with the current demo password." : `Request denied (HTTP ${response.status}).`;
        const error = await response.json().catch(() => ({}));
        throw new Error(typeof error.detail === "string" && response.status === 422 ? error.detail : fallback);
    }
    return response.json();
}

function signedOut() {
    token = undefined;
    checkpoint = undefined;
    login.hidden = false;
    workspace.hidden = true;
    record.hidden = true;
    conversation.replaceChildren();
}

async function act(callback) {
    const buttons = [...document.querySelectorAll("button")];
    buttons.forEach(button => { button.disabled = true; });
    status.textContent = "Working…";
    try {
        await callback();
        status.textContent = "";
    } catch (error) {
        status.textContent = error.message;
    } finally {
        buttons.forEach(button => { button.disabled = false; });
    }
}

function display(title, content) {
    const card = document.createElement("article");
    const heading = document.createElement("h3");
    const text = document.createElement("p");
    heading.textContent = title;
    text.textContent = content;
    card.append(heading, text);
    conversation.append(card);
    card.scrollIntoView({block: "nearest"});
}

async function turn(message, extra = {}) {
    const reply = await request(`/owner-conversations/${thread}/turns`, {turn_id: crypto.randomUUID(), message, ...extra});
    display("You", message);
    display("Heimdall", reply.reply);
    if (reply.evidence?.source === "private_startup_walkthrough") {
        checkpoint = {step: reply.evidence.next_step, date: reply.evidence.as_of};
        record.hidden = !checkpoint.step;
    }
    return reply;
}

login.addEventListener("submit", (event) => {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(login));
    login.elements.password.value = "";
    void act(async () => {
        token = (await request("/login", values)).access_token;
        await request("/owner-conversations", {conversation_id: thread, title: "Synthetic owner demonstration"});
        login.hidden = true;
        workspace.hidden = false;
    });
});

get("walkthrough").onclick = () => act(() => turn(command));
get("professionals").onclick = () => act(() => turn("Startup professionals"));
get("progress").onclick = () => act(() => turn("Startup progress"));
record.onclick = () => act(() => turn(
    `Record startup ${checkpoint.step} | ${checkpoint.date} | demo:practice-${checkpoint.step} | Synthetic practice entry only`
));
get("loki").onclick = () => act(async () => {
    const {reports} = await request("/owner-pantheon/reports?role=MIMIR");
    const receipt = reports.find(item => item.state === "VERIFIED_RECEIPT")?.independent_loki;
    if (!receipt || receipt.status !== "completed") throw new Error("No verified local Loki receipt is available.");
    display("Loki · synthetic review", [`Receipt ${receipt.review_id}`,
        `Reconsideration: ${receipt.reconsideration_status}`, ...receipt.findings].join("\n"));
});
get("mimir").onclick = () => act(async () => {
    const reply = await turn("Recall the incorporation practice note", {
        knowledge_domain: "Incorporation", knowledge_jurisdiction: "CA-MB",
    });
    const {facts, assumptions} = reply.evidence.knowledge;
    const entries = [...facts, ...assumptions];
    display("Mimir · synthetic records", entries.map(item => `${item.title} · ${item.citation_ref}`).join("\n")
        || "No matching record.");
});
get("logout").onclick = () => act(async () => {
    await request("/logout", {});
    signedOut();
});
get("message").addEventListener("submit", (event) => {
    event.preventDefault();
    const input = event.currentTarget.elements.text;
    void act(async () => {
        await turn(input.value);
        input.value = "";
    });
});
