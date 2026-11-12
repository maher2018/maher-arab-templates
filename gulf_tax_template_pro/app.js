/* نظام المحاسبة والامتثال الضريبي الخليجي — واجهة بلا أي مكتبة خارجية */
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const num = (n, digits = 0) => (n == null || n === "" || Number.isNaN(Number(n)))
  ? "—"
  : new Intl.NumberFormat("ar-SA", { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(Number(n));
const money = (n) => num(n, 2);

const ACCOUNT = (localStorage.getItem("at_gulf_account") || (function () {
  const id = "acc-" + Math.random().toString(36).slice(2, 9);
  localStorage.setItem("at_gulf_account", id);
  return id;
})());

const state = {
  countries: [],
  meta: null,
  items: [],
  invoice: null,
  plan: localStorage.getItem("at_gulf_plan") || "growth",
  plans: [],
  quota: null,
  ledgerTab: "sales",
  ledger: { sales: [], purchases: [] },
  scan: null,
  ocr: null,
  sessionScans: 0,
  sessionTax: 0,
};

const todayISO = () => new Date().toISOString().slice(0, 10);

async function api(path, options) {
  const res = await fetch(path, { cache: "no-store", ...(options || {}) });
  let data = null;
  try { data = await res.json(); } catch (err) { data = null; }
  if (!res.ok) throw new Error((data && data.error) || ("HTTP " + res.status));
  return data || {};
}

/* ================= التبويبات ================= */
function showView(name) {
  document.querySelectorAll(".view").forEach((v) => v.classList.toggle("active", v.id === "view-" + name));
  document.querySelectorAll("#tabsNav .tab").forEach((t) => t.classList.toggle("active", t.dataset.view === name));
  if (name === "return") loadReturn();
  if (name === "assistant") { loadNews(); loadTickets(); }
  if (name === "plans") { loadPlans(); }
  window.scrollTo({ top: 0, behavior: "smooth" });
}
document.querySelectorAll("#tabsNav .tab").forEach((tab) => {
  tab.addEventListener("click", () => showView(tab.dataset.view));
});

/* ================= الحالة والعملات ================= */
async function loadHealth() {
  try {
    const data = await api("/api/health");
    $("statusText").textContent = data.engine ? "الخادم متصل" : "متصل";
    document.querySelector("#statusPill .dot").className = "dot ok";
  } catch (err) {
    $("statusText").textContent = "الخادم غير متاح";
    document.querySelector("#statusPill .dot").className = "dot bad";
  }
}

async function loadRates() {
  try {
    const data = await api("/api/rates");
    const codes = Object.keys(data.rates || {});
    if (!codes.length) throw new Error("لا أسعار");
    const arrow = (v) => (v >= 0 ? '<span class="up">▲</span>' : '<span class="down">▼</span>');
    $("tickerTrack").innerHTML = codes.map((code) => {
      const change = Number((data.changes || {})[code] || 0);
      return `<span class="ticker-item"><b>${esc(code)}</b> ${num(data.rates[code], 4)} ${arrow(change)}</span>`;
    }).join("") + `<span class="ticker-item">الأساس ريال سعودي · ${esc(data.source || "")} · ${esc(data.updated_at || "")}</span>`;
  } catch (err) {
    $("tickerTrack").innerHTML = '<span class="ticker-item">تعذّر تحميل أسعار العملات — سيُستخدم آخر تحديث محفوظ.</span>';
  }
}

async function loadNews() {
  try {
    const data = await api("/api/news");
    const items = data.items || [];
    $("statNews").textContent = num(items.length);
    $("newsList").innerHTML = items.length ? items.map((n) => `
      <article class="news">
        <div class="meta"><span class="tag-sm">${esc(n.tag || "الخليج")}</span><span>${esc(n.date || "")}</span></div>
        <h3>${esc(n.title)}</h3>
        <p>${esc(n.summary)}</p>
        ${n.action ? `<div class="action">✔ ${esc(n.action)}</div>` : ""}
      </article>`).join("") : '<p class="fine">لا توجد أخبار محفوظة — حدّث data/market_news.json.</p>';
    $("newsMeta").textContent = "آخر تحديث: " + (data.updated_at || "—");
  } catch (err) {
    $("newsList").innerHTML = '<p class="fine">تعذّر تحميل الأخبار.</p>';
  }
}

/* ================= الدول والنسب ================= */
async function loadCountries() {
  const data = await api("/api/countries");
  state.countries = data.countries || [];
  state.meta = data.default || null;
  const options = state.countries.map((c) => `<option value="${esc(c.code)}">${esc(c.name)} — ${num(c.vat_rate)}%</option>`).join("");
  $("invCountry").innerHTML = options;
  $("retCountry").innerHTML = options;
  if (state.meta) {
    $("invCountry").value = state.meta.code;
    $("retCountry").value = state.meta.code;
    applyCountry(state.meta.code);
  }
  $("invDate").value = todayISO();
  fillPeriods();
}

function countryBy(code) {
  return state.countries.find((c) => c.code === code) || state.meta;
}

function applyCountry(code) {
  const c = countryBy(code);
  if (!c) return;
  state.meta = c;
  $("invRate").value = c.vat_rate;
  $("sellerVatLabel").textContent = c.tax_no_label + " (" + c.tax_no_hint + ")";
  $("invSpec").textContent = c.qr_spec.split("—")[0].trim();
  $("authorityNote").textContent = `${c.name}: ${c.authority} · ${c.filing}`;
  recompute();
}

function fillPeriods() {
  const code = $("retCountry").value || (state.meta && state.meta.code) || "SA";
  const quarterly = (countryBy(code) || {}).period === "quarterly";
  const out = [];
  const cursor = new Date();
  cursor.setDate(1);
  for (let i = 0; i < 24 && out.length < 8; i++) {
    const key = cursor.toISOString().slice(0, 7);
    if (!quarterly || Number(key.slice(5, 7)) % 3 === 0) out.push(key);
    cursor.setMonth(cursor.getMonth() - 1);
  }
  const current = new Date().toISOString().slice(0, 7);
  $("retPeriod").innerHTML = out.map((p) => `<option value="${p}">${p}</option>`).join("");
  if (out.includes(current)) $("retPeriod").value = current;
}

$("invCountry").addEventListener("change", (e) => applyCountry(e.target.value));
$("retCountry").addEventListener("change", () => { fillPeriods(); loadReturn(); });
$("retPeriod").addEventListener("change", loadReturn);
$("invRate").addEventListener("input", recompute);

/* ================= الفواتير الإلكترونية ================= */
function blankItem() {
  return { description: "", quantity: 1, unit_price: 0, discount: 0 };
}

function renderItems() {
  $("itemsBody").innerHTML = state.items.map((item, index) => `
    <tr data-row="${index}">
      <td>${num(index + 1)}</td>
      <td><input class="cell" data-f="description" type="text" value="${esc(item.description)}" placeholder="وصف الخدمة أو المنتج"></td>
      <td><input class="cell narrow" data-f="quantity" type="number" min="0" step="1" value="${esc(item.quantity)}"></td>
      <td><input class="cell narrow" data-f="unit_price" type="number" min="0" step="0.01" value="${esc(item.unit_price)}"></td>
      <td><input class="cell narrow" data-f="discount" type="number" min="0" max="100" step="1" value="${esc(item.discount)}"></td>
      <td class="cell-out" data-out="net">—</td>
      <td class="cell-out" data-out="tax">—</td>
      <td class="cell-out strong" data-out="total">—</td>
      <td><button class="link danger" data-remove="${index}" type="button" aria-label="حذف البند">✕</button></td>
    </tr>`).join("");
  $("itemsBody").querySelectorAll("input[data-f]").forEach((input) => {
    input.addEventListener("input", (e) => {
      const row = e.target.closest("tr");
      const item = state.items[Number(row.dataset.row)];
      const field = e.target.dataset.f;
      item[field] = field === "description" ? e.target.value : e.target.value;
      recompute();
    });
  });
  $("itemsBody").querySelectorAll("[data-remove]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.items.splice(Number(btn.dataset.remove), 1);
      if (!state.items.length) state.items.push(blankItem());
      renderItems();
      recompute();
    });
  });
  recompute();
}

