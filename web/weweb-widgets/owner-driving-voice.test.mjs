import assert from "node:assert/strict";
import { test } from "node:test";
import { dictateOwnerDraft, playDrivingBrief, stopDrivingBrief } from "./owner-driving-voice.mjs";

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

test("parked dictation requires explicit consent and a preinstalled local recognizer", async () => {
  const events = [];
  let available = "downloadable";
  class SpeechRecognition {
    processLocally = false;
    static async available(options) {
      events.push(options);
      return available;
    }
    start() {
      events.push({ startedLocally: this.processLocally, continuous: this.continuous });
      const result = Object.assign([{ transcript: "  Draft text only.  " }], { isFinal: true });
      this.onresult({ results: [result] });
    }
  }
  const browser = { SpeechRecognition };
  const options = { mode: "parked", consent: true, browser };
  assert.equal((await dictateOwnerDraft({ ...options, mode: "driving" })).status, "parked_only");
  assert.equal((await dictateOwnerDraft({ ...options, consent: false })).status, "consent_required");
  assert.deepEqual(events, []);
  assert.equal((await dictateOwnerDraft(options)).status, "text_only");
  assert.deepEqual(events, [{ langs: ["en-CA"], processLocally: true }]);
  available = "available";
  assert.deepEqual(await dictateOwnerDraft(options), { status: "draft_ready", text: "Draft text only." });
  assert.deepEqual(events.at(-1), { startedLocally: true, continuous: false });
});

test("logout or navigation cancels pending dictation without returning a transcript", async () => {
  let capture;
  class SpeechRecognition {
    processLocally = false;
    static async available() { return "available"; }
    start() { capture = this; }
    abort() { this.aborted = true; }
  }
  const controller = new AbortController();
  const pending = dictateOwnerDraft({
    mode: "parked", consent: true, browser: { SpeechRecognition }, signal: controller.signal,
  });
  await Promise.resolve();
  await Promise.resolve();
  assert.ok(capture);
  controller.abort();
  assert.equal((await pending).status, "cancelled");
  assert.ok(capture.aborted);
  assert.equal(capture.onresult, null);
});
