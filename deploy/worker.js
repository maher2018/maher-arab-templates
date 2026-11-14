/**
 * المتجر العام على Cloudflare Workers.
 *
 * يقدّم ملفات store/ الثابتة، ويُمرّر بيانات جدول template من بابل عبر
 * /api/templates. التوكن يصل من متغيّر البيئة السري BUBBLE_TOKEN ولا يظهر
 * في أي استجابة يراها المتصفح.
 */
import fallbackData from "./fallback.json";

const DEFAULT_APP = "https://at-ai-lab.bubbleapps.io/version-test";
const CACHE_TTL_SECONDS = 60;
const API_PATHS = new Set(["/api/templates", "/api/templates/source", "/api/health"]);

let memo = { at: 0, payload: null };

function json(data, status = 200, extra = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "x-content-type-options": "nosniff",
      ...extra,
    },
  });
}

function str(value) {
  return value == null ? "" : String(value).trim();
}

function toItem(row) {
  const raw = str(row.price).replace(/,/g, "");
  const price = Number.parseFloat(raw);
  return {
    id: str(row._id),
    title: str(row.Title) || "بدون عنوان",
    category: str(row.Category) || "غير مصنّف",
    description: str(row.description),
    price: Number.isFinite(price) ? price : null,
    preview_url: str(row.preview_url),
  };
}

function buildPayload(source, rows) {
  const items = rows.map(toItem).sort((a, b) => {
    const byCat = a.category.localeCompare(b.category, "ar");
    if (byCat !== 0) return byCat;
    return (b.price || 0) - (a.price || 0);
  });
  return {
    source,
    count: items.length,
    categories: [...new Set(items.map((i) => i.category))].sort((a, b) => a.localeCompare(b, "ar")),
    updated_at: new Date().toISOString().slice(0, 19),
    items,
  };
}

async function fetchLive(env) {
  if (!env.BUBBLE_TOKEN) throw new Error("token_missing");
  const base = str(env.BUBBLE_APP_URL || DEFAULT_APP).replace(/\/+$/, "");
  const response = await fetch(`${base}/api/1.1/obj/template?limit=100`, {
    headers: {
      Authorization: `Bearer ${env.BUBBLE_TOKEN}`,
      Accept: "application/json",
    },
  });
  if (!response.ok) throw new Error(`bubble_status_${response.status}`);
  const body = await response.json();
  const rows = body && body.response && body.response.results;
  if (!Array.isArray(rows) || rows.length === 0) throw new Error("bubble_empty");
  return rows;
}

async function payloadFor(env) {
  const now = Date.now();
  if (memo.payload && now - memo.at < CACHE_TTL_SECONDS * 1000) return memo.payload;

  let payload;
  try {
    payload = buildPayload("bubble", await fetchLive(env));
  } catch (error) {
    let rows = [];
    try {
      rows = JSON.parse(fallbackData);
    } catch (parseError) {
      rows = [];
    }
    payload = buildPayload("local", Array.isArray(rows) ? rows : []);
    payload.note = "تعذّر الوصول إلى بابل؛ تُعرض نسخة محفوظة.";
  }
  memo = { at: now, payload };
  return payload;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (API_PATHS.has(url.pathname)) {
      const method = request.method.toUpperCase();
      if (method !== "GET" && method !== "HEAD") {
        return json({ error: "method_not_allowed" }, 405, { allow: "GET, HEAD" });
      }
      if (url.pathname === "/api/health") {
        return json({ ok: true, has_token: Boolean(env.BUBBLE_TOKEN) });
      }
      const payload = await payloadFor(env);
      if (url.pathname === "/api/templates/source") {
        return json({ source: payload.source, count: payload.count });
      }
      if (method === "HEAD") {
        return new Response(null, {
          status: 200,
          headers: {
            "content-type": "application/json; charset=utf-8",
            "cache-control": "public, max-age=30",
          },
        });
      }
      return json(payload, 200, { "cache-control": "public, max-age=30" });
    }

    return env.ASSETS.fetch(request);
  },
};