function computeClient() {
  const rate = Number($("invRate").value || 0) / 100;
  const includeVat = $("incVat").checked;
  let subtotal = 0, discount = 0, tax = 0;
  const rows = state.items.map((item) => {
    const qty = Math.max(0, Number(item.quantity) || 0);
    const price = Math.max(0, Number(item.unit_price) || 0);
    const discPct = Math.min(100, Math.max(0, Number(item.discount) || 0));
    const gross = qty * price;
    const discAmt = gross * discPct / 100;
    const netBase = gross - discAmt;
    let net, lineTax;
    if (includeVat && rate > 0) { net = netBase / (1 + rate); lineTax = netBase - net; }
    else { net = netBase; lineTax = net * rate; }
    net = Math.round(net * 100) / 100;
    lineTax = Math.round(lineTax * 100) / 100;
    subtotal += net; discount += discAmt; tax += lineTax;
    return { net, lineTax, total: Math.round((net + lineTax) * 100) / 100, discAmt };
  });
  return {
    rows,
    subtotal: Math.round(subtotal * 100) / 100,
    discount: Math.round(discount * 100) / 100,
    tax: Math.round(tax * 100) / 100,
    total: Math.round((subtotal + tax) * 100) / 100,
    rate: rate * 100,
  };
}

function recompute() {
  const result = computeClient();
  state.items.forEach((item, index) => {
    const row = $("itemsBody").querySelector(`tr[data-row="${index}"]`);
    if (!row) return;
    const values = { net: result.rows[index].net, tax: result.rows[index].lineTax, total: result.rows[index].total };
    Object.keys(values).forEach((key) => {
      const cell = row.querySelector(`[data-out="${key}"]`);
      if (cell) cell.textContent = money(values[key]);
    });
  });
  $("sumSubtotal").textContent = money(result.subtotal);
  $("sumDiscount").textContent = money(result.discount);
  $("sumTax").textContent = money(result.tax);
  $("sumTotal").textContent = money(result.total) + " " + ((countryBy($("invCountry").value) || {}).currency || "");
}

