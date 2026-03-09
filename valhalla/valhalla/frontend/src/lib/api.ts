const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api/v1";

export const api = {
  async login(email: string, password: string) {
    const r = await fetch(`${BASE}/auth/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password }) });
    if (!r.ok) throw new Error("login failed");
    return r.json();
  },
  async listLeads(token: string) {
    const r = await fetch(`${BASE}/leads?limit=50`, { headers: { Authorization: `Bearer ${token}` } });
    if (!r.ok) throw new Error("leads failed");
    return r.json();
  }
  ,
  async enqueueEmail(token: string, to: string[], subject: string, body: string) {
    const params = new URLSearchParams({ subject, body });
    const r = await fetch(`${BASE}/jobs/email?` + params.toString(), {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify(to),
    });
    if (!r.ok) throw new Error("enqueue email failed");
    return r.json();
  },
  async jobStatus(token: string, id: string) {
    const r = await fetch(`${BASE}/jobs/${id}`, { headers: { Authorization: `Bearer ${token}` } });
    if (!r.ok) throw new Error("job status failed");
    return r.json();
  }
};
