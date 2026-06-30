import assert from "node:assert/strict";
import test from "node:test";

import { CoffeeApiClient } from "../src/services/api.js";
import { UploadQueue } from "../src/services/upload-queue.js";

test("api client uploads a photo chunk to the backend chunk endpoint", async () => {
  const calls = [];
  const client = new CoffeeApiClient({
    baseUrl: "https://example.test",
    fetch: async (url, options = {}) => {
      calls.push({ url, method: options.method, body: JSON.parse(options.body) });
      return {
        ok: true,
        async json() {
          return { code: 2000, data: { uploaded_chunks: 1 }, msg: "ok" };
        },
      };
    },
  });

  const result = await client.uploadPhotoChunk("PH202606250401", 0, {
    chunk_hash: "chunk-0-sha",
    chunk_size: 1024,
  });

  assert.equal(result.uploaded_chunks, 1);
  assert.equal(calls[0].method, "PUT");
  assert.match(calls[0].url, /\/api\/coffee\/app\/photos\/PH202606250401\/chunks\/0\/$/);
});

test("upload queue uploads chunks before complete and sends chunk manifest", async () => {
  const calls = [];
  const client = {
    async initPhoto(payload) {
      calls.push(["initPhoto", payload.photo_id]);
      return { photo_id: "PH202606250401", upload_session_id: "UP1" };
    },
    async uploadPhotoChunk(photoId, index, payload) {
      calls.push(["uploadPhotoChunk", photoId, index, payload.chunk_hash]);
      return { uploaded_chunks: index + 1 };
    },
    async completePhoto(photoId, payload) {
      calls.push(["completePhoto", photoId, payload.chunk_count, payload.chunk_hashes.join(",")]);
      return { photo_id: photoId, status: "uploaded" };
    },
    async submitEvent() {
      calls.push(["submitEvent"]);
      return {};
    },
  };
  const queue = new UploadQueue({ client });

  queue.enqueueCollection({
    eventId: "EV202606250401",
    idempotencyKey: "event-key",
    photos: [
      {
        category: "plot_env",
        sha256: "whole-file-sha",
        chunks: [
          { chunkHash: "chunk-0-sha", chunkSize: 1024 },
          { chunkHash: "chunk-1-sha", chunkSize: 2048 },
        ],
        originalFile: "local://plot.jpg",
      },
    ],
    submitPayload: { idempotency_key: "event-key", manifest: { event_id: "EV202606250401", photos: [] } },
  });

  await queue.drain();

  assert.deepEqual(calls.map((call) => call[0]), [
    "initPhoto",
    "uploadPhotoChunk",
    "uploadPhotoChunk",
    "completePhoto",
    "submitEvent",
  ]);
  assert.deepEqual(calls[3], ["completePhoto", "PH202606250401", 2, "chunk-0-sha,chunk-1-sha"]);
});
