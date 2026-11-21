import assert from "node:assert/strict";
import { test } from "node:test";
import { playDrivingBrief, stopDrivingBrief } from "./owner-driving-voice.mjs";

test("owner playback requires consent, a read-only driving brief and a device-local voice", () => {
  const events = [];
  const local = { localService: true, lang: "en-CA" };
  const remote = { localService: false, lang: "en-CA" };
  const synth = {
    getVoices: () => [remote],
    cancel: () => events.push("cancel"),
    speak: (utterance) => events.push(utterance),
  };
  const browser = {
    speechSynthesis: synth,
    SpeechSynthesisUtterance: class {
      constructor(text) { this.text = text; }
    },
  };
  const brief = { mode: "driving", reply: "There are items to review when parked.", execution_authorized: false };
  assert.equal(playDrivingBrief(brief, { browser }).status, "consent_required");
  assert.equal(playDrivingBrief({ ...brief, mode: "standard" }, { browser, consent: true }).status, "invalid_briefing");
  assert.equal(playDrivingBrief({ ...brief, execution_authorized: true }, { browser, consent: true }).status, "invalid_briefing");
  assert.equal(playDrivingBrief(brief, { browser, consent: true }).status, "text_only");
  assert.deepEqual(events, []);
  synth.getVoices = () => [remote, local];
  assert.equal(playDrivingBrief(brief, { browser, consent: true }).status, "playback_requested");
  assert.equal(events[0], "cancel");
  assert.equal(events[1].voice, local);
  assert.equal(events[1].text, brief.reply);
  stopDrivingBrief(browser);
  assert.equal(events.at(-1), "cancel");
});
