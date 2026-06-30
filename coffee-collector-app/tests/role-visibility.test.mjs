import assert from "node:assert/strict";
import test from "node:test";

import { getVisibleAppEntries } from "../src/services/role-visibility.js";

test("collector sees field collection entries but not review or admin entries", () => {
  const entries = getVisibleAppEntries(["coffee_collector"]).map((item) => item.key);

  assert.deepEqual(entries, ["tasks", "collect", "uploadQueue", "returns", "myRecords", "settings"]);
  assert.equal(entries.includes("review"), false);
  assert.equal(entries.includes("providerConfig"), false);
});

test("reviewer and admin receive role-specific App support entries", () => {
  const reviewerEntries = getVisibleAppEntries(["coffee_reviewer"]).map((item) => item.key);
  const adminEntries = getVisibleAppEntries(["coffee_admin"]).map((item) => item.key);

  assert.ok(reviewerEntries.includes("review"));
  assert.ok(reviewerEntries.includes("ocrCorrection"));
  assert.equal(reviewerEntries.includes("providerConfig"), false);
  assert.ok(adminEntries.includes("providerConfig"));
  assert.ok(adminEntries.includes("statistics"));
});

test("viewer only sees read-only records and statistics entries", () => {
  const entries = getVisibleAppEntries(["coffee_viewer"]).map((item) => item.key);

  assert.deepEqual(entries, ["tasks", "myRecords", "statistics", "settings"]);
  assert.equal(entries.includes("collect"), false);
  assert.equal(entries.includes("uploadQueue"), false);
});