$("addItem").addEventListener("click", () => {
  state.items.push(blankItem());
  renderItems();
});
$("incVat").addEventListener("change", recompute);

function invoicePayload(save) {
  return {
    account: ACCOUNT,
    country: $("invCountry").value,
    vat_rate: $("invRate").value,
    date: $("invDate").value || todayISO(),
    number: $("invNumber").value.trim(),
    prices_include_vat: $("incVat").checked,
    save: !!save,
    seller: {
      name: $("sellerName").value, vat_number: $("sellerVat").value,
      address: $("sellerAddress").value, email: $("sellerEmail").value, phone: $("sellerPhone").value,
    },
    buyer: {
      name: $("buyerName").value, vat_number: $("buyerVat").value,
      address: $("buyerAddress").value, email: $("buyerEmail").value,
    },
    items: state.items.filter((item) => String(item.description).trim()),
  };
}

function setInvMsg(text, kind) {
  const el = $("invMsg");
  el.className = "msg " + (kind || "");
  el.textContent = text || "";
}

async function issueInvoice(save) {
  const button = save ? $("saveInvBtn") : $("issueBtn");
  const label = button.textContent;
  button.disabled = true;
  button.textContent = "جارٍ المعالجة…";
  setInvMsg("يتحقق الخادم من البيانات ويحسب الضريبة ويولّد رمز QR…");
  try {
    const inv = await api("/api/einvoice", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(invoicePayload(save)),
    });
    state.invoice = inv;
    fillQrBox(inv);
    fillPrintDoc(inv);
    $("printBtn").disabled = false;
    $("saveInvBtn").disabled = false;
    const notes = (inv.notes || []).join(" ");
    setInvMsg(`أُصدرت الفاتورة ${inv.number} — الإجمالي ${money(inv.total)} ${inv.currency}` +
      (save && inv.saved ? " · حُفظت في سجل المبيعات." : ".") + (notes ? " " + notes : ""), "ok");
    if (save && inv.saved) { state.sessionScans += 1; $("statInvoices").textContent = num(state.sessionScans); loadReturn(); }
  } catch (err) {
    setInvMsg("تعذّر الإصدار: " + err.message, "bad");
  } finally {
    button.disabled = false;
    button.textContent = label;
  }
}

$("issueBtn").addEventListener("click", () => issueInvoice(false));
$("saveInvBtn").addEventListener("click", () => issueInvoice(true));
$("printBtn").addEventListener("click", () => { if (state.invoice) window.print(); });

