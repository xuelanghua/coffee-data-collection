import assert from "node:assert/strict";
import test from "node:test";

import { CoffeeApiClient } from "../src/services/api.js";
import { FieldCollectionFlow } from "../src/services/collection-flow.js";

function createMockFetch() {
  const calls = [];
  const fetch = async (url, options = {}) => {
    calls.push({
      url,
      method: options.method || "GET",
      body: options.body ? JSON.parse(options.body) : null,
      headers: options.headers || {},
    });
    if (url.endsWith("/api/coffee/auth/mobile-login/")) {
      return jsonResponse({ code: 2000, data: { access: "token-1" }, msg: "ok" });
    }
    if (url.endsWith("/api/coffee/app/events/EV202606240401/ocr/")) {
      return jsonResponse({
        code: 2000,
        data: {
          ocr_result_id: "OCR202606240401",
          status: "success",
          structured_json: {
            air_temperature: { value: "23.8", confidence: 0.91 },
            soil_ph: { value: "6.4", confidence: 0.88 },
          },
        },
        msg: "ok",
      });
    }
    return jsonResponse({
      code: 2000,
      data: {
        ok: true,
        event_id: "EV202606240401",
        plot_id: "PL202606240401",
        point_id: "PT202606240401",
        photo_id: "PH202606240401",
        status: "submitted",
      },
      msg: "ok",
    });
  };
  return { fetch, calls };
}

function jsonResponse(payload) {
  return {
    ok: true,
    status: 200,
    async json() {
      return payload;
    },
  };
}

test("client posts the App-first collection loop to backend contract endpoints", async () => {
  const { fetch, calls } = createMockFetch();
  const client = new CoffeeApiClient({ baseUrl: "https://example.test", fetch });
  await client.loginByPassword({ phone: "13800000000", password: "secret" });

  await client.createPlot({ task_id: "TASK1", plot_id: "PL202606240401", name: "现场地块", boundary_geojson: { type: "Polygon", coordinates: [] }, area_mu: "12.34", idempotency_key: "plot-key" });
  await client.createPoint({ task_id: "TASK1", plot_id: "PL202606240401", point_id: "PT202606240401", longitude: "100.1", latitude: "22.1", idempotency_key: "point-key" });
  await client.createEvent({ task_id: "TASK1", plot_id: "PL202606240401", point_id: "PT202606240401", event_id: "EV202606240401", idempotency_key: "event-key", manifest_hash: "draft" });
  await client.initPhoto({ event_id: "EV202606240401", photo_id: "PH202606240401", category: "device_reading", sha256: "abc123", metadata: {} });
  await client.completePhoto("PH202606240401", { original_file: "original.jpg", watermarked_file: "watermarked.jpg", sha256: "abc123", precheck_status: "precheck_pass" });
  await client.runOcr("EV202606240401", { photo_id: "PH202606240401", provider: "manual", structured_json: {} });
  await client.saveOcrCorrection("OCR202606240401", { field_name: "air_temperature", raw_value: "23.8", corrected_value: "23.6", reason: "人工核对" });
  await client.submitEvent("EV202606240401", { idempotency_key: "event-key", manifest: { manifest_hash: "submitted" }, field_values: [], measurements: [] });

  assert.deepEqual(
    calls.map((call) => `${call.method} ${call.url.replace("https://example.test", "")}`),
    [
      "POST /api/coffee/auth/mobile-login/",
      "POST /api/coffee/app/plots/",
      "POST /api/coffee/app/points/",
      "POST /api/coffee/app/events/",
      "POST /api/coffee/app/photos/init/",
      "POST /api/coffee/app/photos/PH202606240401/complete/",
      "POST /api/coffee/app/events/EV202606240401/ocr/",
      "POST /api/coffee/app/ocr-results/OCR202606240401/corrections/",
      "POST /api/coffee/app/events/EV202606240401/submit/",
    ],
  );
  assert.equal(calls[1].headers.Authorization, "Bearer token-1");
});

test("field collection flow fills OCR values into editable device fields", async () => {
  const { fetch } = createMockFetch();
  const client = new CoffeeApiClient({ baseUrl: "https://example.test", fetch });
  const flow = new FieldCollectionFlow({ client, now: () => "2026-06-24T10:30:00+08:00" });

  await flow.startEvent({
    taskId: "TASK1",
    plotId: "PL202606240401",
    pointId: "PT202606240401",
    eventId: "EV202606240401",
    idempotencyKey: "event-key",
  });
  await flow.applyOcrResult({ eventId: "EV202606240401", photoId: "PH202606240401", provider: "manual" });
  flow.correctDeviceField("air_temperature", "23.6", "人工核对");

  const submitPayload = flow.buildSubmitPayload();
  assert.equal(flow.deviceFields.air_temperature.value, "23.6");
  assert.equal(flow.deviceFields.air_temperature.correctedFrom, "23.8");
  assert.equal(submitPayload.measurements[0].soil_ph, "6.4");
  assert.equal(submitPayload.field_values.find((item) => item.field_code === "air_temperature").corrected_from, "23.8");
});

test("field collection flow preserves abnormal device measurement and appends retake payload", async () => {
  const { fetch } = createMockFetch();
  const client = new CoffeeApiClient({ baseUrl: "https://example.test", fetch });
  const flow = new FieldCollectionFlow({ client, now: () => "2026-06-24T10:30:00+08:00" });

  await flow.startEvent({
    taskId: "TASK1",
    plotId: "PL202606240401",
    pointId: "PT202606240401",
    eventId: "EV202606240401",
    idempotencyKey: "event-key",
  });
  await flow.applyOcrResult({ eventId: "EV202606240401", photoId: "PH202606240401", provider: "manual" });
  flow.recordMeasurementRetake({
    reason: "土壤 PH 异常，现场复测",
    values: {
      soil_ph: "6.7",
      air_temperature: "23.7",
    },
  });

  const measurements = flow.buildSubmitPayload().measurements;

  assert.equal(measurements.length, 2);
  assert.equal(measurements[0].client_measurement_id, "MEASURE-001");
  assert.equal(measurements[0].is_abnormal, true);
  assert.equal(measurements[0].remark, "土壤 PH 异常，现场复测");
  assert.equal(measurements[1].client_measurement_id, "MEASURE-001-RETAKE-001");
  assert.equal(measurements[1].retake_of_client_id, "MEASURE-001");
  assert.equal(measurements[1].is_abnormal, false);
  assert.equal(measurements[1].soil_ph, "6.7");
  assert.equal(measurements[1].air_temperature, "23.7");
});
