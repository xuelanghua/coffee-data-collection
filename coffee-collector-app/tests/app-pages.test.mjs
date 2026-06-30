import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("..", import.meta.url));

test("pages.json declares App-first field collection support pages", async () => {
  const pagesJson = JSON.parse(await readFile(join(root, "pages.json"), "utf8"));
  const paths = pagesJson.pages.map((page) => page.path);

  assert.ok(paths.includes("src/pages/plot-map/index"));
  assert.ok(paths.includes("src/pages/photo-capture/index"));
  assert.ok(paths.includes("src/pages/upload-queue/index"));
  assert.ok(paths.includes("src/pages/returns/index"));
});

test("field support pages are wired to local services", async () => {
  const expectations = [
    ["src/pages/plot-map/index.vue", "PlotDrawingSession"],
    ["src/pages/photo-capture/index.vue", "buildPhotoWatermark"],
    ["src/pages/upload-queue/index.vue", "UploadQueue"],
    ["src/pages/returns/index.vue", "LocalDraftStore"],
  ];

  for (const [file, marker] of expectations) {
    const content = await readFile(join(root, file), "utf8");
    assert.match(content, new RegExp(marker));
  }
});
