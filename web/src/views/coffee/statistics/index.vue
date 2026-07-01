<template>
	<fs-page class="coffee-statistics-page">
		<el-card shadow="never" class="panel">
			<template #header>
				<div class="panel-header">
					<span>采集进度</span>
					<el-button @click="loadStatistics">刷新</el-button>
				</div>
			</template>
			<el-row :gutter="20">
				<el-col :span="6"><el-statistic title="事件数" :value="progress.total_events || 0" /></el-col>
				<el-col :span="6"><el-statistic title="地块数" :value="progress.total_plots || 0" /></el-col>
				<el-col :span="6"><el-statistic title="点位数" :value="progress.total_points || 0" /></el-col>
				<el-col :span="6"><el-statistic title="已提交/完成" :value="progress.submitted_or_done || 0" /></el-col>
			</el-row>
			<pre class="json-box">{{ progress.status_counts }}</pre>
		</el-card>

		<el-card shadow="never" class="panel">
			<template #header>
				<span>质量统计</span>
			</template>
			<el-row :gutter="20">
				<el-col :span="8">
					<div class="mini-title">照片审核</div>
					<pre class="json-box compact">{{ quality.photo_review_counts }}</pre>
				</el-col>
				<el-col :span="8">
					<div class="mini-title">预检</div>
					<pre class="json-box compact">{{ quality.precheck_counts }}</pre>
				</el-col>
				<el-col :span="8">
					<div class="mini-title">退回原因</div>
					<pre class="json-box compact">{{ quality.return_reason_counts }}</pre>
				</el-col>
			</el-row>
		</el-card>

		<el-card shadow="never" class="panel">
			<template #header>
				<span>绩效统计</span>
			</template>
			<el-table :data="performance.collectors || []" size="small">
				<el-table-column prop="collector_id" label="采集员" min-width="140" />
				<el-table-column prop="event_count" label="事件数" width="90" />
				<el-table-column prop="approved_count" label="通过数" width="90" />
				<el-table-column prop="returned_count" label="退回数" width="90" />
				<el-table-column prop="approval_rate" label="通过率" width="100" />
				<el-table-column prop="return_rate" label="退回率" width="100" />
			</el-table>
		</el-card>

		<el-card shadow="never" class="panel">
			<template #header>
				<div class="panel-header">
					<span>统计口径中心</span>
					<div class="panel-actions">
						<el-select v-model="metricFilter.metric_group" class="filter-form" size="small" style="width: 128px" @change="loadMetricDefinitions">
							<el-option label="采集进度" value="progress" />
							<el-option label="质量统计" value="quality" />
							<el-option label="绩效统计" value="performance" />
						</el-select>
						<el-button @click="loadMetricDefinitions">刷新</el-button>
						<el-button type="primary" v-permission="'coffee:metric:Create'" @click="openMetricDialog()">新增口径</el-button>
					</div>
				</div>
			</template>
			<el-table :data="metricDefinitions" size="small">
				<el-table-column prop="metric_code" label="指标编码" min-width="140" />
				<el-table-column prop="metric_name" label="指标名称" min-width="140" />
				<el-table-column prop="metric_group" label="分组" width="110" />
				<el-table-column prop="calculation_method" label="计算口径" min-width="220" show-overflow-tooltip />
				<el-table-column prop="version" label="口径版本" width="100" />
				<el-table-column prop="enabled" label="启停" width="90">
					<template #default="{ row }">
						<el-tag :type="row.enabled ? 'success' : 'info'">{{ row.enabled ? '启用' : '停用' }}</el-tag>
					</template>
				</el-table-column>
				<el-table-column label="操作" width="120">
					<template #default="{ row }">
						<el-button link type="primary" v-permission="'coffee:metric:Create'" @click="copyMetricVersion(row)">复制版本</el-button>
					</template>
				</el-table-column>
			</el-table>
			<pre class="json-box compact">{{ progress.metric_definitions }}</pre>
		</el-card>

		<el-dialog v-model="metricDialogVisible" title="口径弹窗" width="640px">
			<el-alert
				class="dialog-help"
				title="计算口径示例：count(scoped CollectionEvent.id)、approved_count / submitted_count。保存会生成新版本，不覆盖历史口径。"
				type="info"
				:closable="false"
				show-icon
			/>
			<el-form :model="metricForm" label-width="86px" size="small">
				<el-form-item label="指标编码">
					<el-input v-model="metricForm.metric_code" placeholder="total_events" />
				</el-form-item>
				<el-form-item label="指标名称">
					<el-input v-model="metricForm.metric_name" placeholder="采集事件总数" />
				</el-form-item>
				<el-form-item label="分组">
					<el-select v-model="metricForm.metric_group">
						<el-option label="采集进度" value="progress" />
						<el-option label="质量统计" value="quality" />
						<el-option label="绩效统计" value="performance" />
					</el-select>
				</el-form-item>
				<el-form-item label="计算口径">
					<el-input v-model="metricForm.calculation_method" type="textarea" :rows="4" placeholder="count(scoped CollectionEvent.id)" />
				</el-form-item>
				<el-form-item label="单位">
					<el-input v-model="metricForm.unit" placeholder="条" />
				</el-form-item>
				<el-form-item label="启停">
					<el-switch v-model="metricForm.enabled" />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="metricDialogVisible = false">取消</el-button>
				<el-button type="primary" @click="createMetric">保存新版本</el-button>
			</template>
		</el-dialog>
	</fs-page>
