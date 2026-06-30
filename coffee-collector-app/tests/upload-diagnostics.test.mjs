import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { UploadQueue } from "../src/services/upload-queue.js";

test("upload queue pauses drain while offline and exposes weak-network diagnostics", async () => {
  const calls = [];
  const queue = new UploadQueue({
    client: {
      async initPhoto(payload) {
        calls.push(["initPhoto", payload.photo_id]);
        return { photo_id: "PH202606250501", upload_session_id: "UP-501" };
      },
      async uploadPhotoChunk(photoId, index) {
        calls.push(["uploadPhotoChunk", photoId, index]);
        return { uploaded_chunks: index + 1 };
      },
      async completePhoto(photoId) {
        calls.push(["completePhoto", photoId]);
        return {};
      },
      async submitEvent(eventId) {
        calls.push(["submitEvent", eventId]);
        return {};
      },
    },
  });

  queue.enqueueCollection({
    eventId: "EV202606250501",
    idempotencyKey: "event-key",
    photos: [
      {
        photoId: "PH-LOCAL-501",
        localPhotoId: "LOCAL-PH-501",
        category: "device_reading",
        sha256: "whole-sha",
        chunks: [
          { chunkHash: "chunk-0", chunkSize: 1024 },
          { chunkHash: "chunk-1", chunkSize: 2048 },
        ],
      },
    ],
    submitPayload: {
      idempotency_key: "event-key",
      manifest: { photos: [{ local_photo_id: "LOCAL-PH-501" }] },
    },
  });

  queue.setNetworkState("offline");
  const offline = await queue.drain();
  assert.equal(offline.completed, 0);
  assert.equal(offline.paused, true);
  assert.equal(calls.length, 0);

  queue.setNetworkState("online");
  const online = await queue.drain({ maxSteps: 1 });
  const diagnostics = queue.diagnostics();

  assert.equal(online.completed, 2);
  assert.equal(diagnostics.networkState, "online");
  assert.equal(diagnostics.pendingCount, 2);
  assert.equal(diagnostics.failedCount, 0);
  assert.equal(diagnostics.completedCount, 1);
  assert.equal(diagnostics.photos[0].photoId, "PH202606250501");
  assert.equal(diagnostics.photos[0].uploadSessionId, "UP-501");
  assert.equal(diagnostics.photos[0].uploadedChunks, 2);
  assert.equal(diagnostics.photos[0].totalChunks, 2);
});

test("upload queue page renders weak-network state and operator controls", () => {
  const source = readFileSync(new URL("../src/pages/upload-queue/index.vue", import.meta.url), "utf8");

  assert.match(source, /networkState/);
  assert.match(source, /paused/);
  assert.match(source, /pauseUpload/);
  assert.match(source, /resumeUpload/);
  assert.match(source, /diagnostics/);
});
