<template>
	<fs-page class="coffee-ocr-page">
		<el-card shadow="never" class="panel">
			<template #header>
				<div class="panel-header">
					<span>OCR 任务</span>
					<el-button size="small" @click="loadOcrJobs">刷新</el-button>
				</div>
			</template>
			<el-table :data="ocrJobs" size="small" @row-click="selectOcrJob">
				<el-table-column prop="ocr_result_id" label="OCR_ID" min-width="170" />
				<el-table-column prop="photo_id" label="Photo_ID" min-width="150" />
				<el-table-column prop="event_id" label="Event_ID" min-width="150" />
				<el-table-column prop="provider" label="Provider" width="120" />
				<el-table-column prop="status" label="状态" width="108" />
				<el-table-column prop="confidence" label="置信度" width="100" />
				<el-table-column prop="correction_count" label="修正数" width="90" />
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
				<el-form label-width="84px" size="small">
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
					<el-form-item>
						<el-button v-permission="'coffee:ocr:Correct'" type="primary" @click="handleSaveCorrection">保存修正</el-button>
					</el-form-item>
				</el-form>
				<pre class="json-box">{{ selectedJob.structured_json }}</pre>
			</template>
		</el-card>
	</fs-page>
</template>

<script lang="ts" setup name="coffeeOcr">
import { onMounted, reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { getOcrJobs, saveOcrCorrection } from '/@/api/coffee/ocr';

const ocrJobs = ref<any[]>([]);
const selectedJob = ref<any>(null);
const correctionForm = reactive({
	field_name: 'air_temperature',
	raw_value: '',
	corrected_value: '',
	reason: '',
});

async function loadOcrJobs(params: Record<string, any> = {}) {
	const data: any = await getOcrJobs(params);
	ocrJobs.value = data?.results || [];
	return data;
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

async function handleSaveCorrection() {
	if (!selectedJob.value?.ocr_result_id) return;
	await saveOcrCorrection(selectedJob.value.ocr_result_id, { ...correctionForm });
	await loadOcrJobs();
	ElMessage.success('OCR 修正已保存');
}

onMounted(() => {
	loadOcrJobs();
});
</script>

<style scoped>
.coffee-ocr-page {
	display: grid;
	grid-template-columns: minmax(0, 1fr) 380px;
	gap: 12px;
	padding: 12px;
}
.panel {
	border-radius: 6px;
}
.panel-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 12px;
}
.correction-panel {
	min-width: 0;
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
</style>
