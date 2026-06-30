<template>
	<fs-page class="coffee-event-page">
		<el-row :gutter="16">
			<el-col :span="9">
				<el-card shadow="never" class="panel">
					<template #header>
						<div class="panel-header">
							<span>采集事件</span>
							<div>
								<el-button v-permission="'coffee:event:BulkApprove'" type="success" size="small" @click="handleBulkApprove">批量通过</el-button>
								<el-button v-permission="'coffee:event:BulkReturn'" type="warning" size="small" @click="handleBulkReturn">批量退回</el-button>
							</div>
						</div>
					</template>
					<el-table :data="events" size="small" @selection-change="handleSelectionChange">
						<el-table-column type="selection" width="42" />
						<el-table-column prop="event_id" label="Event_ID" min-width="148" />
						<el-table-column prop="plot_id" label="Plot_ID" min-width="132" />
						<el-table-column prop="point_id" label="Point_ID" min-width="132" />
						<el-table-column prop="status" label="状态" width="92" />
						<el-table-column label="操作" width="86" fixed="right">
							<template #default="{ row }">
								<el-button type="primary" link @click="loadDetail(row.event_id)">详情</el-button>
							</template>
						</el-table-column>
					</el-table>
				</el-card>
			</el-col>
			<el-col :span="15">
				<el-card shadow="never" class="panel">
					<template #header>
						<div class="panel-header">
							<span>单条数据详情</span>
							<div v-if="detail.event">
								<el-button v-permission="'coffee:event:Approve'" type="success" size="small" @click="handleApprove">通过</el-button>
								<el-button v-permission="'coffee:event:Return'" type="warning" size="small" @click="handleReturn">退回</el-button>
							</div>
						</div>
					</template>

					<el-empty v-if="!detail.event" description="请选择一条采集事件" />
					<el-tabs v-else v-model="activeTab">
						<el-tab-pane label="基础信息" name="base">
							<el-descriptions :column="2" border>
								<el-descriptions-item label="Event_ID">{{ detail.event.event_id }}</el-descriptions-item>
								<el-descriptions-item label="状态">{{ detail.event.status }}</el-descriptions-item>
								<el-descriptions-item label="Plot_ID">{{ detail.plot?.plot_id }}</el-descriptions-item>
								<el-descriptions-item label="Point_ID">{{ detail.point?.point_id }}</el-descriptions-item>
							</el-descriptions>
						</el-tab-pane>
						<el-tab-pane label="地块信息" name="plot">
							<pre class="json-box">{{ detail.plot }}</pre>
						</el-tab-pane>
						<el-tab-pane label="图片资料" name="photos">
							<el-table :data="detail.photos || []" size="small">
								<el-table-column prop="photo_id" label="Photo_ID" min-width="150" />
								<el-table-column prop="category" label="分类" width="120" />
								<el-table-column prop="precheck_status" label="预检" width="120" />
								<el-table-column prop="review_status" label="审核" width="120" />
							</el-table>
						</el-tab-pane>
						<el-tab-pane label="OCR 识别" name="ocr">
							<el-table :data="detail.ocr_results || []" size="small">
								<el-table-column prop="ocr_result_id" label="OCR_ID" min-width="170" />
								<el-table-column prop="photo_id" label="Photo_ID" min-width="150" />
								<el-table-column prop="provider" label="Provider" width="120" />
								<el-table-column prop="confidence" label="置信度" width="100" />
							</el-table>
						</el-tab-pane>
						<el-tab-pane label="设备采集数据" name="measurements">
							<el-table :data="detail.measurements || []" size="small">
								<el-table-column prop="device_no" label="设备编号" width="120" />
								<el-table-column prop="wind_speed" label="风速" width="90" />
								<el-table-column prop="wind_direction" label="风向" width="90" />
								<el-table-column prop="air_temperature" label="空气温度" width="110" />
								<el-table-column prop="air_humidity" label="空气湿度" width="110" />
								<el-table-column prop="atmospheric_pressure" label="大气压力" width="110" />
								<el-table-column prop="rainfall" label="雨量" width="90" />
								<el-table-column prop="soil_moisture" label="土壤湿度" width="110" />
								<el-table-column prop="soil_temperature" label="土壤温度" width="110" />
								<el-table-column prop="soil_salinity" label="土壤盐分" width="110" />
								<el-table-column prop="soil_ph" label="土壤 PH 值" width="110" />
							</el-table>
						</el-tab-pane>
						<el-tab-pane label="质检记录" name="reviews">
							<el-table :data="detail.quality_reviews || []" size="small">
								<el-table-column prop="status" label="状态" width="110" />
								<el-table-column prop="return_reason" label="退回原因" min-width="160" />
								<el-table-column prop="version" label="版本" width="80" />
							</el-table>
						</el-tab-pane>
					</el-tabs>
				</el-card>
			</el-col>
		</el-row>
	</fs-page>
</template>

<script lang="ts" setup name="coffeeEvent">
import { onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { approveEvent, bulkApproveEvents, bulkReturnEvents, getEventDetail, getEventList, returnEvent } from '/@/api/coffee/event';

const activeTab = ref('base');
const selectedEventIds = ref<string[]>([]);
const detail = ref<any>({});
const events = ref<any[]>([]);

async function loadEventList(params: Record<string, any> = {}) {
	const data: any = await getEventList(params);
	events.value = data?.results || [];
	return data;
}

function handleSelectionChange(selection: any[]) {
	selectedEventIds.value = selection.map((item) => item.event_id);
}

async function loadDetail(eventId: string) {
	detail.value = await getEventDetail(eventId);
}

async function handleApprove() {
	if (!detail.value?.event?.event_id) return;
	await approveEvent(detail.value.event.event_id, 'Web 单条审核通过');
	ElMessage.success('审核通过');
}

async function handleReturn() {
	if (!detail.value?.event?.event_id) return;
	await returnEvent(detail.value.event.event_id, {
		return_reason: 'PHOTO_OR_OCR_REVIEW',
		return_note: '请按退回项补充修正',
		return_items: ['photo', 'ocr'],
	});
	ElMessage.success('已退回');
}

async function handleBulkApprove() {
	if (!selectedEventIds.value.length) return;
	await bulkApproveEvents(selectedEventIds.value, 'Web 批量审核通过');
	await loadEventList();
	ElMessage.success('批量通过已提交');
}

async function handleBulkReturn() {
	if (!selectedEventIds.value.length) return;
	await bulkReturnEvents(selectedEventIds.value, {
		return_reason: 'BATCH_REVIEW_RETURN',
		return_note: '批量退回补充说明',
		return_items: ['photo', 'measurement'],
	});
	await loadEventList();
	ElMessage.success('批量退回已提交');
}

onMounted(() => {
	loadEventList();
});
</script>

<style scoped>
.coffee-event-page {
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
.json-box {
	max-height: 360px;
	overflow: auto;
	padding: 12px;
	background: #f6f8f7;
	border: 1px solid #e2e8e4;
	border-radius: 6px;
	white-space: pre-wrap;
}
</style>
