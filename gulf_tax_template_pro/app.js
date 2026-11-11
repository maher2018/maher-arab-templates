/* واجهة Gulf Tax Compliance Pro — دردشة وأخبار وعملات ومسح فواتير */
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const num = (n, digits = 0) => (n == null || Number.isNaN(Number(n)))
  ? "—"
  : new Intl.NumberFormat("ar-SA", {minimumFractionDigits: digits, maximumFractionDigits: digits}).format(Number(n));

let lastInvoice = null;
let lastResult = null;
let sessionCount = 0;
let sessionTax = 0;

/* ---------- الحالة والعملات ---------- */
async function loadHealth() {
  try {
    const res = await fetch("/api/health", {cache: "no-store"});
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    $("statusText").textContent = data.engine ? "الخادم متصل" : "متصل";
    document.querySelector("#statusPill .dot").className = "dot ok";
  } catch (err) {
    $("statusText").textContent = "الخادم غير متاح";
    document.querySelector("#statusPill .dot").className = "dot bad";
  }
}

async function loadRates() {
  try {
    const res = await fetch("/api/rates", {cache: "no-store"});
    const data = await res.json();
    const codes = Object.keys(data.rates || {});
    if (!codes.length) throw new Error("لا توجد أسعار");
    const arrow = (v) => (v >= 0 ? '<span class="up">▲</span>' : '<span class="down">▼</span>');
    const html = codes.map((code) => {
      const rate = Number(data.rates[code]);
      const change = Number((data.changes || {})[code] || 0);
      return `<span class="ticker-item"><b>${esc(code)}</b> ${num(rate, 4)} ${arrow(change)}</span>`;
    }).join("");
    $("tickerTrack").innerHTML = html +
      `<span class="ticker-item">Riyal base · ${esc(data.source || "")} · ${esc(data.updated_at || "")}</span>`;
  } catch (err) {
    $("tickerTrack").innerHTML = '<span class="ticker-item">تعذّر تحميل أسعار العملات — سيُستخدم آخر تحديث محفوظ.</span>';
  }
}

/* ---------- الأخبار ---------- */
async function loadNews() {
  try {
    const res = await fetch("/api/news", {cache: "no-store"});
    const data = await res.json();
    const items = data.items || [];
    $("statNews").textContent = num(items.length);
    $("newsList").innerHTML = items.length ? items.map((n) => `
      <article class="news">
        <div class="meta"><span class="tag-sm">${esc(n.tag || "الخليج")}</span><span>${esc(n.date || "")}</span></div>
        <h3>${esc(n.title)}</h3>
        <p>${esc(n.summary)}</p>
        ${n.action ? `<div class="action">✔ ${esc(n.action)}</div>` : ""}
      </article>`).join("") : '<p class="fine">لا توجد أخبار محفوظة بعد — حدّث ملف data/market_news.json.</p>';
    $("newsMeta").textContent = "آخر تحديث: " + (data.updated_at || "—");
  } catch (err) {
    $("newsList").innerHTML = '<p class="fine">تعذّر تحميل الأخبار.</p>';
  }
}

/* ---------- المساعد ---------- */
function appendMsg(role, text) {
  const wrap = document.createElement("div");
  wrap.className = "msg " + (role === "user" ? "user" : "bot");
  wrap.innerHTML = '<div class="bubble">' + esc(text) + "</div>";
  $("chatLog").appendChild(wrap);
  $("chatLog").scrollTop = $("chatLog").scrollHeight;
  return wrap;
}

async function ask(question) {
  const q = String(question || "").trim();
  if (!q) return;
  appendMsg("user", q);
  $("chatInput").value = "";
  const typing = appendMsg("bot", "يكتب…");
  typing.classList.add("typing");
  try {
    const res = await fetch("/api/assistant", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({question: q, invoice: lastInvoice})
    });
    const data = await res.json();
    typing.remove();
    appendMsg("bot", data.answer || "لم أجد إجابة.");
    if (Array.isArray(data.suggestions) && data.suggestions.length) {
      $("suggestions").innerHTML = data.suggestions
        .map((s) => `<button class="chip" data-q="${esc(s)}">${esc(s)}</button>`).join("");
      bindChips();
    }
  } catch (err) {
    typing.remove();
    appendMsg("bot", "تعذّر الوصول إلى المساعد: " + err.message);
  }
}

function bindChips() {
  document.querySelectorAll("#suggestions .chip").forEach((chip) => {
    chip.addEventListener("click", () => ask(chip.getAttribute("data-q")));
  });
}

/* ---------- مسح الفواتير ---------- */
function setScanMsg(text, kind) {
  const el = $("scanMsg");
  el.className = "msg " + (kind || "");
  el.textContent = text || "";
}