$("resetInvBtn").addEventListener("click", () => {
  ["sellerAddress", "sellerEmail", "sellerPhone", "buyerName", "buyerVat", "buyerAddress", "buyerEmail", "invNumber"]
    .forEach((id) => { $(id).value = ""; });
  state.items = [blankItem()];
  state.invoice = null;
  $("qrBox").hidden = true;
  $("printBtn").disabled = true;
  $("saveInvBtn").disabled = true;
  $("invDate").value = todayISO();
  renderItems();
  setInvMsg("");
});

function fillQrBox(inv) {
  $("qrBox").hidden = false;
  $("qrImg").innerHTML = inv.qr && inv.qr.svg ? inv.qr.svg : '<p class="fine">لا تتوفر صورة QR — ثبّت الحزمة: python -m pip install segno</p>';
  $("qrSpec").textContent = (inv.qr && inv.qr.spec) || "—";
  $("qrPayload").textContent = (inv.qr && inv.qr.payload) || "—";
  $("invHash").textContent = inv.hash || "—";
}

$("copyQrBtn").addEventListener("click", async () => {
  if (!state.invoice) return;
  try {
    await navigator.clipboard.writeText(state.invoice.qr.payload);
    setInvMsg("نُسخت حمولة QR إلى الحافظة.", "ok");
  } catch (err) { setInvMsg("لم يسمح المتصفح بالنسخ.", "bad"); }
});

function fillPrintDoc(inv) {
  $("pSeller").textContent = inv.seller.name;
  $("pSellerAddress").textContent = inv.seller.address || "";
  $("pSellerVat").textContent = inv.seller.vat_number;
  $("pSellerContact").textContent = [inv.seller.email, inv.seller.phone].filter(Boolean).join(" · ");
  $("pCountry").textContent = inv.country.name + " — " + inv.country.authority;
  $("pNumber").textContent = inv.number;
  $("pDate").textContent = inv.issued_at;
  $("pCurrency").textContent = inv.currency;
  $("pBuyer").textContent = inv.buyer.name + (inv.buyer.address ? " — " + inv.buyer.address : "");
  $("pBuyerVat").textContent = inv.buyer.vat_number ? "الرقم الضريبي: " + inv.buyer.vat_number : "";
  $("pItems").innerHTML = inv.items.map((item) => `<tr>
      <td>${esc(item.description)}</td>
      <td>${num(item.quantity, 2)}</td>
      <td>${money(item.unit_price)}</td>
      <td>${money(item.discount_amount)}</td>
      <td>${money(item.net)}</td>
      <td>${money(item.tax)}</td>
      <td>${money(item.total)}</td>
    </tr>`).join("");
  $("pSubtotal").textContent = money(inv.subtotal);
  $("pRate").textContent = num(inv.vat_rate);
  $("pTax").textContent = money(inv.tax);
  $("pTotal").textContent = money(inv.total) + " " + inv.currency;
  $("pQr").innerHTML = inv.qr && inv.qr.svg ? inv.qr.svg : "";
  $("pHref").textContent = (inv.qr && inv.qr.payload) || "";
  $("pHash").textContent = inv.hash;
  $("pSpec").textContent = (inv.qr && inv.qr.spec) || "";
}

/* ================= الإقرار الضريبي ================= */
async function loadReturn() {
  const country = $("retCountry").value || "SA";
  const period = $("retPeriod").value;
  if (!period) return;
  try {
    const tr = await api(`/api/taxreturn?account=${encodeURIComponent(ACCOUNT)}&country=${encodeURIComponent(country)}&period=${encodeURIComponent(period)}`);
    $("kpiOutput").textContent = money(tr.output_tax) + " " + tr.currency;
    $("kpiOutputSub").textContent = `${num(tr.sales_count)} فاتورة · وعاء ${money(tr.taxable_sales)}`;
    $("kpiInput").textContent = money(tr.input_tax) + " " + tr.currency;
    $("kpiInputSub").textContent = `${num(tr.purchases_count)} فاتورة · وعاء ${money(tr.taxable_purchases)}`;
    $("kpiNet").textContent = money(tr.net) + " " + tr.currency;
    $("kpiStatus").textContent = tr.status + (tr.credit ? " (رصيد " + money(tr.credit) + ")" : "");
    $("kpiNet").className = tr.net > 0 ? "due" : "credit";
    $("kpiDue").textContent = tr.due.due;
    $("kpiDueNote").textContent = tr.due.note;
    $("returnNote").textContent = tr.net > 0
      ? `صافي الضريبة المستحقة للهيئة لهذه الفترة: ${money(tr.net)} ${tr.currency}. النسبة الفعلية ${num(tr.effective_rate, 2)}%.`
      : tr.net < 0
        ? `المشتريات أعلى من المبيعات — رصيد دائن ${money(tr.credit)} ${tr.currency} يُرحَّل للفترة التالية.`
        : "لا مستحقات ولا رصيد لهذه الفترة.";
    state.ledger = { sales: tr.sales || [], purchases: tr.purchases || [] };
    $("countSales").textContent = num(tr.sales_count);
    $("countPurchases").textContent = num(tr.purchases_count);
    $("statNet").textContent = money(tr.net);
    renderLedger();
  } catch (err) {
    $("returnNote").textContent = "تعذّر حساب الإقرار: " + err.message;
  }
}

