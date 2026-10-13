// Files a report from the benchmarks site as an issue on pie, with the page's screenshot.
// POST /report {text, context, image: "data:image/png;base64,..."} -> {url}
// GET  /shot/<id>.png serves a stored screenshot.
const ORIGINS = ["https://pie-project.github.io"];
const MAX_IMAGE = 3 * 1024 * 1024;
const MAX_TEXT = 5000;

const cors = (origin) => ({
  "Access-Control-Allow-Origin": ORIGINS.includes(origin) ? origin : ORIGINS[0],
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
});

const json = (body, status, origin) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", ...cors(origin) } });

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = request.headers.get("Origin") || "";

    if (request.method === "GET" && url.pathname.startsWith("/shot/")) {
      const object = await env.SHOTS.get(url.pathname.slice("/shot/".length));
      if (!object) return new Response("Not found", { status: 404 });
      return new Response(object.body, { headers: { "Content-Type": "image/png", "Cache-Control": "public, max-age=31536000, immutable" } });
    }
    if (request.method === "OPTIONS") return new Response(null, { headers: cors(origin) });
    if (request.method !== "POST" || url.pathname !== "/report") return new Response("Not found", { status: 404 });
    if (!ORIGINS.includes(origin)) return json({ error: "origin" }, 403, origin);

    let report;
    try {
      report = await request.json();
    } catch {
      return json({ error: "body" }, 400, origin);
    }
    const text = String(report.text || "").trim().slice(0, MAX_TEXT);
    const context = String(report.context || "").slice(0, 2000);
    if (!text) return json({ error: "empty" }, 400, origin);

    let shot = "";
    const match = /^data:image\/png;base64,([A-Za-z0-9+/=]+)$/.exec(report.image || "");
    if (match) {
      const bytes = Uint8Array.from(atob(match[1]), (c) => c.charCodeAt(0));
      if (bytes.length > MAX_IMAGE) return json({ error: "image too large" }, 413, origin);
      const id = `${Date.now()}-${crypto.randomUUID().slice(0, 8)}.png`;
      await env.SHOTS.put(id, bytes, { httpMetadata: { contentType: "image/png" } });
      shot = `${url.origin}/shot/${id}`;
    }

    const title = `[Benchmarks] ${text.split("\n")[0].slice(0, 70)}`;
    const body = `${text}\n\n${shot ? `![Screenshot](${shot})\n\n` : ""}---\n${context}\n\n_Sent from the benchmarks site._`;
    const created = await fetch(`https://api.github.com/repos/${env.REPO}/issues`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.GITHUB_TOKEN}`,
        Accept: "application/vnd.github+json",
        "User-Agent": "pie-benchmarks-report",
      },
      body: JSON.stringify({ title, body }),
    });
    if (!created.ok) return json({ error: "github", status: created.status }, 502, origin);
    const issue = await created.json();
    return json({ url: issue.html_url }, 201, origin);
  },
};
