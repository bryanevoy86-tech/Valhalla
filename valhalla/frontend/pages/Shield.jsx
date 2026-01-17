import React, { useEffect, useState } from "react";
import { withOrgHeaders } from "../lib/orgContext";

async function api(path, init={}) {
  const token = localStorage.getItem("token");
  const url = `${import.meta.env.VITE_API_URL}/api${path}`;
  const r = await fetch(url, withOrgHeaders({ ...init, headers: { ...(init.headers||{}), Authorization: `Bearer ${token}`, "Content-Type":"application/json" } }));
  return r.json();
}

export default function Shield() {
  const [tab, setTab] = useState("ip");
  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">Shield (Security)</h1>
      <div className="flex gap-2">
        {["ip","keys","limits","verify"].map(t=>(
          <button key={t} className={`border rounded px-3 py-1 ${tab===t?"bg-gray-100":""}`} onClick={()=>setTab(t)}>{t}</button>
        ))}
      </div>
      {tab==="ip" && <IpRulesTab/>}
      {tab==="keys" && <KeysTab/>}
      {tab==="limits" && <LimitsTab/>}
      {tab==="verify" && <VerifyTab/>}
    </div>
  );
}

function IpRulesTab() {
  const [rows, setRows] = useState([]);
  const [form, setForm] = useState({ cidr:"", action:"allow", label:"" });
  const load = async ()=> setRows(await api("/shield/ip_rules"));
  useEffect(()=>{ load(); },[]);
  const save = async ()=> { await api("/shield/ip_rules",{method:"POST", body:JSON.stringify(form)}); setForm({cidr:"",action:"allow",label:""}); load(); };
  return (
    <div className="border rounded p-4">
      <div className="font-semibold mb-2">IP Rules</div>
      <div className="flex gap-2 mb-3">
        <input className="border rounded p-1" placeholder="CIDR (1.2.3.4/32)" value={form.cidr} onChange={e=>setForm({...form,cidr:e.target.value})}/>
        <select className="border rounded p-1" value={form.action} onChange={e=>setForm({...form,action:e.target.value})}>
          <option value="allow">allow</option><option value="deny">deny</option>
        </select>
        <input className="border rounded p-1" placeholder="label" value={form.label} onChange={e=>setForm({...form,label:e.target.value})}/>
        <button className="border rounded px-3 py-1" onClick={save}>Add</button>
      </div>
      <table className="text-sm w-full">
        <thead><tr><th className="p-1 border">id</th><th className="p-1 border">cidr</th><th className="p-1 border">action</th><th className="p-1 border">active</th><th className="p-1 border">label</th></tr></thead>
        <tbody>{rows.map(r=>(
          <tr key={r.id}><td className="p-1 border">{r.id}</td><td className="p-1 border">{r.cidr}</td><td className="p-1 border">{r.action}</td><td className="p-1 border">{String(r.active)}</td><td className="p-1 border">{r.label||""}</td></tr>
        ))}</tbody>
      </table>
    </div>
  );
}

function KeysTab() {
  const [rows, setRows] = useState([]);
  const [form, setForm] = useState({ name:"service", scopes:'["read:deals"]' });
  const load = async ()=> setRows(await api("/shield/api_keys"));
  useEffect(()=>{ load(); },[]);
  const createKey = async () => {
    const payload = { name: form.name, scopes: JSON.parse(form.scopes || "[]") };
    const r = await api("/shield/api_keys", { method:"POST", body: JSON.stringify(payload) });
    alert(`Copy this secret now:\n${r.secret}\n(prefix ${r.prefix})`);
    load();
  };
  return (
    <div className="border rounded p-4">
      <div className="font-semibold mb-2">API Keys</div>
      <div className="flex gap-2 mb-3">
        <input className="border rounded p-1" placeholder="name" value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/>
        <input className="border rounded p-1 flex-1" placeholder='scopes JSON' value={form.scopes} onChange={e=>setForm({...form,scopes:e.target.value})}/>
        <button className="border rounded px-3 py-1" onClick={createKey}>Create</button>
      </div>
      <table className="text-sm w-full">
        <thead><tr><th className="p-1 border">id</th><th className="p-1 border">name</th><th className="p-1 border">prefix</th><th className="p-1 border">active</th><th className="p-1 border">scopes</th></tr></thead>
        <tbody>{rows.map(r=>(
          <tr key={r.id}><td className="p-1 border">{r.id}</td><td className="p-1 border">{r.name}</td><td className="p-1 border">{r.prefix}</td><td className="p-1 border">{String(r.active)}</td><td className="p-1 border"><pre className="text-xs">{JSON.stringify(r.scopes||[],null,2)}</pre></td></tr>
        ))}</tbody>
      </table>
    </div>
  );
}

