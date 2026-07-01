<template>
	<fs-page class="coffee-photo-page">
		<el-card shadow="never" class="panel">
			<template #header>
				<div class="panel-header">
					<span>照片资产</span>
					<el-button @click="loadPhotoList">刷新</el-button>
				</div>
			</template>
			<el-form :inline="true" :model="queryForm" class="filter-form" label-width="78px">
				<el-form-item label="审核状态">
					<el-select v-model="queryForm.review_status" clearable placeholder="全部" style="width: 130px">
						<el-option label="待审核" value="pending" />
						<el-option label="已通过" value="approved" />
						<el-option label="已退回" value="returned" />
					</el-select>
				</el-form-item>
				<el-form-item label="Event_ID">
					<el-input v-model.trim="queryForm.event_id" clearable placeholder="EV..." style="width: 160px" />
				</el-form-item>
				<el-form-item label="分类">
					<el-input v-model.trim="queryForm.category" clearable placeholder="device_panel" style="width: 150px" />
				</el-form-item>
				<el-form-item>
					<el-button type="primary" @click="handleSearch">查询</el-button>
					<el-button @click="handleReset">重置</el-button>
				</el-form-item>
			</el-form>
			<el-table :data="photos" size="small" @row-click="selectPhoto">
				<el-table-column prop="photo_id" label="Photo_ID" min-width="150" />
				<el-table-column prop="event_id" label="Event_ID" min-width="150" />
				<el-table-column prop="category" label="分类" width="126" />
				<el-table-column prop="sha256" label="原图 Hash" min-width="160" />
				<el-table-column prop="precheck_status" label="预检" width="116" />
				<el-table-column prop="review_status" label="审核状态" width="116" />
				<el-table-column prop="latest_ocr_status" label="OCR" width="100" />
				<el-table-column label="操作" width="180" fixed="right">
					<template #default="{ row }">
						<el-button v-permission="'coffee:photo:Approve'" type="primary" link @click.stop="openReviewDialog(row, 'approved')">审核通过</el-button>
						<el-button v-permission="'coffee:photo:Return'" type="primary" link @click.stop="openReviewDialog(row, 'returned')">退回补拍</el-button>
					</template>
				</el-table-column>
			</el-table>
		</el-card>

		<el-card shadow="never" class="panel side-panel">
			<template #header>
				<div class="panel-header">
					<span>metadata</span>
					<el-tag v-if="selectedPhoto" size="small">{{ selectedPhoto.photo_id }}</el-tag>
				</div>
			</template>
			<el-empty v-if="!selectedPhoto" description="请选择照片" />
			<template v-else>
				<el-descriptions :column="2" border>
					<el-descriptions-item label="Event_ID">{{ selectedPhoto.event_id }}</el-descriptions-item>
					<el-descriptions-item label="Plot_ID">{{ selectedPhoto.plot_id }}</el-descriptions-item>
					<el-descriptions-item label="Point_ID">{{ selectedPhoto.point_id }}</el-descriptions-item>
					<el-descriptions-item label="不可变">{{ selectedPhoto.immutable_status }}</el-descriptions-item>
				</el-descriptions>
				<pre class="json-box">{{ selectedPhoto.metadata }}</pre>
				<el-divider>人工标注</el-divider>
				<div class="annotation-toolbar">
					<el-tag size="small">拖拽框选</el-tag>
					<span>在图片上按住并拖出矩形框，系统自动生成 bbox 几何。</span>
				</div>
				<div
					class="annotation-canvas"
					@mousedown="startBoxAnnotation"
					@mousemove="moveBoxAnnotation"
					@mouseup="finishBoxAnnotation"
					@mouseleave="finishBoxAnnotation"
				>
					<img
						v-if="selectedPhoto.original_file"
						class="annotation-image"
						:src="selectedPhoto.original_file"
						:alt="selectedPhoto.photo_id"
						draggable="false"
						@load="captureNaturalImageSize"
					/>
					<div v-else class="annotation-image-placeholder">暂无原图预览</div>
					<div
						v-for="item in annotationBoxes"
						:key="`${item.annotation_id}-${item.version}`"
						class="annotation-box saved"
						:style="boxStyle(displayBoxFor(item.geometry))"
					>
						{{ item.label }} v{{ item.version }}
					</div>
					<div v-if="draftBox" class="annotation-box draft" :style="boxStyle(draftBox)" />
				</div>
				<el-form :model="annotationForm" label-width="78px" size="small" class="annotation-form">
					<el-form-item label="标注ID">
						<el-input v-model="annotationForm.annotation_id" placeholder="留空创建新标注，填入则追加版本" clearable />
					</el-form-item>
					<el-form-item label="标签">
						<el-input v-model="annotationForm.label" placeholder="如 coffee_cherry" />
					</el-form-item>
					<el-form-item label="形状">
						<el-select v-model="annotationForm.shape_type">
							<el-option label="矩形框" value="bbox" />
							<el-option label="多边形" value="polygon" />
							<el-option label="点" value="point" />
						</el-select>
					</el-form-item>
					<el-form-item label="几何">
						<el-input v-model="annotationGeometryText" type="textarea" :rows="4" placeholder='{"x":10,"y":20,"width":80,"height":64}' />
					</el-form-item>
					<el-alert
						class="dialog-help"
						title='标注几何示例：{"display_box":{"x":10,"y":20,"width":80,"height":64},"natural_box":{"x":120,"y":240,"width":960,"height":768}}。拖拽框选会自动生成。'
						type="info"
						:closable="false"
						show-icon
					/>
					<el-form-item label="备注">
						<el-input v-model="annotationForm.note" />
					</el-form-item>
					<el-button v-permission="'coffee:photo:Annotate'" type="primary" @click="saveAnnotation">保存标注</el-button>
				</el-form>
				<el-table :data="annotations" size="small" class="annotation-table" @row-click="selectAnnotationVersion">
					<el-table-column prop="annotation_id" label="标注ID" min-width="138" />
					<el-table-column prop="label" label="标签" min-width="112" />
					<el-table-column prop="shape_type" label="形状" width="86" />
					<el-table-column prop="version" label="版本" width="72" />
					<el-table-column prop="is_latest" label="最新" width="72" />
				</el-table>
			</template>
		</el-card>
		<el-dialog v-model="reviewDialogVisible" title="审核弹窗" width="520px">
			<el-alert
				class="dialog-help"
				title="审核说明示例：照片清晰，水印、定位和 metadata 完整；退回示例：照片模糊或设备面板反光，请补拍。"
				type="info"
				:closable="false"
				show-icon
			/>
			<el-form :model="reviewForm" label-width="92px">
				<el-form-item label="审核状态">
					<el-radio-group v-model="reviewForm.status">
						<el-radio-button label="approved">通过</el-radio-button>
						<el-radio-button label="returned">退回</el-radio-button>
					</el-radio-group>
				</el-form-item>
				<el-form-item label="退回原因" v-if="reviewForm.status === 'returned'">
					<el-input v-model="reviewForm.return_reason" placeholder="PHOTO_RETAKE_REQUIRED" />
				</el-form-item>
				<el-form-item label="退回项" v-if="reviewForm.status === 'returned'">
					<el-select v-model="reviewForm.return_items" multiple placeholder="请选择">
						<el-option label="照片质量" value="photo_quality" />
						<el-option label="水印" value="watermark" />
						<el-option label="metadata" value="metadata" />
					</el-select>
				</el-form-item>
				<el-form-item label="审核说明">
					<el-input v-model="reviewForm.review_note" type="textarea" :rows="3" />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="reviewDialogVisible = false">取消</el-button>
				<el-button type="primary" @click="submitPhotoReview">提交</el-button>
			</template>
		</el-dialog>
	</fs-page>
