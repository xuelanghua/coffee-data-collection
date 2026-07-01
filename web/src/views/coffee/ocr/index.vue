<template>
	<fs-page class="coffee-ocr-page">
		<el-card shadow="never" class="panel">
			<template #header>
				<div class="panel-header">
					<span>OCR 任务</span>
					<el-button @click="loadOcrJobs">刷新</el-button>
				</div>
			</template>
			<el-form :inline="true" :model="queryForm" class="filter-form" label-width="78px">
				<el-form-item label="状态">
					<el-select v-model="queryForm.status" clearable placeholder="全部" style="width: 130px">
						<el-option label="成功" value="success" />
						<el-option label="失败" value="failed" />
						<el-option label="待处理" value="pending" />
					</el-select>
				</el-form-item>
				<el-form-item label="Provider">
					<el-input v-model.trim="queryForm.provider" clearable placeholder="paddle_ocr" style="width: 150px" />
				</el-form-item>
				<el-form-item label="Event_ID">
					<el-input v-model.trim="queryForm.event_id" clearable placeholder="EV..." style="width: 160px" />
				</el-form-item>
				<el-form-item>
					<el-button type="primary" @click="handleSearch">查询</el-button>
					<el-button @click="handleReset">重置</el-button>
				</el-form-item>
			</el-form>
			<el-table :data="ocrJobs" size="small" @row-click="selectOcrJob">
				<el-table-column prop="ocr_result_id" label="OCR_ID" min-width="170" />
				<el-table-column prop="photo_id" label="Photo_ID" min-width="150" />
				<el-table-column prop="event_id" label="Event_ID" min-width="150" />
				<el-table-column prop="provider" label="Provider" width="120" />
				<el-table-column prop="status" label="状态" width="108" />
				<el-table-column prop="confidence" label="置信度" width="100" />
				<el-table-column prop="correction_count" label="修正数" width="90" />
				<el-table-column label="操作" width="100" fixed="right">
					<template #default="{ row }">
						<el-button v-permission="'coffee:ocr:Correct'" type="primary" link @click.stop="openCorrectionDialog(row)">校正</el-button>
					</template>
				</el-table-column>
			</el-table>
		</el-card>

		<el-card shadow="never" class="panel correction-panel">
			<template #header>
				<div class="panel-header">
					<span>OCR 校正</span>
					<el-tag v-if="selectedJob" size="small">{{ selectedJob.ocr_result_id }}</el-tag>
				</div>
			</template>
			<el-empty v-if="!selectedJob" description="请选择 OCR 任务" />
			<template v-else>
				<el-button v-permission="'coffee:ocr:Correct'" type="primary" @click="openCorrectionDialog(selectedJob)">打开校正弹窗</el-button>
				<pre class="json-box">{{ selectedJob.structured_json }}</pre>
			</template>
		</el-card>

		<el-dialog v-model="correctionDialogVisible" title="校正弹窗" width="560px">
			<el-alert
				class="dialog-help"
				title="设备字段示例：wind_speed、wind_direction、air_temperature、air_humidity、atmospheric_pressure、rainfall、soil_moisture、soil_temperature、soil_salinity、soil_ph。修正原因示例：OCR 将 18.6 识别为 186。"
				type="info"
				:closable="false"
				show-icon
			/>
			<el-form :model="correctionForm" label-width="84px">
				<el-form-item label="识别字段">
					<el-input v-model="correctionForm.field_name" placeholder="field_name" />
				</el-form-item>
				<el-form-item label="原始值">
					<el-input v-model="correctionForm.raw_value" />
				</el-form-item>
				<el-form-item label="人工值">
					<el-input v-model="correctionForm.corrected_value" />
				</el-form-item>
				<el-form-item label="修正原因">
					<el-input v-model="correctionForm.reason" type="textarea" :rows="3" />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="correctionDialogVisible = false">取消</el-button>
				<el-button v-permission="'coffee:ocr:Correct'" type="primary" @click="handleSaveCorrection">保存修正</el-button>
			</template>
		</el-dialog>
	</fs-page>
</template>

<script lang="ts" setup name="coffeeOcr">
import { onMounted, reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { getOcrJobs, saveOcrCorrection } from '/@/api/coffee/ocr';

const ocrJobs = ref<any[]>([]);
const selectedJob = ref<any>(null);
const correctionDialogVisible = ref(false);
const queryForm = reactive({
	status: '',
	provider: '',
	event_id: '',
});
const correctionForm = reactive({
	field_name: 'air_temperature',
	raw_value: '',
	corrected_value: '',
	reason: '',
});

async function loadOcrJobs(params: Record<string, any> = activeQueryParams()) {
	const data: any = await getOcrJobs(params);
	ocrJobs.value = data?.results || [];
	return data;
}

function activeQueryParams() {
	return Object.fromEntries(Object.entries(queryForm).filter(([, value]) => value));
}

function selectOcrJob(row: any) {
	selectedJob.value = row;
	const firstField = row?.structured_json ? Object.keys(row.structured_json)[0] : '';
	const firstValue = firstField ? row.structured_json[firstField]?.value : '';
	correctionForm.field_name = firstField || 'air_temperature';
	correctionForm.raw_value = firstValue || '';
	correctionForm.corrected_value = firstValue || '';
	correctionForm.reason = '';
}

function openCorrectionDialog(row: any) {
	selectOcrJob(row);
	correctionDialogVisible.value = true;
}

async function handleSearch() {
	await loadOcrJobs(activeQueryParams());
}

async function handleReset() {
	queryForm.status = '';
	queryForm.provider = '';
	queryForm.event_id = '';
	await loadOcrJobs({});
}

async function handleSaveCorrection() {
	if (!selectedJob.value?.ocr_result_id) return;
	await saveOcrCorrection(selectedJob.value.ocr_result_id, { ...correctionForm });
	await loadOcrJobs();
	correctionDialogVisible.value = false;
	ElMessage.success('OCR 修正已保存');
}

onMounted(() => {
	loadOcrJobs();
});
</script>

<style scoped>
.coffee-ocr-page {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(520px, 1fr));
	align-items: stretch;
	gap: 20px;
	padding: 20px;
	box-sizing: border-box;
	width: 100%;
}
.panel {
	min-width: 0;
	height: 100%;
	border-radius: 6px;
}
.panel-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 20px;
}
.filter-form {
	display: flex;
	align-items: center;
	flex-wrap: wrap;
	gap: 12px 20px;
	margin-bottom: 20px;
}
.filter-form :deep(.el-form-item) {
	align-items: center;
	margin-right: 0;
	margin-bottom: 0;
}
.dialog-help {
	margin-bottom: 16px;
}
.correction-panel {
	min-width: 0;
	min-height: 320px;
}
.json-box {
	max-height: 280px;
	overflow: auto;
	padding: 12px;
	background: #f6f8f7;
	border: 1px solid #e2e8e4;
	border-radius: 6px;
	white-space: pre-wrap;
}

@media (max-width: 640px) {
	.coffee-ocr-page {
		grid-template-columns: minmax(0, 1fr);
		padding: 12px;
	}
}
</style>
