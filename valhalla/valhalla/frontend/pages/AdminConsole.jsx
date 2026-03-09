import React, { useEffect, useState } from "react";
import { withOrgHeaders } from "../lib/orgContext";

async function api(path, init={}) {
  const token = localStorage.getItem("token");
  const url = `${import.meta.env.VITE_API_URL}/api${path}`;
  const r = await fetch(url, withOrgHeaders({ ...init, headers: { ...(init.headers||{}), Authorization: `Bearer ${token}`, "Content-Type":"application/json" } }));
  return r.json();
}

export default function AdminConsole() {
  const [tab, setTab] = useState("users");

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">Admin Console</h1>
      <div className="flex gap-2">
        {["users","flags","tools","actions"].map(t=>(
          <button key={t} className={`border rounded px-3 py-1 ${tab===t?"bg-gray-100":""}`} onClick={()=>setTab(t)}>{t}</button>
        ))}
      </div>
      {tab==="users" && <UsersTab />}
      {tab==="flags" && <FlagsTab />}
      {tab==="tools" && <ToolsTab />}
      {tab==="actions" && <ActionsTab />}
    </div>
  );
}

function UsersTab() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [impUser, setImpUser] = useState(null);
  const load = async () => { setLoading(true); setRows(await api("/admin/users")); setLoading(false); };
  useEffect(()=>{ load(); },[]);
  const changeRole = async (id, role) => { await api(`/admin/users/${id}/role`, { method: "PATCH", body: JSON.stringify({ role }) }); load(); };
  const impersonate = async (id) => {
    const r = await api(`/admin/impersonate/${id}`, { method: "POST" });
    localStorage.setItem("token", r.token);
    setImpUser(id);
  };

  return (
    <div className="border rounded p-4">
      <div className="font-semibold mb-2">Org Users</div>
      {loading ? "Loading..." : (
        <table className="text-sm w-full">
          <thead><tr><th className="p-1 border">id</th><th className="p-1 border">email</th><th className="p-1 border">role</th><th className="p-1 border">org_role</th><th className="p-1 border">actions</th></tr></thead>
          <tbody>
            {rows.map(r=>(
              <tr key={r.id}>
                <td className="p-1 border">{r.id}</td>
                <td className="p-1 border">{r.email}</td>
                <td className="p-1 border">{r.role}</td>
                <td className="p-1 border">{r.org_role}</td>
                <td className="p-1 border space-x-1">
                  {["viewer","operator","admin"].map(role=>(
                    <button key={role} className="text-xs border rounded px-2" onClick={()=>changeRole(r.id, role)}>{role}</button>
                  ))}
                  <button className="text-xs border rounded px-2" onClick={()=>impersonate(r.id)}>impersonate</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {impUser && <div className="mt-2 text-xs opacity-70">Impersonation token stored; refresh app to act as user #{impUser}. (A banner is a good idea in production.)</div>}
    </div>
  );
}

function FlagsTab() {
  const [flags, setFlags] = useState([]);
  const [form, setForm] = useState({ scope:"org", key:"", enabled:true, payload:"" });
  const load = async () => setFlags(await api("/admin/flags"));
  useEffect(()=>{ load(); },[]);
  const save = async () => {
    const payload = form.payload ? JSON.parse(form.payload) : undefined;
    await api("/admin/flags", { method:"POST", body: JSON.stringify({ ...form, payload }) });
    setForm({ scope:"org", key:"", enabled:true, payload:"" }); load();
  };
  const del = async (id) => { await api(`/admin/flags/${id}`, { method:"DELETE" }); load(); };

  return (
    <div className="border rounded p-4 space-y-3">
      <div className="font-semibold">New / Update Flag</div>
      <div className="grid md:grid-cols-4 gap-2">
        <select className="border rounded p-2" value={form.scope} onChange={e=>setForm({...form, scope:e.target.value})}>
          <option value="org">org</option>
          <option value="user">user</option>
          <option value="global">global</option>
        </select>
        <input className="border rounded p-2" placeholder="key" value={form.key} onChange={e=>setForm({...form, key:e.target.value})}/>
        <select className="border rounded p-2" value={String(form.enabled)} onChange={e=>setForm({...form, enabled: e.target.value==="true"})}>
          <option value="true">enabled</option>
          <option value="false">disabled</option>
        </select>
        <input className="border rounded p-2" placeholder='payload JSON (optional)' value={form.payload} onChange={e=>setForm({...form, payload:e.target.value})}/>
      </div>
      <button className="border rounded px-3 py-1" onClick={save}>Save</button>

      <div className="font-semibold mt-4">Flags</div>
      <table className="text-sm w-full">
        <thead><tr><th className="p-1 border">id</th><th className="p-1 border">scope</th><th className="p-1 border">key</th><th className="p-1 border">enabled</th><th className="p-1 border">payload</th><th className="p-1 border">actions</th></tr></thead>
        <tbody>
          {flags.map(f=>(
            <tr key={f.id}>
              <td className="p-1 border">{f.id}</td>
              <td className="p-1 border">{f.scope}</td>
              <td className="p-1 border">{f.key}</td>
              <td className="p-1 border">{String(f.enabled)}</td>
              <td className="p-1 border"><pre className="text-xs">{JSON.stringify(f.payload||{},null,2)}</pre></td>
              <td className="p-1 border"><button className="text-xs border rounded px-2" onClick={()=>del(f.id)}>delete</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ToolsTab() {
  const [tickRes, setTickRes] = useState(null);
  const [whRes, setWhRes] = useState(null);
  const tick = async () => setTickRes(await api("/admin/maintenance/tick", { method:"POST" }));
  const deliver = async () => setWhRes(await api("/admin/maintenance/deliver-webhooks", { method:"POST" }));
  return (
    <div className="border rounded p-4 space-y-3">
      <div className="font-semibold">Maintenance</div>
      <div className="flex gap-2">
        <button className="border rounded px-3 py-1" onClick={tick}>Run Alerts/SLA Tick</button>
        <button className="border rounded px-3 py-1" onClick={deliver}>Deliver Webhooks</button>
      </div>
      {tickRes && <pre className="text-xs">{JSON.stringify(tickRes, null, 2)}</pre>}
      {whRes && <pre className="text-xs">{JSON.stringify(whRes, null, 2)}</pre>}
    </div>
  );
}

function ActionsTab() {
  const [rows, setRows] = useState([]);
  const load = async () => setRows(await api("/admin/actions"));
  useEffect(()=>{ load(); },[]);
  return (
    <div className="border rounded p-4">
      <div className="font-semibold mb-2">Recent Admin Actions</div>
      <table className="text-sm w-full">
        <thead><tr><th className="p-1 border">when</th><th className="p-1 border">actor</th><th className="p-1 border">action</th><th className="p-1 border">details</th></tr></thead>
        <tbody>
          {rows.map(r=>(
            <tr key={r.id}>
              <td className="p-1 border">{r.created_at}</td>
              <td className="p-1 border">{r.actor_user_id ?? "-"}</td>
              <td className="p-1 border">{r.action}</td>
              <td className="p-1 border"><pre className="text-xs">{JSON.stringify(r.details||{},null,2)}</pre></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
