/* الأوامر الصوتية للمساعد الذكي — Web Speech API (بلا مكتبات خارجية) */
(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const btn = $("voiceBtn");
  const line = $("voiceLine");
  if (!btn || !line) return;

  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const appState = typeof state !== "undefined" ? state : null;
  const appDict = typeof I18N !== "undefined" ? I18N : null;
  let lang = appState && appState.lang === "en" ? "en" : "ar";
  let recognizing = false;
  let recognition = null;
  let pendingVoice = false;

  function label(key, vars) {
    const dict = (appDict && appDict[lang]) || {};
    const fallback = (appDict && appDict.ar) || {};
    let text = dict[key] != null ? dict[key] : fallback[key] != null ? fallback[key] : key;
    if (vars) {
      Object.keys(vars).forEach((name) => {
        text = text.split("{" + name + "}").join(vars[name]);
      });
    }
    return text;
  }

  function say(text) {
    if (!window.speechSynthesis || !text) return;
    try {
      window.speechSynthesis.cancel();
      const clean = String(text).replace(/\s+/g, " ").trim().slice(0, 500);
      if (!clean) return;
      const utterance = new SpeechSynthesisUtterance(clean);
      utterance.lang = lang === "en" ? "en-US" : "ar-SA";
      utterance.rate = 1;
      window.speechSynthesis.speak(utterance);
    } catch (err) { /* بعض المتصفحات تمنع النطق */ }
  }

  function setLine(text, kind) {
    line.hidden = !text;
    line.textContent = text || "";
    line.className = "voice-line" + (kind ? " " + kind : "");
  }

  function setButton(active) {
    btn.classList.toggle("listening", !!active);
    btn.setAttribute("aria-pressed", active ? "true" : "false");
    btn.title = active ? label("voice.stop") : label("voice.start");
    btn.setAttribute("aria-label", btn.title);
  }

  if (!Recognition) {
    btn.disabled = true;
    btn.classList.add("disabled");
    setButton(false);
    setLine(label("voice.unsupported"), "warn");
  } else {
    recognition = new Recognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    recognition.lang = lang === "en" ? "en-US" : "ar-SA";

    recognition.addEventListener("result", (event) => {
      let interim = "";
      let final = "";
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) final += transcript;
        else interim += transcript;
      }
      if (interim) setLine(label("voice.listening") + " — " + interim, "live");
      if (final.trim()) {
        const question = final.trim();
        setLine(label("voice.heard", { q: question }), "ok");
        pendingVoice = true;
        ask(question);
      }
    });

    recognition.addEventListener("error", (event) => {
      recognizing = false;
      setButton(false);
      const code = (event && event.error) || "error";
      const denied = code === "not-allowed" || code === "service-not-allowed";
      setLine(denied ? label("voice.denied") : label("voice.error", { error: code }), "warn");
      pendingVoice = false;
    });

    recognition.addEventListener("end", () => {
      recognizing = false;
      setButton(false);
    });

    btn.addEventListener("click", () => {
      if (recognizing) {
        recognition.stop();
        setLine(label("voice.off"), "");
        return;
      }
      try {
        if (window.speechSynthesis) window.speechSynthesis.cancel();
        recognition.lang = lang === "en" ? "en-US" : "ar-SA";
        recognition.start();
        recognizing = true;
        setButton(true);
        setLine(label("voice.listening"), "live");
      } catch (err) {
        setLine(label("voice.error", { error: err.message }), "warn");
      }
    });
  }

  document.addEventListener("assistant:answer", (event) => {
    if (!pendingVoice) return;
    pendingVoice = false;
    say((event.detail && event.detail.text) || "");
  });

  window.VoiceAssistant = {
    setLang(next) {
      lang = next === "en" ? "en" : "ar";
      if (recognition) recognition.lang = lang === "en" ? "en-US" : "ar-SA";
      if (!recognition) setLine(label("voice.unsupported"), "warn");
      else if (!recognizing && line.classList.contains("warn")) setLine("", "");
      setButton(recognizing);
    },
    stop() {
      if (recognition && recognizing) recognition.stop();
    },
  };

  setButton(false);
})();
