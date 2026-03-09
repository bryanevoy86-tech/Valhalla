"use client";
import { useState } from "react";
import { api } from "@/lib/api";

export default function Home() {
  const [token, setToken] = useState<string>("");
  const [leads, setLeads] = useState<any[]>([]);
  const [error, setError] = useState<string>("");

  async function doLogin() {
    try {
      setError("");
      const t = await api.login("admin@example.com", "changeme");
      setToken(t.access_token);
    } catch (e: any) {
      setError(e?.message ?? "Login failed");
    }
  }

  async function loadLeads() {
    try {
      setError("");
      const data = await api.listLeads(token);
      setLeads(data);
    } catch (e: any) {
      setError(e?.message ?? "Load failed");
    }
  }

  return (
    <main style={{ padding: 24, maxWidth: 960, margin: "0 auto" }}>
      <h1 style={{ marginBottom: 12 }}>Valhalla Frontend</h1>
      <p style={{ opacity: 0.8, marginTop: 0 }}>
        Pointing at <code>{process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api/v1"}</code>
      </p>

      <div style={{ display: "flex", gap: 12, marginTop: 12 }}>
        <button onClick={doLogin} style={{ padding: 10, borderRadius: 8, cursor: "pointer" }}>
          Login (seeded admin)
        </button>
        <button onClick={loadLeads} disabled={!token} style={{ padding: 10, borderRadius: 8, cursor: "pointer" }}>
          Load Leads
        </button>
      </div>

      {error && (
        <div style={{ marginTop: 12, padding: 12, border: "1px solid #444", borderRadius: 8 }}>
          <b>Error:</b> {error}
        </div>
      )}

      <pre style={{ marginTop: 12, background: "#111", padding: 12, borderRadius: 8, overflow: "auto" }}>
        {JSON.stringify(leads, null, 2)}
      </pre>

      {!token && (
        <p style={{ marginTop: 8, opacity: 0.7 }}>
          Tip: First create a user via <code>POST /api/v1/users</code>, then click Login.
        </p>
      )}
    </main>
  );
}
