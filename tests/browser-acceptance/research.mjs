import {mountResearchPanel} from "/__widgets/participant-customer-research.mjs";
let bearer;
const form = document.querySelector("form");
const signout = document.querySelector("#signout");
const status = document.querySelector("#login-status");
const panel = mountResearchPanel(document.querySelector("#research"), {
    roundId:new URL(location.href).searchParams.get("round"), apiOrigin:location.origin, getSession:() => bearer,
});
form.addEventListener("submit", async event => {
    event.preventDefault();
    const response = await fetch("/api/weweb/login", {method:"POST", cache:"no-store", redirect:"error",
        headers:{"Content-Type":"application/json"}, body:JSON.stringify(Object.fromEntries(new FormData(form)))});
    if (!response.ok) { status.textContent = "Sign-in failed."; return; }
    bearer = (await response.json()).access_token;
    form.reset();
    form.hidden = true;
    signout.hidden = false;
    status.textContent = "Signed in.";
    await panel.refresh();
});
signout.addEventListener("click", async () => {
    const token = bearer;
    bearer = undefined;
    panel.clear();
    form.hidden = false;
    signout.hidden = true;
    status.textContent = "Signed out.";
    if (token) await fetch("/api/weweb/logout", {method:"POST", headers:{Authorization:"Bearer " + token},
        cache:"no-store", redirect:"error"});
});
