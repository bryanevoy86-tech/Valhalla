import React, { useEffect, useState } from "react";
import PreviewFile from "./PreviewFile";

export default function ExportTable() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [status, setStatus] = useState("");
  const [q, setQ] = useState("");

  async function fetchData(p = page) {
    const params = new URLSearchParams({
      page: String(p),
      page_size: String(pageSize),
    });
    if (status) params.set("status", status);
    if (q) params.set("q", q);
    const res = await fetch(`/api/exports?${params.toString()}`);
    const data = await res.json();
    setItems(data.items);
    setTotal(data.total);
    setPage(data.page);
  }

  useEffect(() => { fetchData(1); /* eslint-disable-next-line */ }, [status, pageSize]);
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  async function handleRetry(id) {
    const res = await fetch(`/api/exports/${id}/retry`, { method: "POST" });
    if (res.ok) {
      await fetchData(page);
    } else {
      const err = await res.json();
      alert(err.detail || "Retry failed");
    }
  }

  function signedUrl(filePath, expirySec = 3600) {
    return filePath.startsWith("/api/") ? filePath : `/api/files/download?path=${encodeURIComponent(filePath)}`;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <input
          className="border rounded px-2 py-1"
          placeholder="Search exports…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <select className="border rounded px-2 py-1" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          <option value="queued">queued</option>
          <option value="processing">processing</option>
          <option value="retrying">retrying</option>
          <option value="failed">failed</option>
          <option value="completed">completed</option>
        </select>
        <button className="border rounded px-3 py-1" onClick={() => fetchData(1)}>Filter</button>
        <div className="ml-auto flex items-center gap-2">
          <span>Rows:</span>
          <select className="border rounded px-2 py-1" value={pageSize} onChange={(e)=>setPageSize(Number(e.target.value))}>
            {[10,20,50,100].map(n => <option key={n} value={n}>{n}</option>)}
          </select>
        </div>
      </div>

      <div className="overflow-x-auto border rounded">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left p-2">ID</th>
              <th className="text-left p-2">Type</th>
              <th className="text-left p-2">Status</th>
              <th className="text-left p-2">Attempts</th>
              <th className="text-left p-2">File</th>
              <th className="text-left p-2">Preview</th>
              <th className="text-left p-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map(job => {
              const canRetry = ["failed","retrying","queued"].includes(job.status) && job.attempts < job.max_attempts;
              const url = job.file_path ? signedUrl(job.file_path) : null;
              return (
                <tr key={job.id} className="border-t">
                  <td className="p-2">{job.id}</td>
                  <td className="p-2">{job.job_type || "-"}</td>
                  <td className="p-2">{job.status}</td>
                  <td className="p-2">{job.attempts}/{job.max_attempts}</td>
                  <td className="p-2">
                    {url ? <a className="text-blue-600 underline" href={url} target="_blank" rel="noreferrer">Download</a> : "—"}
                  </td>
                  <td className="p-2">
                    {url ? <div className="max-w-xs"><PreviewFile url={url} type={job.file_type || "text/plain"} /></div> : "—"}
                  </td>
                  <td className="p-2">
                    {canRetry ? (
                      <button className="border rounded px-2 py-1" onClick={()=>handleRetry(job.id)}>Retry</button>
                    ) : "—"}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between">
        <span>Page {page} of {totalPages} • {total} total</span>
        <div className="flex gap-2">
          <button className="border rounded px-2 py-1" disabled={page<=1} onClick={()=>{setPage(p=>p-1); fetchData(page-1);}}>Prev</button>
          <button className="border rounded px-2 py-1" disabled={page>=totalPages} onClick={()=>{setPage(p=>p+1); fetchData(page+1);}}>Next</button>
        </div>
      </div>
    </div>
  );
}