</template>

<script lang="ts" setup name="coffeePhoto">
import { computed, onMounted, reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { getPhotoAnnotations, getPhotoList, reviewPhoto, savePhotoAnnotation } from '/@/api/coffee/photo';

const photos = ref<any[]>([]);
const selectedPhoto = ref<any>(null);
const reviewingPhoto = ref<any>(null);
const reviewDialogVisible = ref(false);
const annotations = ref<any[]>([]);
const annotationGeometryText = ref('{"x":10,"y":20,"width":80,"height":64}');
const dragStart = ref<{ x: number; y: number } | null>(null);
const draftBox = ref<Record<string, number> | null>(null);
const imageMetrics = ref({
	naturalWidth: 0,
	naturalHeight: 0,
	displayWidth: 0,
	displayHeight: 0,
});
const annotationForm = ref({
	annotation_id: '',
	label: '',
	shape_type: 'bbox',
	note: '',
});
const queryForm = reactive({
	review_status: '',
	event_id: '',
	category: '',
});
const reviewForm = reactive({
	status: 'approved' as 'approved' | 'returned',
	review_note: '照片清晰，水印和 metadata 完整',
	return_reason: 'PHOTO_RETAKE_REQUIRED',
	return_items: ['photo_quality'] as string[],
});
const annotationBoxes = computed(() => annotations.value.filter((item) => item.shape_type === 'bbox' && item.geometry));

async function loadPhotoList(params: Record<string, any> = activeQueryParams()) {
	const data: any = await getPhotoList(params);
	photos.value = data?.results || [];
	return data;
}

function activeQueryParams() {
	return Object.fromEntries(Object.entries(queryForm).filter(([, value]) => value));
}

async function handleSearch() {
	await loadPhotoList(activeQueryParams());
}

async function handleReset() {
	queryForm.review_status = '';
	queryForm.event_id = '';
	queryForm.category = '';
	await loadPhotoList({});
}

function selectPhoto(row: any) {
	selectedPhoto.value = row;
	loadPhotoAnnotations(row.photo_id);
}

async function loadPhotoAnnotations(photoId: string) {
	const data: any = await getPhotoAnnotations(photoId);
	annotations.value = data?.results || [];
	return data;
}

function selectAnnotationVersion(row: any) {
	annotationForm.value = {
		annotation_id: row.annotation_id,
		label: row.label,
		shape_type: row.shape_type,
		note: row.note || '',
	};
	annotationGeometryText.value = JSON.stringify(row.geometry || {}, null, 2);
	draftBox.value = row.shape_type === 'bbox' ? displayBoxFor(row.geometry) : null;
}

function captureNaturalImageSize(event: Event) {
	const image = event.target as HTMLImageElement;
	imageMetrics.value = {
		naturalWidth: image.naturalWidth,
		naturalHeight: image.naturalHeight,
		displayWidth: image.clientWidth,
		displayHeight: image.clientHeight,
	};
}

function getCanvasPoint(event: MouseEvent) {
	const target = event.currentTarget as HTMLElement;
	const rect = target.getBoundingClientRect();
	return {
		x: Math.max(0, Math.min(rect.width, event.clientX - rect.left)),
		y: Math.max(0, Math.min(rect.height, event.clientY - rect.top)),
	};
}

function updateAnnotationGeometryFromCanvas(box: Record<string, number>) {
	annotationForm.value.shape_type = 'bbox';
	annotationGeometryText.value = JSON.stringify(
		{
			display_box: box,
			natural_box: toNaturalBox(box),
			naturalWidth: imageMetrics.value.naturalWidth,
			naturalHeight: imageMetrics.value.naturalHeight,
		},
		null,
		2
	);
}

function toNaturalBox(box: Record<string, number>) {
	const { naturalWidth, naturalHeight, displayWidth, displayHeight } = imageMetrics.value;
	if (!naturalWidth || !naturalHeight || !displayWidth || !displayHeight) return box;
	const scaleX = naturalWidth / displayWidth;
	const scaleY = naturalHeight / displayHeight;
	return {
		x: Math.round(box.x * scaleX),
		y: Math.round(box.y * scaleY),
		width: Math.round(box.width * scaleX),
		height: Math.round(box.height * scaleY),
	};
}

function startBoxAnnotation(event: MouseEvent) {
	const point = getCanvasPoint(event);
	dragStart.value = point;
	draftBox.value = { x: point.x, y: point.y, width: 0, height: 0 };
}

function moveBoxAnnotation(event: MouseEvent) {
	if (!dragStart.value) return;
	const point = getCanvasPoint(event);
	const x = Math.min(dragStart.value.x, point.x);
	const y = Math.min(dragStart.value.y, point.y);
	const width = Math.abs(point.x - dragStart.value.x);
	const height = Math.abs(point.y - dragStart.value.y);
	draftBox.value = { x: Math.round(x), y: Math.round(y), width: Math.round(width), height: Math.round(height) };
}

function finishBoxAnnotation() {
	if (!dragStart.value || !draftBox.value) return;
	dragStart.value = null;
	if (draftBox.value.width < 4 || draftBox.value.height < 4) return;
	updateAnnotationGeometryFromCanvas(draftBox.value);
}

function boxStyle(box: Record<string, any>) {
	return {
		left: `${box.x || 0}px`,
		top: `${box.y || 0}px`,
		width: `${box.width || 0}px`,
		height: `${box.height || 0}px`,
	};
}

function displayBoxFor(geometry: Record<string, any>) {
	return geometry?.display_box || geometry;
}

async function saveAnnotation() {
	if (!selectedPhoto.value) return;
	const geometry = JSON.parse(annotationGeometryText.value || '{}');
	await savePhotoAnnotation(selectedPhoto.value.photo_id, {
		annotation_id: annotationForm.value.annotation_id || undefined,
		label: annotationForm.value.label,
		shape_type: annotationForm.value.shape_type as 'bbox' | 'polygon' | 'point',
		geometry,
		note: annotationForm.value.note,
	});
	await loadPhotoAnnotations(selectedPhoto.value.photo_id);
	ElMessage.success('保存标注版本成功');
}

function openReviewDialog(row: any, status: 'approved' | 'returned') {
	reviewingPhoto.value = row;
	reviewForm.status = status;
	reviewForm.review_note = status === 'approved' ? '照片清晰，水印和 metadata 完整' : '退回补拍';
	reviewDialogVisible.value = true;
}

async function submitPhotoReview() {
	if (!reviewingPhoto.value) return;
	if (reviewForm.status === 'approved') await approvePhoto(reviewingPhoto.value);
	if (reviewForm.status === 'returned') await returnPhoto(reviewingPhoto.value);
	reviewDialogVisible.value = false;
}

async function approvePhoto(row: any) {
	await reviewPhoto(row.photo_id, {
		status: 'approved',
		review_note: reviewForm.review_note,
	});
	await loadPhotoList();
	ElMessage.success('照片审核通过');
}

async function returnPhoto(row: any) {
	await reviewPhoto(row.photo_id, {
		status: 'returned',
		return_reason: reviewForm.return_reason,
		return_items: reviewForm.return_items,
		review_note: reviewForm.review_note,
	});
	await loadPhotoList();
	ElMessage.success('已退回补拍');
}

onMounted(() => {
	loadPhotoList();
});
</script>

<style scoped>
.coffee-photo-page {
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
.side-panel {
	min-width: 0;
	min-height: 360px;
}
.json-box {
	max-height: 420px;
	overflow: auto;
	margin-top: 20px;
	padding: 12px;
	background: #f6f8f7;
	border: 1px solid #e2e8e4;
	border-radius: 6px;
	white-space: pre-wrap;
}
.annotation-toolbar {
	display: flex;
	align-items: center;
	gap: 8px;
	margin-top: 12px;
	font-size: 12px;
	color: #64706b;
}
.annotation-canvas {
	position: relative;
	height: 240px;
	margin-top: 10px;
	overflow: hidden;
	background: #101815;
	border: 1px solid #d8e0dc;
	border-radius: 6px;
	user-select: none;
	cursor: crosshair;
}
.annotation-image,
.annotation-image-placeholder {
	width: 100%;
	height: 100%;
	object-fit: contain;
	display: flex;
	align-items: center;
	justify-content: center;
	color: #d7e6df;
}
.annotation-box {
	position: absolute;
	box-sizing: border-box;
	border: 2px solid #32d583;
	background: rgba(50, 213, 131, 0.08);
	color: #083b24;
	font-size: 11px;
	line-height: 16px;
	padding: 0 4px;
	pointer-events: none;
}
.annotation-box.saved {
	border-color: #4c8dff;
	background: rgba(76, 141, 255, 0.1);
	color: #f6fbff;
}
.annotation-box.draft {
	border-color: #32d583;
	background: rgba(50, 213, 131, 0.14);
}
.annotation-form {
	margin-top: 12px;
}
.annotation-table {
	margin-top: 12px;
}

@media (max-width: 640px) {
	.coffee-photo-page {
		grid-template-columns: minmax(0, 1fr);
		padding: 12px;
	}
}
</style>
