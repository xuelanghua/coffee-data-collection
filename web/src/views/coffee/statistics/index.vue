<template>
	<fs-page class="coffee-statistics-page">
		<el-card shadow="never" class="panel">
			<template #header>
				<div class="panel-header">
					<span>采集进度</span>
					<el-button size="small" @click="loadStatistics">刷新</el-button>
				</div>
			</template>
			<el-row :gutter="12">
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
			<el-row :gutter="12">
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
						<el-select v-model="metricFilter.metric_group" size="small" style="width: 128px" @change="loadMetricDefinitions">
							<el-option label="采集进度" value="progress" />
							<el-option label="质量统计" value="quality" />
							<el-option label="绩效统计" value="performance" />
						</el-select>
						<el-button size="small" @click="loadMetricDefinitions">刷新</el-button>
						<el-button size="small" type="primary" v-permission="'coffee:metric:Create'" @click="createMetric">新增口径</el-button>
					</div>
				</div>
			</template>
			<el-form :model="metricForm" label-width="86px" class="metric-form" size="small">
				<el-form-item label="指标编码">
					<el-input v-model="metricForm.metric_code" placeholder="total_events" />
				</el-form-item>
				<el-form-item label="指标名称">
					<el-input v-model="metricForm.metric_name" placeholder="采集事件总数" />
				</el-form-item>
				<el-form-item label="计算口径">
					<el-input v-model="metricForm.calculation_method" placeholder="count(scoped CollectionEvent.id)" />
				</el-form-item>
				<el-form-item label="单位">
					<el-input v-model="metricForm.unit" placeholder="条" />
				</el-form-item>
				<el-form-item label="启停">
					<el-switch v-model="metricForm.enabled" />
				</el-form-item>
			</el-form>
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
						<el-button link type="primary" size="small" v-permission="'coffee:metric:Create'" @click="copyMetricVersion(row)">复制版本</el-button>
					</template>
				</el-table-column>
			</el-table>
			<pre class="json-box compact">{{ progress.metric_definitions }}</pre>
		</el-card>
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
}

onMounted(() => {
	loadStatistics();
	loadMetricDefinitions();
});
</script>

<style scoped>
.coffee-statistics-page {
	display: grid;
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
.panel-actions {
	display: flex;
	align-items: center;
	gap: 8px;
}
.metric-form {
	display: grid;
	grid-template-columns: repeat(5, minmax(0, 1fr));
	gap: 8px;
	margin-bottom: 12px;
}
.metric-form :deep(.el-form-item) {
	margin-bottom: 0;
}
.mini-title {
	margin-bottom: 6px;
	color: #606266;
	font-size: 13px;
}
.json-box {
	overflow: auto;
	margin-top: 12px;
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
</style>
