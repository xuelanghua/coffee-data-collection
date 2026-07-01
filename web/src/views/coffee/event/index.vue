<template>
	<fs-page class="coffee-event-page">
		<el-row :gutter="20">
			<el-col :span="9">
				<el-card shadow="never" class="panel">
					<template #header>
						<div class="panel-header">
							<span>采集事件</span>
							<div class="header-actions">
								<el-button @click="loadEventList()">刷新</el-button>
								<el-button v-permission="'coffee:event:BulkApprove'" type="primary" @click="openReviewDialog('bulk-approve')">批量通过</el-button>
								<el-button v-permission="'coffee:event:BulkReturn'" type="primary" @click="openReviewDialog('bulk-return')">批量退回</el-button>
							</div>
						</div>
					</template>
					<el-form :inline="true" :model="queryForm" class="filter-form" label-width="72px">
						<el-form-item label="状态">
							<el-select v-model="queryForm.status" clearable placeholder="全部" style="width: 120px">
								<el-option label="已提交" value="submitted" />
								<el-option label="已通过" value="approved" />
								<el-option label="已退回" value="returned" />
							</el-select>
						</el-form-item>
						<el-form-item label="任务">
							<el-input v-model.trim="queryForm.task_id" clearable placeholder="TASK" style="width: 140px" />
						</el-form-item>
						<el-form-item>
							<el-button type="primary" @click="handleSearch">查询</el-button>
							<el-button @click="handleReset">重置</el-button>
						</el-form-item>
					</el-form>
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
								<el-button v-permission="'coffee:event:Approve'" type="primary" @click="openReviewDialog('approve')">通过</el-button>
								<el-button v-permission="'coffee:event:Return'" type="primary" @click="openReviewDialog('return')">退回</el-button>
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
		<el-dialog v-model="reviewDialogVisible" title="审核弹窗" width="560px">
			<el-form :model="reviewForm" label-width="92px">
				<el-form-item label="审核说明" v-if="reviewMode === 'approve' || reviewMode === 'bulk-approve'">
					<el-input v-model="reviewForm.review_note" type="textarea" :rows="3" placeholder="请输入审核说明" />
				</el-form-item>
				<template v-else>
					<el-alert
						class="dialog-help"
						title="退回项说明：photo=照片资料，ocr=OCR 校正，measurement=设备采集数据，plot=地块信息。示例：照片模糊、OCR 数值异常时选择 photo 和 ocr。"
						type="info"
						:closable="false"
						show-icon
					/>
					<el-form-item label="退回原因">
						<el-input v-model="reviewForm.return_reason" placeholder="PHOTO_OR_OCR_REVIEW" />
					</el-form-item>
					<el-form-item label="退回项">
						<el-select v-model="reviewForm.return_items" multiple placeholder="请选择退回项">
							<el-option label="照片资料" value="photo" />
							<el-option label="OCR 校正" value="ocr" />
							<el-option label="设备采集数据" value="measurement" />
							<el-option label="地块信息" value="plot" />
						</el-select>
					</el-form-item>
					<el-form-item label="退回说明">
						<el-input v-model="reviewForm.return_note" type="textarea" :rows="3" placeholder="请说明需要补充或复核的内容" />
					</el-form-item>
				</template>
			</el-form>
			<template #footer>
				<el-button @click="reviewDialogVisible = false">取消</el-button>
				<el-button type="primary" @click="submitReviewDialog">提交</el-button>
			</template>
		</el-dialog>
	</fs-page>
</template>

<script lang="ts" setup name="coffeeEvent">
import { onMounted, reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { approveEvent, bulkApproveEvents, bulkReturnEvents, getEventDetail, getEventList, returnEvent } from '/@/api/coffee/event';

const activeTab = ref('base');
const selectedEventIds = ref<string[]>([]);
const detail = ref<any>({});
const events = ref<any[]>([]);
const reviewDialogVisible = ref(false);
const reviewMode = ref<'approve' | 'return' | 'bulk-approve' | 'bulk-return'>('approve');
const queryForm = reactive({
	status: '',
	task_id: '',
});
const reviewForm = reactive({
	review_note: 'Web 审核通过',
	return_reason: 'PHOTO_OR_OCR_REVIEW',
	return_note: '请按退回项补充修正',
	return_items: ['photo', 'ocr'] as string[],
});

async function loadEventList(params: Record<string, any> = activeQueryParams()) {
	const data: any = await getEventList(params);
	events.value = data?.results || [];
	return data;
}

function activeQueryParams() {
	return Object.fromEntries(Object.entries(queryForm).filter(([, value]) => value));
}

function handleSelectionChange(selection: any[]) {
	selectedEventIds.value = selection.map((item) => item.event_id);
}

async function loadDetail(eventId: string) {
	detail.value = await getEventDetail(eventId);
}

function openReviewDialog(mode: 'approve' | 'return' | 'bulk-approve' | 'bulk-return') {
	if ((mode === 'approve' || mode === 'return') && !detail.value?.event?.event_id) return;
	if ((mode === 'bulk-approve' || mode === 'bulk-return') && !selectedEventIds.value.length) {
		ElMessage.warning('请先选择需要审核的数据');
		return;
	}
	reviewMode.value = mode;
	reviewDialogVisible.value = true;
}

async function submitReviewDialog() {
	if (reviewMode.value === 'approve') await handleApprove();
	if (reviewMode.value === 'return') await handleReturn();
	if (reviewMode.value === 'bulk-approve') await handleBulkApprove();
	if (reviewMode.value === 'bulk-return') await handleBulkReturn();
	reviewDialogVisible.value = false;
}

async function handleSearch() {
	await loadEventList(activeQueryParams());
}

async function handleReset() {
	queryForm.status = '';
	queryForm.task_id = '';
	await loadEventList({});
}

async function handleApprove() {
	if (!detail.value?.event?.event_id) return;
	await approveEvent(detail.value.event.event_id, reviewForm.review_note);
	ElMessage.success('审核通过');
}

async function handleReturn() {
	if (!detail.value?.event?.event_id) return;
	await returnEvent(detail.value.event.event_id, {
		return_reason: reviewForm.return_reason,
		return_note: reviewForm.return_note,
		return_items: reviewForm.return_items,
	});
	ElMessage.success('已退回');
}

async function handleBulkApprove() {
	if (!selectedEventIds.value.length) return;
	await bulkApproveEvents(selectedEventIds.value, reviewForm.review_note);
	await loadEventList();
	ElMessage.success('批量通过已提交');
}

async function handleBulkReturn() {
	if (!selectedEventIds.value.length) return;
	await bulkReturnEvents(selectedEventIds.value, {
		return_reason: reviewForm.return_reason,
		return_note: reviewForm.return_note,
		return_items: reviewForm.return_items,
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
	padding: 20px;
}
.panel {
	border-radius: 6px;
}
.panel-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 20px;
}
.header-actions {
	display: flex;
	align-items: center;
	gap: 8px;
	flex-wrap: wrap;
	justify-content: flex-end;
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