$("refreshReturn").addEventListener("click", loadReturn);

document.querySelectorAll("[data-ledger]").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("[data-ledger]").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    state.ledgerTab = btn.dataset.ledger;
    renderLedger();
  });
});

function renderLedger() {
  const kind = state.ledgerTab;
  const rows = state.ledger[kind] || [];
  if (kind === "sales") {
    $("ledgerHead").innerHTML = "<tr><th>رقم الفاتورة</th><th>التاريخ</th><th>العميل</th><th>قبل الضريبة</th><th>الضريبة</th><th>الإجمالي</th><th></th></tr>";
  } else {
    $("ledgerHead").innerHTML = "<tr><th>المورد</th><th>التاريخ</th><th>قبل الضريبة</th><th>الضريبة</th><th>الإجمالي</th><th>المصدر</th><th></th></tr>";
  }
  if (!rows.length) {
    $("ledgerBody").innerHTML = `<tr><td colspan="7" class="fine">لا صفوف بعد — ${kind === "sales" ? "أصدر فاتورة واحفظها." : "امسح فاتورة مشتريات."}</td></tr>`;
    return;
  }
  $("ledgerBody").innerHTML = rows.map((row) => {
    const del = `<button class="link danger" data-del="${esc(row.id)}" type="button">حذف</button>`;
    return kind === "sales"
      ? `<tr><td class="mono">${esc(row.number || "—")}</td><td>${esc(row.date || "—")}</td><td>${esc(row.buyer || "—")}</td>
         <td>${money(row.subtotal)}</td><td>${money(row.tax)}</td><td class="strong">${money(row.total)}</td><td>${del}</td></tr>`
      : `<tr><td>${esc(row.supplier || "—")}</td><td>${esc(row.date || "—")}</td>
         <td>${money(row.subtotal)}</td><td>${money(row.tax)}</td><td class="strong">${money(row.total)}</td>
         <td class="fine">${esc(row.source || "")}</td><td>${del}</td></tr>`;
  }).join("");
  $("ledgerBody").querySelectorAll("[data-del]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        await api(`/api/ledger/${kind}/${encodeURIComponent(btn.dataset.del)}?account=${encodeURIComponent(ACCOUNT)}`, { method: "DELETE" });
        loadReturn();
      } catch (err) { $("returnNote").textContent = "تعذّر الحذف: " + err.message; }
    });
  });
}

/* ================= الماسح النصي ================= */
function setScanMsg(text, kind) {
  const el = $("scanMsg");
  el.className = "msg " + (kind || "");
  el.textContent = text || "";
}

let lastScan = null;

