import { access, readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { join } from "node:path";

const root = fileURLToPath(new URL("..", import.meta.url));
const required = [
  "App.vue",
  "pages.json",
  "manifest.json",
  "src/services/api.js",
  "src/services/collection-flow.js",
  "src/services/draft-store.js",
  "src/services/geometry.js",
  "src/services/upload-queue.js",
  "src/services/watermark.js",
  "src/pages/login/index.vue",
  "src/pages/collect/index.vue",
];

for (const file of required) {
  await access(join(root, file));
}

const pages = JSON.parse(await readFile(join(root, "pages.json"), "utf8"));
if (!Array.isArray(pages.pages) || pages.pages.length < 2) {
  throw new Error("pages.json must declare at least login and collection pages");
}

console.log("PASS: UniApp app skeleton is build-ready");
