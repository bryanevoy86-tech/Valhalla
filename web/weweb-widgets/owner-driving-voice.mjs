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
