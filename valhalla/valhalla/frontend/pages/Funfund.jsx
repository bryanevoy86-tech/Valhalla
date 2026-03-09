import React, { useEffect, useState } from "react";
import { withOrgHeaders } from "../lib/orgContext";

async function api(path, init={}) {
  const token = localStorage.getItem("token");
  const url = `${import.meta.env.VITE_API_URL}/api${path}`;
  const r = await fetch(url, withOrgHeaders({ ...init, headers: { ...(init.headers||{}), Authorization: `Bearer ${token}`, "Content-Type":"application/json" } }));
  return r.json();
}

export default function Funfund() {
  const [list, setList] = useState([]);
  const [form, setForm] = useState({ amount: 10000, currency: "USD", purpose: "" });
  const [selected, setSelected] = useState(null);
  const load = async () => setList(await api("/funfund/requests"));
  useEffect(()=>{ load(); },[]);

  const createReq = async () => {
    await api("/funfund/requests", { method:"POST", body: JSON.stringify(form) });
    setForm({ amount: 10000, currency: "USD", purpose: "" });
    load();
  };
  const openReq = async (id) => setSelected(await api(`/funfund/requests/${id}`));
  const submitReq = async (id) => { await api(`/funfund/requests/${id}/submit`, { method:"POST" }); openReq(id); load(); };
  const approveReq = async (id) => { await api(`/funfund/requests/${id}/approve`, { method:"POST", body: JSON.stringify({}) }); openReq(id); load(); };
  const disburse = async (id) => { const amt = prompt("Disburse amount", selected?.amount || "0"); if (!amt) return; await api(`/funfund/requests/${id}/disburse`, { method:"POST", body: JSON.stringify({ amount: Number(amt) }) }); openReq(id); load(); };
  const setSched = async (id) => { const months = prompt("Months", "6"); await api(`/funfund/requests/${id}/schedule`, { method:"POST", body: JSON.stringify({ months: Number(months) }) }); openReq(id); };
  const repay = async (id) => { const amt = prompt("Repay amount"); if (!amt) return; await api(`/funfund/requests/${id}/repay`, { method:"POST", body: JSON.stringify({ amount: Number(amt) }) }); openReq(id); load(); };

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">Funfund (Funding)</h1>

      <div className="border rounded p-4">
        <div className="font-semibold mb-2">Create Request</div>
        <div className="grid md:grid-cols-4 gap-2">
          <input className="border rounded p-2" type="number" value={form.amount} onChange={e=>setForm({...form, amount:Number(e.target.value)})}/>
          <input className="border rounded p-2" value={form.currency} onChange={e=>setForm({...form, currency:e.target.value})}/>
          <input className="border rounded p-2 md:col-span-2" placeholder="purpose" value={form.purpose} onChange={e=>setForm({...form, purpose:e.target.value})}/>
        </div>
        <button className="mt-2 border rounded px-3 py-1" onClick={createReq}>Create</button>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="border rounded p-4">
          <div className="font-semibold mb-2">Requests</div>
          <table className="text-sm w-full">
            <thead><tr><th className="p-1 border">id</th><th className="p-1 border">amount</th><th className="p-1 border">status</th><th className="p-1 border">actions</th></tr></thead>
            <tbody>
              {list.map(r=>(
                <tr key={r.id}>
                  <td className="p-1 border">{r.id}</td>
                  <td className="p-1 border">{r.amount} {r.currency}</td>
                  <td className="p-1 border">{r.status}</td>
                  <td className="p-1 border space-x-1">
                    <button className="text-xs border rounded px-2" onClick={()=>openReq(r.id)}>open</button>
                    {r.status==="draft" && <button className="text-xs border rounded px-2" onClick={()=>submitReq(r.id)}>submit</button>}
                    {r.status==="submitted" && <button className="text-xs border rounded px-2" onClick={()=>approveReq(r.id)}>approve</button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="border rounded p-4">
          <div className="font-semibold mb-2">Details</div>
          {!selected ? <div className="text-sm opacity-70">Select a request</div> : (
            <div className="space-y-2">
              <div>Request #{selected.id} — <span className="font-semibold">{selected.status}</span></div>
              <div>Amount: {selected.amount} {selected.currency}</div>
              <div className="text-sm">Balance: {selected.balance && selected.balance.outstanding}</div>
              {selected.schedule && (
                <div className="text-sm">
                  <div className="font-semibold">Schedule</div>
                  <ul className="list-disc ml-5">
                    {selected.schedule.map((s,i)=><li key={i}>{s.due}: {s.amount}</li>)}
                  </ul>
                </div>
              )}
              <div className="flex gap-2 flex-wrap">
                {["approved","disbursed"].includes(selected.status) && <button className="border rounded px-3 py-1" onClick={()=>disburse(selected.id)}>Disburse</button>}
                <button className="border rounded px-3 py-1" onClick={()=>setSched(selected.id)}>Set Schedule</button>
                <button className="border rounded px-3 py-1" onClick={()=>repay(selected.id)}>Repay</button>
              </div>
              <pre className="text-xs overflow-auto">{JSON.stringify(selected, null, 2)}</pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
