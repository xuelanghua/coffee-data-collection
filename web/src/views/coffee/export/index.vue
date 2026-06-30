<template>
	<fs-page class="coffee-export-page">
		<el-card shadow="never" class="panel">
			<template #header>
				<div class="panel-header">
					<span>导出任务</span>
					<div class="header-actions">
						<el-button size="small" @click="loadExportJobs">刷新</el-button>
						<el-button v-permission="'coffee:export:Create'" type="primary" size="small" @click="handleCreateDatasetPackage">创建数据集包</el-button>
						<el-button v-permission="'coffee:export:Create'" size="small" @click="handleCreateExport">新建导出</el-button>
					</div>
				</div>
			</template>

			<el-form :inline="true" :model="queryForm" class="filter-form" label-width="82px">
				<el-form-item label="任务状态">
					<el-select v-model="queryForm.status" clearable placeholder="全部状态" style="width: 150px">
						<el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
					</el-select>
				</el-form-item>
				<el-form-item label="导出类型">
					<el-select v-model="queryForm.export_type" clearable placeholder="全部类型" style="width: 170px">
						<el-option v-for="item in exportTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
					</el-select>
				</el-form-item>
				<el-form-item label="Event_ID">
					<el-input v-model.trim="datasetEventId" clearable placeholder="EV202606250501" style="width: 190px" />
				</el-form-item>
				<el-form-item>
					<el-button type="primary" @click="handleSearch">查询</el-button>
					<el-button @click="handleReset">重置</el-button>
				</el-form-item>
			</el-form>

			<el-table :data="jobs" size="small" row-key="job_code">
				<el-table-column prop="job_code" label="任务编号" min-width="170" />
				<el-table-column label="导出类型" width="140">
					<template #default="{ row }">
						{{ exportTypeLabel(row.export_type) }}
					</template>
				</el-table-column>
				<el-table-column label="状态" width="120">
					<template #default="{ row }">
						<el-tag :type="statusTagType(row.status)" effect="plain">{{ statusLabel(row.status) }}</el-tag>
					</template>
				</el-table-column>
				<el-table-column label="进度" width="150">
					<template #default="{ row }">
						<el-progress :percentage="Number(row.progress || 0)" :stroke-width="8" />
					</template>
				</el-table-column>
				<el-table-column label="文件路径" min-width="220" show-overflow-tooltip>
					<template #default="{ row }">
						<span>{{ row.file_path || '-' }}</span>
					</template>
				</el-table-column>
				<el-table-column label="文件 SHA256" min-width="220" show-overflow-tooltip>
					<template #default="{ row }">
						<span>{{ row.file_sha256 || '-' }}</span>
					</template>
				</el-table-column>
				<el-table-column prop="expires_at" label="过期时间" min-width="170" />
				<el-table-column label="操作" width="150" fixed="right">
					<template #default="{ row }">
						<el-button v-if="row.file_path" type="primary" link @click="handleCopyFilePath(row)">复制路径</el-button>
						<el-button v-permission="'coffee:export:Cancel'" type="warning" link :disabled="!canCancel(row)" @click="handleCancel(row)">取消</el-button>
					</template>
				</el-table-column>
			</el-table>
		</el-card>
	</fs-page>
</template>

<script lang="ts" setup name="coffeeExport">
import { onMounted, reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { cancelExportJob, createExportJob, getExportJobs } from '/@/api/coffee/export';

const jobs = ref<any[]>([]);
const datasetEventId = ref('');
const queryForm = reactive({
	status: '',
	export_type: '',
});

const exportTypeOptions = [
	{ label: '采集事件明细', value: 'event_detail' },
	{ label: '照片资产清单', value: 'photo_asset' },
	{ label: 'OCR 结果和修正记录', value: 'ocr_correction' },
	{ label: '质检审核记录', value: 'quality_review' },
	{ label: '统计报表', value: 'statistics' },
	{ label: '数据集包', value: 'dataset_package' },
];

const statusOptions = [
	{ label: '排队', value: 'queued' },
	{ label: '处理中', value: 'running' },
	{ label: '完成', value: 'success' },
	{ label: '失败', value: 'failed' },
	{ label: '已取消', value: 'cancelled' },
	{ label: '已过期', value: 'expired' },
];

async function loadExportJobs(params: Record<string, any> = {}) {
	const requestParams = params && Object.keys(params).length ? params : activeQueryParams();
	const data: any = await getExportJobs(requestParams);
	jobs.value = data?.results || [];
	return data;
}

function activeQueryParams() {
	return Object.fromEntries(Object.entries(queryForm).filter(([, value]) => value));
}

function exportTypeLabel(value: string) {
	return exportTypeOptions.find((item) => item.value === value)?.label || value || '-';
}

function statusLabel(value: string) {
	return statusOptions.find((item) => item.value === value)?.label || value || '-';
}

function statusTagType(value: string) {
	const map: Record<string, string> = {
		queued: 'info',
		running: 'warning',
		success: 'success',
		failed: 'danger',
		cancelled: '',
		expired: 'info',
	};
	return map[value] || 'info';
}

function canCancel(row: any) {
	return !['success', 'failed', 'expired', 'cancelled'].includes(row.status);
}

async function handleSearch() {
	await loadExportJobs(activeQueryParams());
}

async function handleReset() {
	queryForm.status = '';
	queryForm.export_type = '';
	await loadExportJobs({});
}

async function handleCreateExport() {
	await createExportJob({
		export_type: 'event_detail',
		filters: {},
	});
	await loadExportJobs();
	ElMessage.success('导出任务已创建');
}

async function handleCreateDatasetPackage() {
	if (!datasetEventId.value) {
		ElMessage.warning('请输入 Event_ID');
		return;
	}
	await createExportJob({
		export_type: 'dataset_package',
		filters: { event_id: datasetEventId.value },
	});
	queryForm.export_type = 'dataset_package';
	await loadExportJobs();
	ElMessage.success('数据集包导出任务已创建');
}

async function handleCopyFilePath(row: any) {
	await navigator.clipboard?.writeText(row.file_path || '');
	ElMessage.success('文件路径已复制');
}

async function handleCancel(row: any) {
	await cancelExportJob(row.job_code);
	await loadExportJobs();
	ElMessage.success('导出任务已取消');
}

onMounted(() => {
	loadExportJobs();
});
</script>

<style scoped>
.coffee-export-page {
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
.header-actions {
	display: flex;
	align-items: center;
	gap: 8px;
}
.filter-form {
	margin-bottom: 12px;
}
</style>
