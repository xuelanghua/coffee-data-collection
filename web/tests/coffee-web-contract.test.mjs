import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import test from "node:test";

const apiPath = new URL("../src/api/coffee/event.ts", import.meta.url);
const photoApiPath = new URL("../src/api/coffee/photo.ts", import.meta.url);
const ocrApiPath = new URL("../src/api/coffee/ocr.ts", import.meta.url);
const providerApiPath = new URL("../src/api/coffee/provider.ts", import.meta.url);
const statisticsApiPath = new URL("../src/api/coffee/statistics.ts", import.meta.url);
const metricApiPath = new URL("../src/api/coffee/metric.ts", import.meta.url);
const exportApiPath = new URL("../src/api/coffee/export.ts", import.meta.url);
const bGradeApiPath = new URL("../src/api/coffee/b-grade.ts", import.meta.url);
const pagePath = new URL("../src/views/coffee/event/index.vue", import.meta.url);
const photoPagePath = new URL("../src/views/coffee/photo/index.vue", import.meta.url);
const ocrPagePath = new URL("../src/views/coffee/ocr/index.vue", import.meta.url);
const providerPagePath = new URL("../src/views/coffee/provider/index.vue", import.meta.url);
const statisticsPagePath = new URL("../src/views/coffee/statistics/index.vue", import.meta.url);
const exportPagePath = new URL("../src/views/coffee/export/index.vue", import.meta.url);
const bGradePagePath = new URL("../src/views/coffee/b-grade/index.vue", import.meta.url);

