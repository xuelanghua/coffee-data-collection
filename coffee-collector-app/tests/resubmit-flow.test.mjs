import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { CoffeeApiClient } from "../src/services/api.js";

test("api client posts returned events to the resubmit endpoint", async () => {
  const calls = [];
  const client = new CoffeeApiClient({
    baseUrl: "https://example.test",
    fetch: async (url, options = {}) => {
      calls.push({ url, method: options.method, body: JSON.parse(options.body) });
      return {
        ok: true,
        async json() {
          return { code: 2000, data: { event_id: "EV202606250701", status: "submitted", version: 2 } };
        },
      };
    },
  });

  const result = await client.resubmitEvent("EV202606250701", {
    idempotency_key: "resubmit-key",
    manifest: { manifest_hash: "manifest-v2" },
    field_values: [{ field_code: "air_temperature", field_label: "空气温度", value_text: "22.5" }],
  });

  assert.equal(result.version, 2);
  assert.equal(calls[0].method, "POST");
  assert.match(calls[0].url, /\/api\/coffee\/app\/events\/EV202606250701\/resubmit\/$/);
});

test("returns page wires correction draft state to resubmit action", () => {
  const source = readFileSync(new URL("../src/pages/returns/index.vue", import.meta.url), "utf8");

  assert.match(source, /CoffeeApiClient/);
  assert.match(source, /resubmitEvent/);
  assert.match(source, /resubmitStatus/);
});
