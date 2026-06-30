import assert from "node:assert/strict";
import test from "node:test";

import { FieldCollectionFlow } from "../src/services/collection-flow.js";
import { InMemoryDraftStorage, LocalDraftStore } from "../src/services/draft-store.js";
import { UploadQueue } from "../src/services/upload-queue.js";

test("field collection flow stores server-confirmed plot, point and event ids into draft and manifest", async () => {
  const storage = new InMemoryDraftStorage();
  const draftStore = new LocalDraftStore({ storage, now: () => "2026-06-25T09:00:00+08:00" });
  const client = {
    async createPlot(payload) {
      assert.equal(payload.plot_id, undefined);
      return { ...payload, plot_id: "PL202606250001" };
    },
    async createPoint(payload) {
      assert.equal(payload.plot_id, "PL202606250001");
      assert.equal(payload.point_id, undefined);
      return { ...payload, point_id: "PT202606250001" };
    },
    async createEvent(payload) {
      assert.equal(payload.plot_id, "PL202606250001");
      assert.equal(payload.point_id, "PT202606250001");
      assert.equal(payload.event_id, undefined);
      return { ...payload, event_id: "EV202606250001" };
    },
  };
  const flow = new FieldCollectionFlow({ client, draftStore });

  const result = await flow.createServerConfirmedCollection({
    taskId: "TASK1",
    plot: {
      name: "现场地块",
      boundaryGeojson: { type: "Polygon", coordinates: [[[100, 22], [100.001, 22], [100.001, 22.001], [100, 22.001], [100, 22]]] },
      areaMu: "12.34",
    },
    point: { longitude: "100.0005", latitude: "22.0005" },
    event: { idempotencyKey: "event-key", manifestHash: "draft-hash" },
  });

  const draft = await draftStore.getDraft("EV202606250001");
  const submitPayload = flow.buildSubmitPayload();

  assert.equal(result.plotId, "PL202606250001");
  assert.equal(result.pointId, "PT202606250001");
  assert.equal(result.eventId, "EV202606250001");
  assert.equal(draft.plotId, "PL202606250001");
  assert.equal(draft.pointId, "PT202606250001");
  assert.equal(submitPayload.manifest.plot_id, "PL202606250001");
  assert.equal(submitPayload.manifest.event_id, "EV202606250001");
});

test("upload queue replaces local photo ids with server-confirmed ids before OCR and submit manifest", async () => {
  const calls = [];
  const client = {
    async initPhoto(payload) {
      calls.push(["initPhoto", payload.photo_id]);
      assert.equal(payload.photo_id, undefined);
      return { photo_id: "PH202606250001" };
    },
    async completePhoto(photoId) {
      calls.push(["completePhoto", photoId]);
      assert.equal(photoId, "PH202606250001");
      return { photo_id: photoId, status: "uploaded" };
    },
    async runOcr(eventId, payload) {
      calls.push(["runOcr", eventId, payload.photo_id]);
      assert.equal(payload.photo_id, "PH202606250001");
      return { ocr_result_id: "OCR1", structured_json: {} };
    },
    async submitEvent(eventId, payload) {
      calls.push(["submitEvent", eventId, payload.manifest.photos[0].photo_id]);
      assert.equal(payload.manifest.photos[0].photo_id, "PH202606250001");
      return { event_id: eventId, status: "submitted" };
    },
  };
  const queue = new UploadQueue({ client });

  queue.enqueueCollection({
    eventId: "EV202606250001",
    idempotencyKey: "event-key",
    photos: [
      {
        localPhotoId: "LOCAL-PH-1",
        category: "device_reading",
        sha256: "abc123",
        metadata: {},
        originalFile: "local://device.jpg",
        watermarkedFile: "local://device-watermarked.jpg",
      },
    ],
    submitPayload: {
      idempotency_key: "event-key",
      manifest: { event_id: "EV202606250001", photos: [{ local_photo_id: "LOCAL-PH-1" }] },
      field_values: [],
      measurements: [],
    },
  });

  await queue.drain();

  assert.deepEqual(calls.map((call) => call[0]), ["initPhoto", "completePhoto", "runOcr", "submitEvent"]);
});
