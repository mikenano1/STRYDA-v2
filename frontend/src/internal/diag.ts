export const API_BASE = process.env.EXPO_PUBLIC_API_BASE ?? 'https://onsite-copilot.preview.emergentagent.com';
export const DEV_DIAG = process.env.EXPO_PUBLIC_DEV_DIAG === '1';

export async function pingHealth() {
  const url = `${API_BASE}/health`;
  const t0 = performance.now();
  try {
    const res = await fetch(url, { method: 'GET' });
    const ms = Math.round(performance.now() - t0);
    const text = await res.text();
    return { ok: res.ok, status: res.status, ms, text };
  } catch (e:any) {
    return { ok: false, status: -1, ms: Math.round(performance.now() - t0), text: String(e?.message || e) };
  }
}

export async function pingChat() {
  const url = `${API_BASE}/api/chat`;
  const t0 = performance.now();
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: 'minimum apron flashing cover', session_id: 'diag_test' })
    });
    const ms = Math.round(performance.now() - t0);
    const text = await res.text();
    return { ok: res.ok, status: res.status, ms, text };
  } catch (e:any) {
    return { ok: false, status: -1, ms: Math.round(performance.now() - t0), text: String(e?.message || e) };
  }
}