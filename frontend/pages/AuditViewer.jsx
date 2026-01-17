import React, { useEffect, useMemo, useState } from "react";
import { withOrgHeaders } from "../lib/orgContext";

async function api(path, init={}) {
  const token = localStorage.getItem("token");
  const url = `${import.meta.env.VITE_API_URL}/api${path}`;
  const r = await fetch(url, withOrgHeaders({ ...init, headers: { ...(init.headers||{}), Authorization: `Bearer ${token}`, "Content-Type":"application/json" } }));
  return r.json();
}

function Diff({diff}) {
  if (!diff) return null;
  const changed = Object.entries(diff.changed || {});
  const added = Object.entries(diff.added || {});
  const removed = diff.removed || [];
  return (
    <div className="text-xs">
      {changed.length>0 && (
        <div className="mb-2">
          <div className="font-semibold">Changed</div>
          <table className="w-full">
            <thead><tr><th className="border p-1">field</th><th className="border p-1">before</th><th className="border p-1">after</th></tr></thead>
            <tbody>{changed.map(([k,[b,a]])=>(
              <tr key={k}><td className="border p-1">{k}</td><td className="border p-1">{String(b)}</td><td className="border p-1">{String(a)}</td></tr>
            ))}</tbody>
          </table>
        </div>
      )}
      {added.length>0 && (
        <div className="mb-2">
          <div className="font-semibold">Added</div>
          <table className="w-full">
            <thead><tr><th className="border p-1">field</th><th className="border p-1">value</th></tr></thead>
            <tbody>{added.map(([k,v])=>(
              <tr key={k}><td className="border p-1">{k}</td><td className="border p-1">{String(v)}</td></tr>
            ))}</tbody>
          </table>
        </div>
      )}
      {removed.length>0 && (
        <div className="mb-2">
          <div className="font-semibold">Removed</div>
          <div className="flex flex-wrap gap-2">{removed.map(k=><span key={k} className="text-[10px] border rounded px-2 py-0.5">{k}</span>)}</div>
        </div>
      )}
    </div>
  );
}

export default function AuditViewer() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({ entity:"", entity_id:"", action:"" });
  const [selected, setSelected] = useState(null);

  const run = async (p=1) => {
    const qs = new URLSearchParams();
    if (filters.entity) qs.set("entity", filters.entity);
    if (filters.entity_id) qs.set("entity_id", filters.entity_id);
    if (filters.action) qs.set("action", filters.action);
    qs.set("page", String(p)); qs.set("size","50");
    const res = await api(`/audit?${qs.toString()}`);
    setItems(res.items||[]); setTotal(res.total||0); setPage(res.page||1);
  };

  useEffect(()=>{ run(1); }, []);

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">Audit Trail</h1>
      <div className="flex gap-2 items-end">
        <div>
          <div className="text-xs">Entity</div>
          <input className="border rounded p-2" placeholder="deals, funding_requests..." value={filters.entity} onChange={e=>setFilters({...filters, entity:e.target.value})}/>
        </div>
        <div>
          <div className="text-xs">Entity ID</div>
          <input className="border rounded p-2" placeholder="123" value={filters.entity_id} onChange={e=>setFilters({...filters, entity_id:e.target.value})}/>
        </div>
        <div>
          <div className="text-xs">Action</div>
          <select className="border rounded p-2" value={filters.action} onChange={e=>setFilters({...filters, action:e.target.value})}>
            <option value="">(any)</option>
            {["create","update","delete","status","login","run"].map(a=><option key={a} value={a}>{a}</option>)}
          </select>
        </div>
        <button className="border rounded px-3 py-2" onClick={()=>run(1)}>Filter</button>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="border rounded p-3">
          <div className="font-semibold mb-2">Events ({total})</div>
          <div className="max-h-[70vh] overflow-auto">
            <table className="text-sm w-full">
              <thead><tr><th className="border p-1">when</th><th className="border p-1">who</th><th className="border p-1">action</th><th className="border p-1">entity</th></tr></thead>
              <tbody>
                {items.map(ev=>(
                  <tr key={ev.id} className="hover:bg-gray-50 cursor-pointer" onClick={()=>setSelected(ev)}>
                    <td className="border p-1">{new Date(ev.when).toLocaleString()}</td>
                    <td className="border p-1">{ev.actor_user_id ?? "-"}</td>
                    <td className="border p-1">{ev.action}</td>
                    <td className="border p-1">{ev.entity}#{ev.entity_id}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-2 flex items-center gap-2">
            <button className="border rounded px-2 py-1" disabled={page<=1} onClick={()=>run(page-1)}>Prev</button>
            <div>Page {page}</div>
            <button className="border rounded px-2 py-1" disabled={(page*50)>=total} onClick={()=>run(page+1)}>Next</button>
          </div>
        </div>

        <div className="border rounded p-3">
          <div className="font-semibold mb-2">Diff</div>
          {!selected ? <div className="text-sm opacity-70">Select an event</div> : <Diff diff={selected.diff} />}
          {selected && (
            <div className="mt-3">
              <div className="font-semibold">Metadata</div>
              <pre className="text-xs overflow-auto">{JSON.stringify({ meta: selected.meta, route: selected.route, ip: selected.ip }, null, 2)}</pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
