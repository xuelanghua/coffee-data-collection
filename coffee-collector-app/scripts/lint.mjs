import { readdir, readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { join } from "node:path";

const root = fileURLToPath(new URL("..", import.meta.url));
const files = await collect(root);
for (const file of files) {
  const content = await readFile(file, "utf8");
  if (/\t/.test(content)) {
    throw new Error(`Tab indentation is not allowed: ${file}`);
  }
}
console.log(`PASS: linted ${files.length} source files`);

async function collect(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  const result = [];
  for (const entry of entries) {
    if (entry.name === "node_modules") continue;
    const path = join(dir, entry.name);
    if (entry.isDirectory()) {
      result.push(...await collect(path));
    } else if (/\.(js|mjs|vue|json)$/.test(entry.name)) {
      result.push(path);
    }
  }
  return result;
}
