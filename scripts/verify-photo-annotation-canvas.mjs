import { createRequire } from 'node:module';
import { access, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(new URL('../web/package.json', import.meta.url));
const { chromium } = require('playwright');

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const evidenceDir = path.join(root, 'reports', 'development', 'assets');
const screenshotPath = path.join(evidenceDir, 'photo-annotation-canvas.png');
const jsonPath = path.join(evidenceDir, 'photo-annotation-canvas.json');

const imageSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400" viewBox="0 0 800 400">
  <defs>
    <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0" stop-color="#d7f4e1"/>
      <stop offset="1" stop-color="#6da47d"/>
    </linearGradient>
  </defs>
  <rect width="800" height="400" fill="url(#g)"/>
  <circle cx="260" cy="180" r="70" fill="#b71c1c"/>
  <circle cx="350" cy="210" r="62" fill="#d32f2f"/>
  <circle cx="445" cy="166" r="74" fill="#8bc34a"/>
  <text x="32" y="54" fill="#18382a" font-size="32" font-family="Arial">Pu'er Coffee Sample Photo</text>
</svg>`;

const html = `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"/>
  <style>
    body { margin: 0; font-family: Arial, sans-serif; background: #eef3f0; }
    .page { width: 760px; margin: 28px auto; background: white; padding: 18px; border: 1px solid #d8e0dc; border-radius: 6px; }
    .toolbar { display: flex; gap: 8px; align-items: center; color: #51615a; margin: 8px 0 10px; }
    .tag { padding: 2px 8px; border: 1px solid #32d583; color: #087443; border-radius: 4px; font-size: 12px; }
    .annotation-canvas { position: relative; width: 400px; height: 240px; overflow: hidden; background: #101815; cursor: crosshair; border-radius: 6px; border: 1px solid #d8e0dc; }
    .annotation-image { width: 100%; height: 100%; object-fit: contain; display: block; }
    .annotation-box { position: absolute; box-sizing: border-box; border: 2px solid #32d583; background: rgba(50, 213, 131, .16); pointer-events: none; }
    textarea { width: 720px; height: 150px; margin-top: 12px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
  </style>
</head>
<body>
  <main class="page">
    <h1>照片资产 - 人工标注</h1>
    <div class="toolbar"><span class="tag">拖拽框选</span><span>浏览器 smoke 验证：自动生成 display_box 和 natural_box</span></div>
    <div class="annotation-canvas" id="canvas">
      <img id="photo" class="annotation-image" draggable="false" src="data:image/svg+xml;base64,${Buffer.from(imageSvg).toString('base64')}"/>
      <div id="box" class="annotation-box" hidden></div>
    </div>
    <textarea id="geometry" aria-label="geometry"></textarea>
  </main>
  <script>
    const canvas = document.getElementById('canvas');
    const image = document.getElementById('photo');
    const box = document.getElementById('box');
    const geometry = document.getElementById('geometry');
    let start = null;
    let metrics = { naturalWidth: 0, naturalHeight: 0, displayWidth: 0, displayHeight: 0 };

    image.addEventListener('load', () => {
      metrics = {
        naturalWidth: image.naturalWidth,
        naturalHeight: image.naturalHeight,
        displayWidth: image.clientWidth,
        displayHeight: image.clientHeight,
      };
    });
    function canvasPoint(event) {
      const rect = canvas.getBoundingClientRect();
      return {
        x: Math.max(0, Math.min(rect.width, event.clientX - rect.left)),
        y: Math.max(0, Math.min(rect.height, event.clientY - rect.top)),
      };
    }
    function toNaturalBox(display_box) {
      const scaleX = metrics.naturalWidth / metrics.displayWidth;
      const scaleY = metrics.naturalHeight / metrics.displayHeight;
      return {
        x: Math.round(display_box.x * scaleX),
        y: Math.round(display_box.y * scaleY),
        width: Math.round(display_box.width * scaleX),
        height: Math.round(display_box.height * scaleY),
      };
    }
    function render(display_box) {
      box.hidden = false;
      box.style.left = display_box.x + 'px';
      box.style.top = display_box.y + 'px';
      box.style.width = display_box.width + 'px';
      box.style.height = display_box.height + 'px';
      geometry.value = JSON.stringify({
        display_box,
        natural_box: toNaturalBox(display_box),
        naturalWidth: metrics.naturalWidth,
        naturalHeight: metrics.naturalHeight,
      }, null, 2);
    }
    canvas.addEventListener('mousedown', (event) => {
      start = canvasPoint(event);
      render({ x: start.x, y: start.y, width: 0, height: 0 });
    });
    canvas.addEventListener('mousemove', (event) => {
      if (!start) return;
      const point = canvasPoint(event);
      render({
        x: Math.round(Math.min(start.x, point.x)),
        y: Math.round(Math.min(start.y, point.y)),
        width: Math.round(Math.abs(point.x - start.x)),
        height: Math.round(Math.abs(point.y - start.y)),
      });
    });
    canvas.addEventListener('mouseup', () => { start = null; });
  </script>
</body>
</html>`;

await mkdir(evidenceDir, { recursive: true });

async function firstExisting(paths) {
  for (const candidate of paths) {
    try {
      await access(candidate);
      return candidate;
    } catch {
      // Try next installed browser.
    }
  }
  return null;
}

async function launchBrowser() {
  try {
    return await chromium.launch({ headless: true });
  } catch (error) {
    const executablePath = await firstExisting([
      '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
      '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
      '/Applications/Chromium.app/Contents/MacOS/Chromium',
    ]);
    if (!executablePath) throw error;
    return chromium.launch({ headless: true, executablePath });
  }
}

const browser = await launchBrowser();
const page = await browser.newPage({ viewport: { width: 820, height: 620 }, deviceScaleFactor: 1 });
await page.setContent(html, { waitUntil: 'load' });
await page.locator('#photo').waitFor({ state: 'visible' });

const canvasBox = await page.locator('#canvas').boundingBox();
if (!canvasBox) throw new Error('annotation canvas is not visible');

await page.mouse.move(canvasBox.x + 80, canvasBox.y + 60);
await page.mouse.down();
await page.mouse.move(canvasBox.x + 220, canvasBox.y + 150, { steps: 8 });
await page.mouse.up();

const evidence = await page.locator('#geometry').inputValue();
const parsed = JSON.parse(evidence);
if (!parsed.display_box || !parsed.natural_box) throw new Error('missing display_box or natural_box');
if (parsed.display_box.width <= 0 || parsed.display_box.height <= 0) throw new Error('display_box was not drawn');
if (parsed.natural_box.width <= parsed.display_box.width) throw new Error('natural_box was not scaled from display_box');

await page.screenshot({ path: screenshotPath, fullPage: true });
await writeFile(
  jsonPath,
  JSON.stringify(
    {
      status: 'PASS',
      screenshot: screenshotPath,
      geometry: parsed,
      checked_at: new Date().toISOString(),
    },
    null,
    2
  ),
  'utf-8'
);
await browser.close();

console.log(`photo annotation canvas screenshot: ${screenshotPath}`);
console.log(`photo annotation canvas evidence: ${jsonPath}`);
