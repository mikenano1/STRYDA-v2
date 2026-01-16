export const API_BASE = process.env.EXPO_PUBLIC_API_BASE ?? 'https://pdf-library-14.preview.emergentagent.com';
export const DEV_DIAG = false; // Disabled by default for production

export async function pingHealth() {
  const url = `${API_BASE}/health`;
  const t0 = performance.now();
  try {
    const res = await fetch(url, { method: 'GET' });
    const ms = Math.round(performance.now() - t0);
    let text;
    
    try {
      // Try to parse as JSON first
      const jsonData = await res.json();
      text = JSON.stringify(jsonData);
    } catch {
      // Fallback to text if not JSON
      text = await res.text();
      // If it starts with HTML, it's likely an error page
      if (text.startsWith('<')) {
        text = 'HTML response (possibly CORS or 404)';
      }
    }
    
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
    
    let text;
    try {
      const jsonData = await res.json();
      text = JSON.stringify(jsonData, null, 2);
    } catch {
      text = await res.text();
      if (text.startsWith('<')) {
        text = 'HTML response (possibly CORS or 404)';
      }
    }
    
    return { ok: res.ok, status: res.status, ms, text };
  } catch (e:any) {
    return { ok: false, status: -1, ms: Math.round(performance.now() - t0), text: String(e?.message || e) };
  }
}