function renderScanResult(data) {
  lastScan = data;
  const rows = data.invoices || [];
  const totals = data.totals || {};
  $("totals").hidden = false;
  $("tableWrap").hidden = false;
  $("tCount").textContent = num(totals.count || rows.length);
  $("tTotal").textContent = money(totals.total);
  $("tTax").textContent = money(totals.tax);
  $("tReview").textContent = num(totals.needs_review || 0);
  $("scanBody").innerHTML = rows.map((inv, i) => {
    const low = Number(inv.confidence || 0) < 0.8;
    return `<tr>
      <td>${num(i + 1)}</td><td>${esc(inv.supplier || "—")}</td><td>${esc(inv.date || "—")}</td>
      <td>${money(inv.subtotal)}</td><td>${money(inv.tax)}</td><td>${money(inv.total)}</td>
      <td>${inv.rate == null ? "—" : num(inv.rate) + "%"}</td>
      <td class="${low ? "low" : ""}">${num((inv.confidence || 0) * 100)}%</td></tr>`;
  }).join("");
  $("exportBtn").disabled = !rows.length;
  state.sessionScans += rows.length;
  state.sessionTax += Number(totals.tax || 0);
  $("statInvoices").textContent = num(state.sessionScans);
  $("statTax").textContent = money(state.sessionTax);
  const q = data.quota || null;
  let msg = `تم مسح ${num(rows.length)} فاتورة في ${num(data.elapsed_ms || 0)} ms`;
  if (q && q.capacity) msg += ` · استهلاك السعة ${num(q.used)}/${num(q.capacity)}`;
  if (q && q.deferred) msg += ` · ${num(q.deferred)} فاتورة مؤجلة (سماحية الباقة)`;
  setScanMsg(msg, "ok");
}

async function scanText() {
  const text = $("scanText").value.trim();
  if (!text) { setScanMsg("الصق نص الفواتير أو أفلت ملفًا أولًا.", "bad"); return; }
  const btn = $("scanBtn");
  btn.disabled = true; btn.textContent = "جارٍ المسح…";
  setScanMsg("يُعالج النص على الخادم…");
  try {
    const data = await api("/api/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, account: ACCOUNT, plan: state.plan }),
    });
    if (!data.ok) throw new Error(data.error || "فشل المسح");
    renderScanResult(data);
  } catch (err) {
    setScanMsg("تعذّر المسح: " + err.message, "bad");
  } finally {
    btn.disabled = false; btn.textContent = "امسح الفواتير";
  }
}

$("scanBtn").addEventListener("click", scanText);
$("newsRefresh").addEventListener("click", loadNews);

$("addPurchasesBtn").addEventListener("click", async () => {
  if (!lastScan || !(lastScan.invoices || []).length) return;
  try {
    const data = await api("/api/ledger", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ account: ACCOUNT, source: "scan", rows: lastScan.invoices }),
    });
    setScanMsg(`أُضيفت ${num(data.count)} فاتورة إلى سجل المشتريات — حدّث الإقرار لرؤية الخصم.`, "ok");
  } catch (err) { setScanMsg("تعذّرت الإضافة: " + err.message, "bad"); }
});

$("sampleBtn").addEventListener("click", async () => {
  try {
    const data = await api("/api/sample");
    $("scanText").value = data.text || "";
    setScanMsg("حُمّل نموذج واتساب (٣ فواتير) — اضغط «امسح الفواتير».");
  } catch (err) { setScanMsg("تعذّر تحميل النموذج.", "bad"); }
});

