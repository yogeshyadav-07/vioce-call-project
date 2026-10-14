async function req(path, opts = {}) {
  let r;
  try { r = await fetch(path, opts); }
  catch { throw new Error('Network error: cannot reach the BhashaBridge server.'); }
  if (!r.ok) {
    let msg = `Server error (${r.status})`;
    try {
      const j = await r.json();
      if (j.detail && j.detail.message) msg = j.detail.message;
      else if (Array.isArray(j.detail)) msg = 'Invalid request.';
    } catch { /* keep default */ }
    throw new Error(msg);
  }
  return r;
}
const json = (body) => ({ method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });

export const getConfig = async () => (await req('/api/config')).json();
export const createRoom = async () => (await req('/api/rooms', { method: 'POST' })).json();
export const translate = async (text, source, target) => (await req('/api/translate', json({ text, source, target }))).json();
export const stt = async (blob, language) => {
  const f = new FormData();
  const ext = blob.type.includes('mp4') ? 'mp4' : 'webm';
  f.append('audio', blob, `speech.${ext}`);
  f.append('language', language);
  return (await req('/api/stt', { method: 'POST', body: f })).json();
};
export const tts = async (text, language) => (await req('/api/tts', json({ text, language }))).blob();