</template>

<script lang="ts" setup name="coffeeStatistics">
import { onMounted, ref } from 'vue';
import { createMetricDefinition, getMetricDefinitions } from '/@/api/coffee/metric';
import { getPerformanceStatistics, getProgressStatistics, getQualityStatistics } from '/@/api/coffee/statistics';

const progress = ref<any>({});
const quality = ref<any>({});
const performance = ref<any>({});
const metricDefinitions = ref<any[]>([]);
const metricDialogVisible = ref(false);
const metricFilter = ref({
	metric_group: 'progress',
});
const metricForm = ref({
	metric_code: '',
	metric_name: '',
	metric_group: 'progress' as 'progress' | 'quality' | 'performance',
	calculation_method: '',
	description: '',
	unit: '',
	enabled: true,
});

async function loadStatistics() {
	progress.value = await getProgressStatistics();
	quality.value = await getQualityStatistics();
	performance.value = await getPerformanceStatistics();
}

async function loadMetricDefinitions() {
	const response = await getMetricDefinitions(metricFilter.value);
	metricDefinitions.value = response?.results || response?.data?.results || [];
	metricForm.value.metric_group = metricFilter.value.metric_group as 'progress' | 'quality' | 'performance';
}

async function createMetric() {
	await createMetricDefinition(metricForm.value);
	await loadMetricDefinitions();
	await loadStatistics();
	metricDialogVisible.value = false;
}

function openMetricDialog() {
	metricForm.value = {
		metric_code: '',
		metric_name: '',
		metric_group: metricFilter.value.metric_group as 'progress' | 'quality' | 'performance',
		calculation_method: '',
		description: '',
		unit: '',
		enabled: true,
	};
	metricDialogVisible.value = true;
}

function copyMetricVersion(row: any) {
	metricForm.value = {
		metric_code: row.metric_code,
		metric_name: row.metric_name,
		metric_group: row.metric_group,
		calculation_method: row.calculation_method,
		description: row.description || '',
		unit: row.unit || '',
		enabled: row.enabled,
	};
	metricDialogVisible.value = true;
}

onMounted(() => {
	loadStatistics();
	loadMetricDefinitions();
});
</script>

<style scoped>
.coffee-statistics-page {
	display: grid;
	gap: 20px;
	padding: 20px;
	box-sizing: border-box;
	width: 100%;
}
.panel {
	min-width: 0;
	border-radius: 6px;
}
.panel + .panel {
	margin-top: 20px;
}
.panel-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 20px;
}
.panel-actions {
	display: flex;
	align-items: center;
	gap: 8px;
}
.dialog-help {
	margin-bottom: 16px;
}
.mini-title {
	margin-bottom: 6px;
	color: #606266;
	font-size: 13px;
}
.json-box {
	overflow: auto;
	margin-top: 20px;
	padding: 12px;
	background: #f6f8f7;
	border: 1px solid #e2e8e4;
	border-radius: 6px;
	white-space: pre-wrap;
}
.compact {
	max-height: 160px;
	margin-top: 0;
}

@media (max-width: 640px) {
	.coffee-statistics-page {
		padding: 12px;
	}
}
</style>