test("coffee web event api wraps detail and review endpoints", () => {
  assert.equal(existsSync(apiPath), true);
  const source = readFileSync(apiPath, "utf8");

  assert.match(source, /getEventDetail/);
  assert.match(source, /getEventList/);
  assert.match(source, /approveEvent/);
  assert.match(source, /returnEvent/);
  assert.match(source, /bulkApproveEvents/);
  assert.match(source, /bulkReturnEvents/);
  assert.match(source, /\/api\/coffee\/events\/\$\{eventId\}\//);
  assert.match(source, /url:\s*'\/api\/coffee\/events\/'/);
  assert.match(source, /\/api\/coffee\/events\/review\/bulk-approve\//);
  assert.match(source, /\/api\/coffee\/events\/review\/bulk-return\//);
});

test("coffee web event page exposes list, detail sections and batch review actions", () => {
  assert.equal(existsSync(pagePath), true);
  const source = readFileSync(pagePath, "utf8");

  assert.match(source, /Event_ID/);
  assert.match(source, /Plot_ID/);
  assert.match(source, /Point_ID/);
  assert.match(source, /地块信息/);
  assert.match(source, /图片资料/);
  assert.match(source, /OCR 识别/);
  assert.match(source, /设备采集数据/);
  assert.match(source, /质检记录/);
  assert.match(source, /批量通过/);
  assert.match(source, /批量退回/);
  assert.match(source, /getEventDetail/);
  assert.match(source, /loadEventList/);
  assert.match(source, /onMounted/);
  assert.match(source, /bulkApproveEvents/);
  assert.match(source, /v-permission="'coffee:event:Approve'"/);
  assert.match(source, /v-permission="'coffee:event:Return'"/);
  assert.match(source, /v-permission="'coffee:event:BulkApprove'"/);
  assert.match(source, /v-permission="'coffee:event:BulkReturn'"/);
});

test("coffee web photo api and page expose photo review workflow", () => {
  assert.equal(existsSync(photoApiPath), true);
  const apiSource = readFileSync(photoApiPath, "utf8");
  assert.match(apiSource, /getPhotoList/);
  assert.match(apiSource, /reviewPhoto/);
  assert.match(apiSource, /getPhotoAnnotations/);
  assert.match(apiSource, /savePhotoAnnotation/);
  assert.match(apiSource, /\/api\/coffee\/photos\//);
  assert.match(apiSource, /\/api\/coffee\/photos\/\$\{photoId\}\/review\//);
  assert.match(apiSource, /\/api\/coffee\/photos\/\$\{photoId\}\/annotations\//);

  assert.equal(existsSync(photoPagePath), true);
  const pageSource = readFileSync(photoPagePath, "utf8");
  assert.match(pageSource, /Photo_ID/);
  assert.match(pageSource, /Event_ID/);
  assert.match(pageSource, /metadata/);
  assert.match(pageSource, /人工标注/);
  assert.match(pageSource, /拖拽框选/);
  assert.match(pageSource, /保存标注/);
  assert.match(pageSource, /版本/);
  assert.match(pageSource, /annotation-canvas/);
  assert.match(pageSource, /annotation-box/);
  assert.match(pageSource, /@mousedown="startBoxAnnotation"/);
  assert.match(pageSource, /@mousemove="moveBoxAnnotation"/);
  assert.match(pageSource, /@mouseup="finishBoxAnnotation"/);
  assert.match(pageSource, /@load="captureNaturalImageSize"/);
  assert.match(pageSource, /function startBoxAnnotation/);
  assert.match(pageSource, /function moveBoxAnnotation/);
  assert.match(pageSource, /function finishBoxAnnotation/);
  assert.match(pageSource, /function captureNaturalImageSize/);
  assert.match(pageSource, /function toNaturalBox/);
  assert.match(pageSource, /naturalWidth/);
  assert.match(pageSource, /naturalHeight/);
  assert.match(pageSource, /display_box/);
  assert.match(pageSource, /natural_box/);
  assert.match(pageSource, /updateAnnotationGeometryFromCanvas/);
  assert.match(pageSource, /审核通过/);
  assert.match(pageSource, /退回补拍/);
  assert.match(pageSource, /getPhotoList/);
  assert.match(pageSource, /reviewPhoto/);
  assert.match(pageSource, /getPhotoAnnotations/);
  assert.match(pageSource, /savePhotoAnnotation/);
  assert.match(pageSource, /v-permission="'coffee:photo:Approve'"/);
  assert.match(pageSource, /v-permission="'coffee:photo:Return'"/);
  assert.match(pageSource, /v-permission="'coffee:photo:Annotate'"/);
});

test("coffee web ocr api and page expose correction workflow", () => {
  assert.equal(existsSync(ocrApiPath), true);
  const apiSource = readFileSync(ocrApiPath, "utf8");
  assert.match(apiSource, /getOcrJobs/);
  assert.match(apiSource, /saveOcrCorrection/);
  assert.match(apiSource, /\/api\/coffee\/ocr\/jobs\//);
  assert.match(apiSource, /\/api\/coffee\/ocr-results\/\$\{ocrResultId\}\/corrections\//);

  assert.equal(existsSync(ocrPagePath), true);
  const pageSource = readFileSync(ocrPagePath, "utf8");
  assert.match(pageSource, /OCR_ID/);
  assert.match(pageSource, /Photo_ID/);
  assert.match(pageSource, /Provider/);
  assert.match(pageSource, /置信度/);
  assert.match(pageSource, /人工值/);
  assert.match(pageSource, /修正原因/);
  assert.match(pageSource, /getOcrJobs/);
  assert.match(pageSource, /saveOcrCorrection/);
  assert.match(pageSource, /v-permission="'coffee:ocr:Correct'"/);
});

test("coffee web provider api and page expose safe provider configuration workflow", () => {
  assert.equal(existsSync(providerApiPath), true);
  const apiSource = readFileSync(providerApiPath, "utf8");
  assert.match(apiSource, /getProviderConfigs/);
  assert.match(apiSource, /createProviderConfig/);
  assert.match(apiSource, /testProviderConfig/);
  assert.match(apiSource, /\/api\/coffee\/provider-configs\//);
  assert.match(apiSource, /\/api\/coffee\/provider-configs\/\$\{providerId\}\/test\//);

  assert.equal(existsSync(providerPagePath), true);
  const pageSource = readFileSync(providerPagePath, "utf8");
  assert.match(pageSource, /Provider 类型/);
  assert.match(pageSource, /地图 Provider/);
  assert.match(pageSource, /腾讯地图/);
  assert.match(pageSource, /百度地图/);
  assert.match(pageSource, /地图能力/);
  assert.match(pageSource, /reverse_geocode/);
  assert.match(pageSource, /boundary_polygon/);
  assert.match(pageSource, /area_recheck/);
  assert.match(pageSource, /脱敏 Key/);
  assert.match(pageSource, /连接测试/);
  assert.match(pageSource, /启用状态/);
  assert.match(pageSource, /getProviderConfigs/);
  assert.match(pageSource, /createProviderConfig/);
  assert.match(pageSource, /testProviderConfig/);
  assert.match(pageSource, /createTencentMapProvider/);
  assert.match(pageSource, /createBaiduMapProvider/);
  assert.match(pageSource, /v-permission="'coffee:provider:Create'"/);
  assert.match(pageSource, /v-permission="'coffee:provider:Test'"/);
});

test("coffee web statistics api and page expose progress quality and performance views", () => {
  assert.equal(existsSync(statisticsApiPath), true);
  const apiSource = readFileSync(statisticsApiPath, "utf8");
  assert.match(apiSource, /getProgressStatistics/);
  assert.match(apiSource, /getQualityStatistics/);
  assert.match(apiSource, /getPerformanceStatistics/);
  assert.match(apiSource, /\/api\/coffee\/statistics\/progress\//);
  assert.match(apiSource, /\/api\/coffee\/statistics\/quality\//);
  assert.match(apiSource, /\/api\/coffee\/statistics\/performance\//);

  assert.equal(existsSync(statisticsPagePath), true);
  const pageSource = readFileSync(statisticsPagePath, "utf8");
  assert.match(pageSource, /采集进度/);
  assert.match(pageSource, /质量统计/);
  assert.match(pageSource, /绩效统计/);
  assert.match(pageSource, /getProgressStatistics/);
  assert.match(pageSource, /getQualityStatistics/);
  assert.match(pageSource, /getPerformanceStatistics/);
});

test("coffee web metric center api and statistics page expose metric definitions", () => {
  assert.equal(existsSync(metricApiPath), true);
  const apiSource = readFileSync(metricApiPath, "utf8");
  assert.match(apiSource, /CoffeeMetricDefinitionPayload/);
  assert.match(apiSource, /getMetricDefinitions/);
  assert.match(apiSource, /createMetricDefinition/);
  assert.match(apiSource, /\/api\/coffee\/metric-definitions\//);

  assert.equal(existsSync(statisticsPagePath), true);
  const pageSource = readFileSync(statisticsPagePath, "utf8");
  assert.match(pageSource, /统计口径中心/);
  assert.match(pageSource, /指标编码/);
  assert.match(pageSource, /计算口径/);
  assert.match(pageSource, /口径版本/);
  assert.match(pageSource, /复制版本/);
  assert.match(pageSource, /启停/);
  assert.match(pageSource, /新增口径/);
  assert.match(pageSource, /metric_definitions/);
  assert.match(pageSource, /getMetricDefinitions/);
  assert.match(pageSource, /createMetricDefinition/);
  assert.match(pageSource, /v-permission="'coffee:metric:Create'"/);
}
);

test("coffee web export api and page expose export job workflow", () => {
  assert.equal(existsSync(exportApiPath), true);
  const apiSource = readFileSync(exportApiPath, "utf8");
  assert.match(apiSource, /getExportJobs/);
  assert.match(apiSource, /createExportJob/);
  assert.match(apiSource, /cancelExportJob/);
  assert.match(apiSource, /\/api\/coffee\/exports\//);
  assert.match(apiSource, /\/api\/coffee\/exports\/\$\{jobCode\}\/cancel\//);

  assert.equal(existsSync(exportPagePath), true);
  const pageSource = readFileSync(exportPagePath, "utf8");
  assert.match(pageSource, /导出任务/);
  assert.match(pageSource, /新建导出/);
  assert.match(pageSource, /数据集包/);
  assert.match(pageSource, /Event_ID/);
  assert.match(pageSource, /文件 SHA256/);
  assert.match(pageSource, /文件路径/);
  assert.match(pageSource, /任务状态/);
  assert.match(pageSource, /复制路径/);
  assert.match(pageSource, /创建数据集包/);
  assert.match(pageSource, /ExportJob\.TYPE_DATASET_PACKAGE|dataset_package/);
  assert.match(pageSource, /取消/);
  assert.match(pageSource, /getExportJobs/);
  assert.match(pageSource, /createExportJob/);
  assert.match(pageSource, /cancelExportJob/);
  assert.match(pageSource, /handleCreateDatasetPackage/);
  assert.match(pageSource, /handleCopyFilePath/);
  assert.match(pageSource, /v-permission="'coffee:export:Create'"/);
  assert.match(pageSource, /v-permission="'coffee:export:Cancel'"/);
});

test("coffee web b grade rule api and page expose rule simulation workflow", () => {
  assert.equal(existsSync(bGradeApiPath), true);
  const apiSource = readFileSync(bGradeApiPath, "utf8");
  assert.match(apiSource, /getBGradeRules/);
  assert.match(apiSource, /createBGradeRule/);
  assert.match(apiSource, /checkBGradeRule/);
  assert.match(apiSource, /\/api\/coffee\/b-grade-rules\//);
  assert.match(apiSource, /\/api\/coffee\/b-grade-rules\/\$\{ruleCode\}\/check\//);

  assert.equal(existsSync(bGradePagePath), true);
  const pageSource = readFileSync(bGradePagePath, "utf8");
  assert.match(pageSource, /B 级规则/);
  assert.match(pageSource, /规则名称/);
  assert.match(pageSource, /阻断级别/);
  assert.match(pageSource, /模拟检查/);
  assert.match(pageSource, /getBGradeRules/);
  assert.match(pageSource, /createBGradeRule/);
  assert.match(pageSource, /checkBGradeRule/);
});
