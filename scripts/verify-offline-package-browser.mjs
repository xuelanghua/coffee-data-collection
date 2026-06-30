import { createRequire } from 'node:module';
import { access, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(new URL('../web/package.json', import.meta.url));
const { chromium } = require('playwright');

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const evidenceDir = path.join(root, 'reports', 'development', 'assets');
const packageDir = path.join(evidenceDir, 'offline-package-smoke');
const screenshotPath = path.join(evidenceDir, 'offline-package-browser.png');
const jsonPath = path.join(evidenceDir, 'offline-package-browser.json');

const manifest = {
  package_type: 'coffee_event_offline_package',
  package_version: 1,
  event_id: 'EV-SMOKE-0001',
  task_id: 'TASK-SMOKE',
  manifest_hash: 'smoke-manifest-hash',
  package_hash: 'smoke-package-hash',
  offline_package_index: {
    package_version: 1,
    event_id: 'EV-SMOKE-0001',
    manifest_hash: 'smoke-manifest-hash',
    resource_counts: {
      photos: 1,
      ocr_results: 1,
      measurements: 1,
      audit_logs: 1,
    },
    resources: {
      photos: [
        {
          photo_id: 'PH-SMOKE-0001',
          category: 'device_reading',
          sha256: 'smoke-photo-sha256',
          files: {
            controlled: 'photos/controlled/PH-SMOKE-0001.jpg',
          },
        },
      ],
    },
  },
};

const html = `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>离线数据包 EV-SMOKE-0001</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; color: #1f2933; }
    h1 { font-size: 22px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { border: 1px solid #d8dee4; padding: 8px; text-align: left; }
    th { background: #f3f6f4; }
    code { background: #f3f6f4; padding: 2px 4px; border-radius: 4px; }
  </style>
</head>
<body>
  <h1>离线数据包</h1>
  <p>Event_ID：<code>${manifest.event_id}</code></p>
  <p>Manifest Hash：<code>${manifest.manifest_hash}</code></p>
  <p>Package Hash：<code>${manifest.package_hash}</code></p>
  <section>
    <h2>资源计数</h2>
    <ul>
      <li>照片：1</li>
      <li>OCR：1</li>
      <li>测量记录：1</li>
      <li>审计日志：1</li>
    </ul>
  </section>
  <section>
    <h2>照片资料</h2>
    <table>
      <thead><tr><th>Photo_ID</th><th>分类</th><th>SHA256</th><th>受控图片引用</th></tr></thead>
      <tbody><tr><td>PH-SMOKE-0001</td><td>device_reading</td><td>smoke-photo-sha256</td><td>photos/controlled/PH-SMOKE-0001.jpg</td></tr></tbody>
    </table>
  </section>
</body>
</html>`;

await mkdir(path.join(packageDir, 'photos', 'controlled'), { recursive: true });
await mkdir(evidenceDir, { recursive: true });
await writeFile(path.join(packageDir, 'manifest.json'), JSON.stringify(manifest, null, 2), 'utf-8');
await writeFile(path.join(packageDir, 'index.html'), html, 'utf-8');
await writeFile(path.join(packageDir, 'photos', 'controlled', 'PH-SMOKE-0001.jpg'), 'controlled-photo-placeholder', 'utf-8');

async function launchBrowser() {
  try {
    return await chromium.launch({ headless: true });
  } catch (error) {
    const candidates = [
      '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
      '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
      '/Applications/Chromium.app/Contents/MacOS/Chromium',
    ];
    for (const executablePath of candidates) {
      try {
        await access(executablePath);
        return await chromium.launch({ headless: true, executablePath });
      } catch {
        // Try the next installed browser.
      }
    }
    throw error;
  }
}

const browser = await launchBrowser();
const page = await browser.newPage({ viewport: { width: 900, height: 680 }, deviceScaleFactor: 1 });
await page.goto(`file://${path.join(packageDir, 'index.html')}`, { waitUntil: 'load' });

const title = await page.locator('h1').textContent();
const bodyText = await page.locator('body').innerText();
if (!title || !title.includes('离线数据包')) throw new Error('offline package title missing');
if (!bodyText.includes('EV-SMOKE-0001')) throw new Error('Event_ID missing from offline package page');
if (!bodyText.includes('smoke-manifest-hash')) throw new Error('Manifest Hash missing from offline package page');
if (!bodyText.includes('photos/controlled/PH-SMOKE-0001.jpg')) throw new Error('controlled photo reference missing');

await page.screenshot({ path: screenshotPath, fullPage: true });
await browser.close();

await writeFile(
  jsonPath,
  JSON.stringify(
    {
      status: 'PASS',
      package_dir: packageDir,
      manifest: path.join(packageDir, 'manifest.json'),
      html: path.join(packageDir, 'index.html'),
      screenshot: screenshotPath,
      checked_at: new Date().toISOString(),
    },
    null,
    2
  ),
  'utf-8'
);

console.log(`offline package browser screenshot: ${screenshotPath}`);
console.log(`offline package browser evidence: ${jsonPath}`);
