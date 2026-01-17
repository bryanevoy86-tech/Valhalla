import React, { useEffect, useState } from "react";
import { withOrgHeaders } from "../lib/orgContext";

async function api(path, init={}) {
  const token = localStorage.getItem("token");
  const url = `${import.meta.env.VITE_API_URL}/api${path}`;
  const r = await fetch(url, withOrgHeaders({ ...init, headers: { ...(init.headers||{}), Authorization: `Bearer ${token}`, "Content-Type":"application/json" } }));
  return r.json();
}

export default function Billing() {
  const [plan, setPlan] = useState("starter");
  const [seats, setSeats] = useState(1);

  const checkout = async () => {
    const r = await api("/billing/checkout", { method: "POST", body: JSON.stringify({ plan, seats }) });
    window.location.href = r.url;
  };
  const portal = async () => {
    const r = await api("/billing/portal", { method: "POST" });
    window.location.href = r.url;
  };
  const saveSeats = async () => {
    await api("/billing/seats", { method: "POST", body: JSON.stringify({ seats }) });
    alert("Seats updated");
  };

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">Billing</h1>

      <div className="border rounded p-4 space-y-3">
        <div className="font-semibold">Choose a plan</div>
        <div className="grid md:grid-cols-3 gap-3">
          {["starter","pro"].map(p=>(
            <label key={p} className={`border rounded p-3 cursor-pointer ${plan===p?"ring-2":""}`}>
              <input type="radio" name="plan" value={p} checked={plan===p} onChange={()=>setPlan(p)} />{" "}
              <span className="uppercase">{p}</span>
              <div className="text-xs opacity-70">{p==="starter"?"Great to start":"More power & seats"}</div>
            </label>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <div className="text-sm">Seats</div>
          <input type="number" min={1} className="border rounded p-2 w-24" value={seats} onChange={e=>setSeats(Number(e.target.value)||1)} />
          <button className="border rounded px-3 py-1" onClick={saveSeats}>Save seats</button>
        </div>
        <div className="flex gap-2">
          <button className="border rounded px-3 py-1" onClick={checkout}>Checkout</button>
          <button className="border rounded px-3 py-1" onClick={portal}>Manage in Portal</button>
        </div>
      </div>
    </div>
  );
}