function renderResult(data) {
  lastResult = data;
  const rows = data.invoices || [];
  const totals = data.totals || {};
  $("totals").hidden = false;
  $("tableWrap").hidden = false;
  $("tCount").textContent = num(totals.count || rows.length);
  $("tTotal").textContent = num(totals.total, 2);
  $("tTax").textContent = num(totals.tax, 2);
  $("tReview").textContent = num(totals.needs_review || 0);
  $("scanBody").innerHTML = rows.map((inv, i) => {
    const low = Number(inv.confidence || 0) < 0.8;
    const conf = '<span class="' + (low ? "low" : "") + '">' + num((inv.confidence || 0) * 100) + "%</span>";
    return `<tr>
      <td>${num(i + 1)}</td>
      <td>${esc(inv.supplier || "—")}</td>
      <td>${esc(inv.date || "—")}</td>
      <td>${esc(inv.subtotal == null ? "—" : num(inv.subtotal, 2))}</td>
      <td>${esc(inv.tax == null ? "—" : num(inv.tax, 2))}</td>
      <td>${esc(inv.total == null ? "—" : num(inv.total, 2))}</td>
      <td>${esc(inv.rate == null ? "—" : num(inv.rate) + "%")}</td>
      <td>${conf}</td>
    </tr>`;
  }).join("");
  $("exportBtn").disabled = !rows.length;
  $("jsonBtn").disabled = !rows.length;
  if (rows.length) lastInvoice = rows[0];

  sessionCount += rows.length;
  sessionTax += Number(totals.tax || 0);
  $("statInvoices").textContent = num(sessionCount);
  $("statTax").textContent = num(sessionTax, 2);

  const q = data.quota || null;
  let msg = `تم مسح ${num(rows.length)} فاتورة في ${num(data.elapsed_ms || 0)} ms`;
  if (q && q.capacity) msg += ` · استهلاك السعة ${num(q.used)}/${num(q.capacity)} هذا الشهر`;
  if (q && q.deferred) msg += ` · ${num(q.deferred)} فاتورة مؤجلة للدورة التالية (سماحية الباقة)`;
  setScanMsg(msg, "ok");
}

async function scan() {
  const text = $("scanText").value.trim();
  if (!text) { setScanMsg("الصق نص الفواتير أو أفلت ملفًا أولًا.", "bad"); return; }
  const btn = $("scanBtn");
  btn.disabled = true; btn.textContent = "جارٍ المسح…";
  setScanMsg("يُعالج النص على الخادم…");
  try {
    const res = await fetch("/api/scan", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({text})
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "فشل المسح");
    renderResult(data);
  } catch (err) {
    setScanMsg("تعذّر المسح: " + err.message, "bad");
  } finally {
    btn.disabled = false; btn.textContent = "امسح الفواتير";
  }
}

function toCsv(rows) {
  const head = ["المورد", "التاريخ", "قبل الضريبة", "الضريبة", "الإجمالي", "النسبة", "الثقة"];
  const lines = rows.map((i) => [i.supplier || "", i.date || "", i.subtotal ?? "", i.tax ?? "", i.total ?? "", i.rate ?? "", i.confidence ?? ""]
    .map((v) => '"' + String(v).replace(/"/g, '""') + '"').join(","));
  return "\ufeff" + [head.join(",")].concat(lines).join("\r\n");
}

/* ---------- الأحداث ---------- */
$("chatForm").addEventListener("submit", (e) => { e.preventDefault(); ask($("chatInput").value); });
$("scanBtn").addEventListener("click", scan);
$("newsRefresh").addEventListener("click", loadNews);

$("sampleBtn").addEventListener("click", async () => {
  try {
    const res = await fetch("/api/sample");
    const data = await res.json();
    $("scanText").value = data.text || "";
    setScanMsg("حُمّل نموذج واتساب (٣ فواتير) — اضغط «امسح الفواتير».");
  } catch (err) { setScanMsg("تعذّر تحميل النموذج.", "bad"); }
});

$("clearBtn").addEventListener("click", () => {
  $("scanText").value = "";
  $("totals").hidden = true; $("tableWrap").hidden = true;
  $("exportBtn").disabled = true; $("jsonBtn").disabled = true;
  setScanMsg("");
});

$("pick").addEventListener("click", () => $("file").click());
$("file").addEventListener("change", (e) => readFile(e.target.files[0]));
$("drop").addEventListener("dragover", (e) => { e.preventDefault(); $("drop").classList.add("hover"); });
$("drop").addEventListener("dragleave", () => $("drop").classList.remove("hover"));
$("drop").addEventListener("drop", (e) => {
  e.preventDefault(); $("drop").classList.remove("hover");
  const file = e.dataTransfer.files && e.dataTransfer.files[0];
  readFile(file);
});

function readFile(file) {
  if (!file) return;
  if (!/\.(txt|csv)$/i.test(file.name)) { setScanMsg("الصيغة المدعومة TXT أو CSV.", "bad"); return; }
  if (file.size > 2 * 1024 * 1024) { setScanMsg("الحد الأقصى ٢ ميغابايت.", "bad"); return; }
  const reader = new FileReader();
  reader.onload = () => {
    $("scanText").value = String(reader.result || "");
    setScanMsg(`حُمّل الملف ${file.name} — اضغط «امسح الفواتير».`);
  };
  reader.onerror = () => setScanMsg("تعذّر قراءة الملف.", "bad");
  reader.readAsText(file, "utf-8");
}

$("exportBtn").addEventListener("click", () => {
  if (!lastResult) return;
  const blob = new Blob([toCsv(lastResult.invoices)], {type: "text/csv;charset=utf-8"});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = "invoices-scan.csv"; a.click();
  URL.revokeObjectURL(url);
});

$("jsonBtn").addEventListener("click", async () => {
  if (!lastResult) return;
  try {
    await navigator.clipboard.writeText(JSON.stringify(lastResult.invoices, null, 2));
    setScanMsg("نُسخ JSON إلى الحافظة.", "ok");
  } catch (err) { setScanMsg("لم يسمح المتصفح بالنسخ — استخدم تصدير CSV.", "bad"); }
});

/* التنقل الناعم */
document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
  });
});

bindChips();
loadHealth();
loadRates();
loadNews();