$("exportBtn").addEventListener("click", () => {
  if (!lastScan) return;
  const head = ["المورد", "التاريخ", "قبل الضريبة", "الضريبة", "الإجمالي", "النسبة", "الثقة"];
  const lines = lastScan.invoices.map((i) => [i.supplier || "", i.date || "", i.subtotal ?? "", i.tax ?? "", i.total ?? "", i.rate ?? "", i.confidence ?? ""]
    .map((v) => '"' + String(v).replace(/"/g, '""') + '"').join(","));
  const blob = new Blob(["\ufeff" + [head.join(",")].concat(lines).join("\r\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = "invoices-scan.csv"; a.click();
  URL.revokeObjectURL(url);
});

async function bulkTest() {
  const total = 500;
  const lines = [];
  for (let i = 1; i <= total; i++) {
    const subtotal = 100 + (i % 900);
    const tax = Math.round(subtotal * 0.15 * 100) / 100;
    lines.push("المورد: شركة الاختبار " + i + "\nالتاريخ: 2026-11-" + String((i % 28) + 1).padStart(2, "0") +
      "\nالإجمالي قبل الضريبة: " + subtotal.toFixed(2) + "\nالضريبة (15%): " + tax.toFixed(2) +
      "\nالإجمالي: " + (subtotal + tax).toFixed(2));
  }
  $("scanText").value = lines.join("\n\n");
  await scanText();
}
$("bulkBtn").addEventListener("click", bulkTest);

/* ================= ماسح الصور (OCR) ================= */
function showOcr(data) {
  state.ocr = data;
  const inv = data.invoice || {};
  $("ocrResult").hidden = false;
  $("ocrMode").textContent = data.mode === "tesseract" ? "OCR فعلي — Tesseract" : "محاكاة استخراج";
  $("ocrModeTag").textContent = data.mode === "tesseract" ? "OCR فعلي" : "وضع المحاكاة";
  $("ocrNote").textContent = data.note || "";
  $("ocrSupplier").value = inv.supplier || "";
  $("ocrDate").value = inv.date || todayISO();
  $("ocrSubtotal").value = inv.subtotal ?? "";
  $("ocrTax").value = inv.tax ?? "";
  $("ocrConfidence").textContent = inv.confidence != null
    ? `درجة الثقة ${num(inv.confidence * 100)}% — راجع الحقول قبل الحفظ`
    : "";
}

async function sendImage(file) {
  if (!file) return;
  const form = new FormData();
  form.append("image", file);
  form.append("account", ACCOUNT);
  setScanMsg("جارٍ تحليل الصورة…");
  try {
    const res = await fetch("/api/ocr", { method: "POST", body: form });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "تعذّر تحليل الصورة");
    showOcr(data);
    setScanMsg("استُخرجت بيانات الفاتورة — راجعها ثم أضفها للسجل.", "ok");
  } catch (err) {
    setScanMsg("تعذّر تحليل الصورة: " + err.message, "bad");
  }
}

$("pick").addEventListener("click", () => $("file").click());
$("file").addEventListener("change", (e) => sendImage(e.target.files[0]));
$("drop").addEventListener("dragover", (e) => { e.preventDefault(); $("drop").classList.add("hover"); });
$("drop").addEventListener("dragleave", () => $("drop").classList.remove("hover"));
$("drop").addEventListener("drop", (e) => {
  e.preventDefault();
  $("drop").classList.remove("hover");
  sendImage(e.dataTransfer.files && e.dataTransfer.files[0]);
});

$("demoOcrBtn").addEventListener("click", () => {
  const canvas = document.createElement("canvas");
  canvas.width = 480;
  canvas.height = 240;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#ffffff"; ctx.fillRect(0, 0, 480, 240);
  ctx.fillStyle = "#123"; ctx.font = "bold 20px Tahoma";
  ctx.fillText("TAX INVOICE — فاتورة ضريبية", 24, 46);
  ctx.font = "16px Tahoma";
  ctx.fillText("المورد: شركة الأفق للتقنية", 24, 86);
  ctx.fillText("الإجمالي: 1,150.00  الضريبة: 150.00", 24, 120);
  ctx.fillText("2026-11-10", 24, 154);
  canvas.toBlob((blob) => {
    if (blob) sendImage(new File([blob], "demo-invoice.png", { type: "image/png" }));
  }, "image/png");
});

$("ocrSaveBtn").addEventListener("click", async () => {
  const subtotal = Number($("ocrSubtotal").value || 0);
  const tax = Number($("ocrTax").value || 0);
  const row = {
    supplier: $("ocrSupplier").value.trim() || "مورد غير معروف",
    date: $("ocrDate").value || todayISO(),
    subtotal,
    tax,
    total: Math.round((subtotal + tax) * 100) / 100,
    rate: subtotal > 0 ? Math.round((tax / subtotal) * 100) : 0,
    confidence: (state.ocr && state.ocr.invoice && state.ocr.invoice.confidence) || null,
  };
  try {
    const data = await api("/api/ledger", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ account: ACCOUNT, source: "ocr", rows: [row] }),
    });
    $("ocrResult").hidden = true;
    setScanMsg(`أُضيفت فاتورة ${row.supplier} إلى سجل المشتريات (${num(data.count)}).`, "ok");
  } catch (err) { setScanMsg("تعذّرت الإضافة: " + err.message, "bad"); }
});

/* ================= المساعد والمحاسب ================= */
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
    const data = await api("/api/assistant", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q, invoice: lastScan && lastScan.invoices ? lastScan.invoices[0] : null }),
    });
    typing.remove();
    appendMsg("bot", data.answer || "لم أجد إجابة.");
    if (Array.isArray(data.suggestions) && data.suggestions.length) {
      $("suggestions").innerHTML = data.suggestions
        .map((s) => `<button class="chip" type="button" data-q="${esc(s)}">${esc(s)}</button>`).join("");
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

$("chatForm").addEventListener("submit", (e) => { e.preventDefault(); ask($("chatInput").value); });

async function loadTickets() {
  try {
    const data = await api(`/api/support?account=${encodeURIComponent(ACCOUNT)}`);
    const list = data.messages || [];
    $("msgList").innerHTML = list.length ? list.map((m) => `
      <article class="msg-card">
        <div class="meta"><span class="tag-sm">${esc(m.ticket)}</span><span>${esc(String(m.created_at).replace("T", " "))}</span></div>
        <strong>${esc(m.topic)}</strong>
        <p>${esc(m.message)}</p>
      </article>`).join("") : '<p class="fine">لا رسائل بعد.</p>';
  } catch (err) { /* يبقى العرض السابق */ }
}

$("sendTicketBtn").addEventListener("click", async () => {
  const message = $("ticketMessage").value.trim();
  if (!message) { $("ticketMsg").textContent = "اكتب نص الرسالة أولًا."; $("ticketMsg").className = "msg bad"; return; }
  try {
    const data = await api("/api/support", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ account: ACCOUNT, topic: $("ticketTopic").value, message }),
    });
    $("ticketMsg").className = "msg ok";
    $("ticketMsg").textContent = `رقم التذكرة ${data.ticket} — ${data.reply}`;
    $("ticketMessage").value = "";
    loadTickets();
  } catch (err) {
    $("ticketMsg").className = "msg bad";
    $("ticketMsg").textContent = "تعذّر الإرسال: " + err.message;
  }
});

