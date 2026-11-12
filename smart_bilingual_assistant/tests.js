/* tests.js — اختبارات سريعة للأسئلة الشائعة (عربي/إنجليزي) */
(function (root) {
  "use strict";

  const CASES = [
    // ===== العربية: فصحى =====
    { q: "ما نسبة ضريبة القيمة المضافة في السعودية؟", expect: "rates", country: "SA" },
    { q: "كم نسبة الضريبة في الإمارات؟", expect: "rates", country: "AE" },
    { q: "هل أحتاج أسجل؟", expect: "registration" },
    { q: "متى آخر موعد لتقديم الإقرار الضريبي؟", expect: "deadline" },
    { q: "ما الحقول المطلوبة في الفاتورة الضريبية؟", expect: "fields" },
    { q: "كيف أخصم ضريبة المشتريات؟", expect: "input" },
    { q: "ما الفرق بين المعفاة والصفرية؟", expect: "zero" },
    { q: "هل هناك غرامة على التأخير في الإقرار؟", expect: "penalty" },
    { q: "كيف أدقق قيد فاتورة المبيعات؟", expect: "journal" },
    { q: "أي قالب يناسب مكتب محاسبة؟", expect: "templates" },
    { q: "كيف أشغل النظام على جهازي؟", expect: "setup" },
    { q: "أريد التحدث مع موظف دعم", expect: "support" },

    // ===== العربية: لهجة خليجية / صيغ حرة =====
    { q: "وش نسبة الضريبة بالإمارات؟", expect: "rates", country: "AE" },
    { q: "كم ضريبة القيمة المضافة بالرياض؟", expect: "rates", country: "SA" },
    { q: "ايش النسبة في البحرين؟", expect: "rates", country: "BH" },
    { q: "هل لازم أسجل في الضريبة؟", expect: "registration" },
    { q: "لازم نسجل ولا لا؟", expect: "registration" },
    { q: "متى ينزل الإقرار؟", expect: "deadline", loose: true },
    { q: "وش حقول الفاتورة يا طيب؟", expect: "fields" },
    { q: "أقدر أخصم ضريبة المدخلات؟", expect: "input" },
    { q: "ايش الفرق بين الصفرية والمعفاة؟", expect: "zero" },
    { q: "في غرامة إذا تأخرت؟", expect: "penalty" },
    { q: "كيف أسوي قيد الفاتورة؟", expect: "journal" },
    { q: "ابغى قالب للمحاسبة", expect: "templates" },
    { q: "كيف اثبته عندي؟", expect: "setup", loose: true },
    { q: "ابغى اكلم احد من الدعم", expect: "support" },

    // ===== الإنجليزية =====
    { q: "What is the VAT rate in Saudi Arabia?", expect: "rates", country: "SA" },
    { q: "what's the VAT in Dubai?", expect: "rates", country: "AE" },
    { q: "Do I need to register for VAT?", expect: "registration" },
    { q: "When is the VAT return due?", expect: "deadline" },
    { q: "Which fields must a tax invoice contain?", expect: "fields" },
    { q: "Can I deduct input VAT on purchases?", expect: "input" },
    { q: "Difference between zero rated and exempt?", expect: "zero" },
    { q: "Any penalty for late filing?", expect: "penalty" },
    { q: "How do I audit a sales invoice entry?", expect: "journal" },
    { q: "Which template fits an accounting office?", expect: "templates" },
    { q: "How do I run this project locally?", expect: "setup" },
    { q: "I need to talk to a human", expect: "support" },

    // ===== حالات يجب ألا تُطابق =====
    { q: "مرحبا كيف الحال", expect: null, loose: true },
    { q: "blah blah something random", expect: null, loose: true },
  ];

  function runFaqTests(options) {
    const core = (options && options.core) || root.AssistantCore;
    if (!core) throw new Error("AssistantCore is not loaded");
    const rows = CASES.map((testCase) => {
      const result = core.matchIntent(testCase.q);
      const intentOk = result.id === testCase.expect;
      const countryOk = !testCase.country || result.country === testCase.country;
      const pass = intentOk && countryOk;
      return {
        q: testCase.q,
        expected: testCase.expect,
        actual: result.id,
        expectedCountry: testCase.country || "—",
        actualCountry: result.country || "—",
        score: result.score,
        pass,
      };
    });
    const passed = rows.filter((row) => row.pass).length;
    return { total: rows.length, passed, failed: rows.length - passed, rows };
  }

  function renderFaqTests(target) {
    const host = target || document.getElementById("testRows");
    if (!host) return null;
    const report = runFaqTests();
    host.innerHTML = report.rows.map((row) => `
      <tr class="${row.pass ? "pass" : "fail"}">
        <td>${row.pass ? "✓" : "✕"}</td>
        <td dir="auto">${row.q}</td>
        <td>${row.expected || "—"}</td>
        <td>${row.actual || "—"}</td>
        <td>${row.expectedCountry}</td>
        <td>${row.actualCountry}</td>
        <td>${row.score}</td>
      </tr>`).join("");
    const summary = document.getElementById("testSummary");
    if (summary) {
      summary.textContent = `${report.passed} / ${report.total} ناجحة · ${report.failed} فاشلة`;
      summary.className = report.failed ? "summary bad" : "summary ok";
    }
    return report;
  }

  root.FAQ_TESTS = CASES;
  root.runFaqTests = runFaqTests;
  root.renderFaqTests = renderFaqTests;

  if (typeof module !== "undefined" && module.exports) {
    module.exports = { CASES, runFaqTests };
    if (typeof require !== "undefined" && require.main === module) {
      const core = require("./core.js");
      const report = runFaqTests({ core });
      report.rows.forEach((row) => {
        console.log(`${row.pass ? "PASS" : "FAIL"}  ${row.q}  →  ${row.actual || "null"}` +
          ` (expected ${row.expected || "null"}, country ${row.actualCountry}/${row.expectedCountry}, score ${row.score})`);
      });
      console.log(`\n${report.passed}/${report.total} passed, ${report.failed} failed`);
      process.exitCode = report.failed ? 1 : 0;
    }
  } else if (typeof document !== "undefined" && document.getElementById("testRows")) {
    document.addEventListener("DOMContentLoaded", () => renderFaqTests());
  }
})(typeof window !== "undefined" ? window : globalThis);
