import assert from "node:assert/strict";
import test from "node:test";

import { calculatePolygonAreaMu, createPlotGeoJson } from "../src/services/geometry.js";
import { InMemoryDraftStorage, LocalDraftStore } from "../src/services/draft-store.js";
import { UploadQueue } from "../src/services/upload-queue.js";
import { buildPhotoWatermark } from "../src/services/watermark.js";

test("field polygon produces GeoJSON and a positive mu area for App-created plots", () => {
  const points = [
    { longitude: 100.0, latitude: 22.0 },
    { longitude: 100.001, latitude: 22.0 },
    { longitude: 100.001, latitude: 22.001 },
    { longitude: 100.0, latitude: 22.001 },
  ];

  const geojson = createPlotGeoJson(points);
  const areaMu = calculatePolygonAreaMu(points);

  assert.equal(geojson.type, "Polygon");
  assert.deepEqual(geojson.coordinates[0][0], [100.0, 22.0]);
  assert.deepEqual(geojson.coordinates[0].at(-1), [100.0, 22.0]);
  assert.ok(areaMu > 10);
  assert.ok(areaMu < 20);
});

test("watermark payload carries four-level identifiers and location metadata", () => {
  const watermark = buildPhotoWatermark({
    taskId: "TASK1",
    plotId: "PL202606240401",
    pointId: "PT202606240401",
    eventId: "EV202606240401",
    photoId: "PH202606240401",
    capturedAt: "2026-06-24T10:30:00+08:00",
    collectorName: "采集员A",
    location: { longitude: 100.1, latitude: 22.1, accuracy: 6, coordinateSystem: "gcj02" },
  });

  assert.equal(watermark.metadata.plot_id, "PL202606240401");
  assert.equal(watermark.metadata.photo_id, "PH202606240401");
  assert.match(watermark.lines.join("\n"), /EV202606240401/);
  assert.match(watermark.lines.join("\n"), /100.1,22.1/);
});

test("local draft store saves and restores offline collection state", async () => {
  const storage = new InMemoryDraftStorage();
  const store = new LocalDraftStore({ storage });

  await store.saveDraft({
    eventId: "EV202606240401",
    plotId: "PL202606240401",
    status: "pending_upload",
    photos: [{ photoId: "PH202606240401", localPath: "/tmp/device.jpg" }],
  });

  const drafts = await store.listDrafts();
  const draft = await store.getDraft("EV202606240401");

  assert.equal(drafts.length, 1);
  assert.equal(drafts[0].eventId, "EV202606240401");
  assert.equal(draft.photos[0].photoId, "PH202606240401");
});

test("upload queue advances photo, OCR and final submit steps in contract order", async () => {
  const calls = [];
  const client = {
    async initPhoto(payload) {
      calls.push(["initPhoto", payload.photo_id]);
      return { photo_id: payload.photo_id };
    },
    async completePhoto(photoId, payload) {
      calls.push(["completePhoto", photoId, payload.sha256]);
      return { photo_id: photoId, status: "uploaded" };
    },
    async runOcr(eventId, payload) {
      calls.push(["runOcr", eventId, payload.photo_id]);
      return { ocr_result_id: "OCR1", structured_json: {} };
    },
    async submitEvent(eventId, payload) {
      calls.push(["submitEvent", eventId, payload.idempotency_key]);
      return { event_id: eventId, status: "submitted" };
    },
  };
  const queue = new UploadQueue({ client });

  queue.enqueueCollection({
    eventId: "EV202606240401",
    idempotencyKey: "event-key",
    photos: [
      {
        photoId: "PH202606240401",
        category: "device_reading",
        sha256: "abc123",
        metadata: { width: 1280, height: 720 },
        originalFile: "local://device.jpg",
        watermarkedFile: "local://device-watermarked.jpg",
      },
    ],
    submitPayload: {
      idempotency_key: "event-key",
      manifest: { event_id: "EV202606240401" },
      field_values: [],
      measurements: [],
    },
  });

  const result = await queue.drain();

  assert.equal(result.completed, 4);
  assert.deepEqual(calls.map((call) => call[0]), ["initPhoto", "completePhoto", "runOcr", "submitEvent"]);
  assert.equal(queue.pendingCount, 0);
});