/* ================= الباقات ================= */
async function loadPlans() {
  try {
    const data = await api("/api/plans");
    state.plans = data.plans || [];
    renderPlans();
    await loadQuota();
  } catch (err) {
    $("planCards").innerHTML = '<p class="fine">تعذّر تحميل الباقات.</p>';
  }
}

function renderPlans() {
  $("planCards").innerHTML = state.plans.map((p) => {
    const active = p.key === state.plan;
    return `<article class="plan${active ? " active" : ""}">
      <h3>${esc(p.name)}</h3>
      <div class="plan-price">${num(p.price)} <small>ر.س / سنة</small></div>
      <div class="plan-scan">${num(p.scans)} فاتورة شهريًا</div>
      <ul>${(p.features || []).map((f) => `<li>${esc(f)}</li>`).join("")}</ul>
      <p class="fine">${esc(p.for || "")}</p>
      <button class="${active ? "" : "ghost"}" data-plan="${esc(p.key)}" type="button">${active ? "الباقة الحالية" : "اختيار الباقة"}</button>
    </article>`;
  }).join("");
  document.querySelectorAll("#planCards [data-plan]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      state.plan = btn.dataset.plan;
      localStorage.setItem("at_gulf_plan", state.plan);
      renderPlans();
      await loadQuota();
    });
  });
}

async function loadQuota() {
  try {
    const q = await api(`/api/quota?account=${encodeURIComponent(ACCOUNT)}&plan=${encodeURIComponent(state.plan)}`);
    state.quota = q;
    const pct = Math.min(100, Math.round((q.used / (q.capacity + q.grace || 1)) * 100));
    $("quotaBar").style.width = pct + "%";
    $("quotaBar").className = "bar-fill" + (pct >= 90 ? " danger" : pct >= 70 ? " warn" : "");
    $("quotaLabel").textContent = "استهلاك شهر " + q.period + " — باقة " + (q.plan_name || "");
    $("quotaValue").textContent = num(q.used) + " / " + num(q.capacity) + " فاتورة";
    $("quotaNote").textContent = q.deferred
      ? "تجاوزت السعة: " + num(q.deferred) + " فاتورة مؤجلة، وسماحية " + num(q.grace) + " استُهلكت."
      : "المتبقي: " + num(q.remaining) + " فاتورة + سماحية " + num(q.grace) + " — لا قيود لكل دقيقة.";
  } catch (err) { /* يبقى العرض السابق */ }
}

/* ================= الإقلاع ================= */
(async function boot() {
  state.items = [blankItem()];
  renderItems();
  bindChips();
  loadHealth();
  loadRates();
  loadNews();
  try {
    await loadCountries();
  } catch (err) {
    $("authorityNote").textContent = "تعذّر تحميل بيانات الدول: " + err.message;
  }
  loadPlans();
})();
