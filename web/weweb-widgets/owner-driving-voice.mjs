// Explicit playback of the existing authenticated driving briefing.
export function playDrivingBrief(brief, { consent = false, browser = globalThis } = {}) {
  if (!consent) return { status: "consent_required" };
  const text = typeof brief?.reply === "string" ? brief.reply.trim() : "";
  if (brief?.mode !== "driving" || brief.execution_authorized !== false || !text || text.length > 240) {
    return { status: "invalid_briefing" };
  }
  const synth = browser.speechSynthesis;
  const Utterance = browser.SpeechSynthesisUtterance;
  if (!synth || typeof Utterance !== "function") return { status: "text_only" };
  try {
    const voice = synth.getVoices().find((entry) => entry.localService === true && /^en(?:-|$)/i.test(entry.lang));
    if (!voice) return { status: "text_only" };
    const utterance = new Utterance(text);
    utterance.voice = voice;
    utterance.lang = voice.lang;
    synth.cancel();
    synth.speak(utterance);
    return { status: "playback_requested" };
  } catch {
    return { status: "text_only" };
  }
}

export function stopDrivingBrief(browser = globalThis) {
  browser.speechSynthesis?.cancel();
}

// Parked dictation returns editable text for a deliberate subsequent submission.
export async function dictateOwnerDraft({
  mode, consent = false, browser = globalThis, signal, lang = "en-CA",
} = {}) {
  if (mode !== "parked") return { status: "parked_only" };
  if (!consent) return { status: "consent_required" };
  if (signal?.aborted) return { status: "cancelled" };
  const Recognition = browser.SpeechRecognition;
  if (typeof Recognition !== "function" || typeof Recognition.available !== "function") {
    return { status: "text_only" };
  }
  try {
    const recognition = new Recognition();
    if (!("processLocally" in recognition)) return { status: "text_only" };
    recognition.processLocally = true;
    if (recognition.processLocally !== true) return { status: "text_only" };
    const availability = await Recognition.available({ langs: [lang], processLocally: true });
    if (signal?.aborted) return { status: "cancelled" };
    if (availability !== "available") return { status: "text_only" };
    recognition.lang = lang;
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    return await new Promise((resolve) => {
      let finished = false;
      const finish = (result) => {
        if (finished) return;
        finished = true;
        clearTimeout(timer);
        signal?.removeEventListener("abort", cancel);
        recognition.onresult = recognition.onerror = recognition.onend = null;
        resolve(result);
      };
      const cancel = () => {
        finish({ status: "cancelled" });
        try { recognition.abort(); } catch {}
      };
      const timer = setTimeout(() => {
        finish({ status: "text_only" });
        try { recognition.abort(); } catch {}
      }, 15000);
      if (signal?.aborted) {
        cancel();
        return;
      }
      signal?.addEventListener("abort", cancel, { once: true });
      recognition.onresult = ({ results }) => {
        const text = results?.[0]?.isFinal && results[0][0]?.transcript;
        finish(typeof text === "string" && text.trim()
          ? { status: "draft_ready", text: text.trim().slice(0, 4000) }
          : { status: "text_only" });
      };
      recognition.onerror = recognition.onend = () => finish({ status: "text_only" });
      try { recognition.start(); } catch { finish({ status: "text_only" }); }
    });
  } catch {
    return { status: "text_only" };
  }
}