function LimitsTab() {
  const [rows, setRows] = useState([]);
  const [form, setForm] = useState({ key:"ip:127.0.0.1:route:/shield/verify/rate", window_sec:10, max_hits:3 });
  const load = async ()=> setRows(await api("/shield/rate_limits"));
  useEffect(()=>{ load(); },[]);
  const save = async ()=> { await api("/shield/rate_limits",{method:"POST", body:JSON.stringify(form)}); load(); };
  return (
    <div className="border rounded p-4">
      <div className="font-semibold mb-2">Rate Limits</div>
      <div className="flex gap-2 mb-3">
        <input className="border rounded p-1 flex-1" placeholder="key (ip:user:org:route...)" value={form.key} onChange={e=>setForm({...form,key:e.target.value})}/>
        <input className="border rounded p-1 w-24" type="number" value={form.window_sec} onChange={e=>setForm({...form,window_sec:Number(e.target.value)})}/>
        <input className="border rounded p-1 w-24" type="number" value={form.max_hits} onChange={e=>setForm({...form,max_hits:Number(e.target.value)})}/>
        <button className="border rounded px-3 py-1" onClick={save}>Add</button>
      </div>
      <table className="text-sm w-full">
        <thead><tr><th className="p-1 border">id</th><th className="p-1 border">key</th><th className="p-1 border">window</th><th className="p-1 border">max</th><th className="p-1 border">active</th></tr></thead>
        <tbody>{rows.map(r=>(
          <tr key={r.id}><td className="p-1 border">{r.id}</td><td className="p-1 border">{r.key}</td><td className="p-1 border">{r.window_sec}s</td><td className="p-1 border">{r.max_hits}</td><td className="p-1 border">{String(r.active)}</td></tr>
        ))}</tbody>
      </table>
    </div>
  );
}

function VerifyTab() {
  const [ip, setIp] = useState(null);
  const [key, setKey] = useState(null);
  const [rate, setRate] = useState(null);
  const call = async (path, setter, hdrs={}) => {
    const token = localStorage.getItem("token");
    const url = `${import.meta.env.VITE_API_URL}/api${path}`;
    const r = await fetch(url, withOrgHeaders({ headers: { Authorization:`Bearer ${token}`, ...hdrs } }));
    setter(await r.json());
  };
  return (
    <div className="border rounded p-4 space-y-2">
      <button className="border rounded px-3 py-1" onClick={()=>call("/shield/verify/ip", setIp)}>Check IP</button>
      <pre className="text-xs">{ip && JSON.stringify(ip,null,2)}</pre>
      <button className="border rounded px-3 py-1" onClick={()=>call("/shield/verify/rate", setRate)}>Check Rate</button>
      <pre className="text-xs">{rate && JSON.stringify(rate,null,2)}</pre>
      <button className="border rounded px-3 py-1" onClick={()=>call("/shield/verify/key", setKey, {"Authorization":"ApiKey INVALID"})}>Check API Key (expect 401)</button>
      <pre className="text-xs">{key && JSON.stringify(key,null,2)}</pre>
    </div>
  );
}
