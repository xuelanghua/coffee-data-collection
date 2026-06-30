import assert from "node:assert/strict";
import test from "node:test";

import { CameraCaptureAdapter } from "../src/services/camera-capture.js";
import { PlotDrawingSession } from "../src/services/plot-drawing.js";
import { UploadQueue } from "../src/services/upload-queue.js";

test("plot drawing session appends, undoes and closes a field boundary payload", () => {
  const session = new PlotDrawingSession();
  session.addPoint({ longitude: 100, latitude: 22 });
  session.addPoint({ longitude: 100.001, latitude: 22 });
  session.addPoint({ longitude: 100.002, latitude: 22 });
  session.undoPoint();
  session.addPoint({ longitude: 100.001, latitude: 22.001 });
  session.addPoint({ longitude: 100, latitude: 22.001 });

  const payload = session.buildCreatePlotPayload({
    taskId: "TASK1",
    plotId: "PL202606240501",
    name: "现场地块",
    idempotencyKey: "plot-key",
  });

  assert.equal(payload.task_id, "TASK1");
  assert.equal(payload.plot_id, "PL202606240501");
  assert.equal(payload.boundary_geojson.type, "Polygon");
  assert.equal(payload.boundary_geojson.coordinates[0].length, 5);
  assert.ok(payload.area_mu > 10);
  assert.equal(payload.source_type, "app_drawn");
});

test("camera capture adapter creates a photo draft with watermark metadata", async () => {
  const adapter = new CameraCaptureAdapter({
    chooseImage: async () => ({
      tempFilePath: "local://device.jpg",
      size: 2048,
      width: 1280,
      height: 720,
    }),
    now: () => "2026-06-24T10:30:00+08:00",
  });

  const draft = await adapter.capturePhotoDraft({
    taskId: "TASK1",
    plotId: "PL202606240501",
    pointId: "PT202606240501",
    eventId: "EV202606240501",
    photoId: "PH202606240501",
    category: "device_reading",
    collectorName: "采集员A",
    location: { longitude: 100.1, latitude: 22.1, accuracy: 5, coordinateSystem: "gcj02" },
  });

  assert.equal(draft.photoId, "PH202606240501");
  assert.equal(draft.localPath, "local://device.jpg");
  assert.equal(draft.metadata.width, 1280);
  assert.equal(draft.metadata.watermark.photo_id, "PH202606240501");
  assert.match(draft.watermark.lines.join("\n"), /PL202606240501/);
});

test("upload queue records failed items and retries them later", async () => {
  let shouldFail = true;
  const client = {
    async initPhoto() {
      if (shouldFail) {
        throw new Error("network offline");
      }
      return {};
    },
    async completePhoto() {
      return {};
    },
    async submitEvent() {
      return {};
    },
  };
  const queue = new UploadQueue({ client });
  queue.enqueueCollection({
    eventId: "EV202606240501",
    idempotencyKey: "event-key",
    photos: [{ photoId: "PH202606240501", category: "plot_env", sha256: "abc" }],
    submitPayload: { idempotency_key: "event-key" },
  });

  const failed = await queue.drain({ stopOnError: false });
  shouldFail = false;
  queue.retryFailed();
  const retried = await queue.drain();

  assert.equal(failed.failed, 1);
  assert.equal(queue.failedCount, 0);
  assert.equal(retried.completed, 3);
});
