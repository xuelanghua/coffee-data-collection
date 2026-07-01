<template>
	<fs-page class="coffee-provider-page">
		<el-card shadow="never" class="panel">
			<template #header>
				<div class="panel-header">
					<span>Provider 配置</span>
					<div class="header-actions">
						<el-button @click="loadProviderConfigs()">刷新</el-button>
						<el-button v-permission="'coffee:provider:Create'" type="primary" @click="openProviderDialog()">新增配置</el-button>
					</div>
				</div>
			</template>

			<el-form :inline="true" :model="queryForm" class="filter-form" label-width="96px">
				<el-form-item label="Provider 类型">
					<el-select v-model="queryForm.provider_type" clearable placeholder="全部类型" style="width: 160px">
						<el-option label="地图 Provider" value="map" />
						<el-option label="天气 Provider" value="weather" />
						<el-option label="OCR Provider" value="ocr" />
						<el-option label="存储 Provider" value="storage" />
					</el-select>
				</el-form-item>
				<el-form-item label="启用状态">
					<el-select v-model="queryForm.enabled" clearable placeholder="全部状态" style="width: 140px">
						<el-option label="启用" value="true" />
						<el-option label="停用" value="false" />
					</el-select>
				</el-form-item>
				<el-form-item>
					<el-button type="primary" @click="handleSearch">查询</el-button>
					<el-button @click="handleReset">重置</el-button>
				</el-form-item>
			</el-form>

			<el-table :data="providers" size="small" @row-click="selectProvider">
				<el-table-column prop="provider_type" label="Provider 类型" width="126" />
				<el-table-column prop="provider_name" label="名称" min-width="132" />
				<el-table-column prop="display_name" label="显示名" min-width="132" />
				<el-table-column prop="enabled" label="启用状态" width="100">
					<template #default="{ row }">
						<el-tag :type="row.enabled ? 'success' : 'info'" size="small">{{ row.enabled ? '启用' : '停用' }}</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="priority" label="优先级" width="88" />
				<el-table-column prop="timeout_ms" label="超时" width="92" />
				<el-table-column prop="config_status" label="配置状态" width="112" />
				<el-table-column label="操作" width="260" fixed="right">
					<template #default="{ row }">
						<el-button v-permission="'coffee:provider:Edit'" type="primary" link @click.stop="openProviderDialog(row)">编辑</el-button>
						<el-button v-permission="'coffee:provider:Edit'" type="primary" link @click.stop="openProviderDialog(row, true)">设置密钥</el-button>
						<el-button v-permission="'coffee:provider:Edit'" type="primary" link @click.stop="handleToggle(row)">启停</el-button>
						<el-button v-permission="'coffee:provider:Test'" type="primary" link @click.stop="runConnectionTest(row)">连接测试</el-button>
						<el-button v-permission="'coffee:provider:Delete'" type="primary" link @click.stop="handleDelete(row)">删除</el-button>
					</template>
				</el-table-column>
			</el-table>
		</el-card>

		<el-card shadow="never" class="panel side-panel">
			<template #header>
				<div class="panel-header">
					<span>脱敏 Key</span>
					<el-tag v-if="selectedProvider" size="small">{{ selectedProvider.provider_name }}</el-tag>
				</div>
			</template>
			<el-empty v-if="!selectedProvider" description="请选择 Provider" />
			<template v-else>
				<el-descriptions :column="1" border>
					<el-descriptions-item label="Provider 类型">{{ selectedProvider.provider_type }}</el-descriptions-item>
					<el-descriptions-item label="限流">{{ selectedProvider.rate_limit_per_minute }}/min</el-descriptions-item>
					<el-descriptions-item label="版本">{{ selectedProvider.version }}</el-descriptions-item>
				</el-descriptions>
				<div v-if="selectedProvider.provider_type === 'map'" class="capability-box">
					<div class="capability-title">地图能力</div>
					<el-tag size="small">reverse_geocode</el-tag>
					<el-tag size="small">boundary_polygon</el-tag>
					<el-tag size="small">area_recheck</el-tag>
				</div>
				<pre class="json-box">{{ selectedProvider.masked_config }}</pre>
			</template>
		</el-card>

		<el-dialog v-model="providerDialogVisible" title="配置弹窗" width="720px">
			<el-alert
				class="dialog-help"
				title="配置示例：按 Provider 类型填写 JSON；secret_fields 中列出的字段会在列表和详情中脱敏展示。"
				type="info"
				:closable="false"
				show-icon
			/>
			<el-form :model="providerForm" label-width="120px">
				<el-form-item label="Provider 类型">
					<el-select v-model="providerForm.provider_type" placeholder="请选择">
						<el-option label="地图 Provider" value="map" />
						<el-option label="天气 Provider" value="weather" />
						<el-option label="OCR Provider" value="ocr" />
						<el-option label="存储 Provider" value="storage" />
					</el-select>
				</el-form-item>
				<el-form-item label="名称">
					<el-input v-model.trim="providerForm.provider_name" placeholder="amap / juhe_weather / paddle_ocr" />
				</el-form-item>
				<el-form-item label="显示名">
					<el-input v-model.trim="providerForm.display_name" placeholder="高德地图" />
				</el-form-item>
				<el-form-item label="地图示例">
					<el-tag>腾讯地图</el-tag>
					<el-tag>百度地图</el-tag>
				</el-form-item>
				<el-form-item label="启用状态">
					<el-switch v-model="providerForm.enabled" />
				</el-form-item>
				<el-form-item label="优先级">
					<el-input-number v-model="providerForm.priority" :min="1" :max="999" />
				</el-form-item>
				<el-form-item label="超时 ms">
					<el-input-number v-model="providerForm.timeout_ms" :min="500" :max="60000" :step="500" />
				</el-form-item>
				<el-form-item label="限流 / min">
					<el-input-number v-model="providerForm.rate_limit_per_minute" :min="1" :max="10000" />
				</el-form-item>
				<el-form-item label="密钥字段">
					<el-select v-model="providerForm.secret_fields" multiple allow-create filterable default-first-option placeholder="如 api_key、ak、sk">
						<el-option label="api_key" value="api_key" />
						<el-option label="ak" value="ak" />
						<el-option label="sk" value="sk" />
					</el-select>
				</el-form-item>
				<el-form-item label="设置密钥">
					<el-input v-model="providerConfigText" type="textarea" :rows="8" placeholder='{"endpoint":"https://example.test","api_key":"***"}' />
				</el-form-item>
			</el-form>
			<div class="config-example-grid">
				<div class="config-example">
					<div class="example-title">高德地图示例</div>
					<pre>{
  "endpoint": "https://restapi.amap.com",
  "api_key": "你的高德 Key",
  "coordinate_system": "GCJ02",
  "capabilities": ["reverse_geocode", "boundary_polygon", "area_recheck"]
}</pre>
				</div>
				<div class="config-example">
					<div class="example-title">聚合天气示例</div>
					<pre>{
  "endpoint": "https://apis.juhe.cn/simpleWeather/query",
  "api_key": "你的聚合天气 Key",
  "city": "普洱市"
}</pre>
				</div>
				<div class="config-example">
					<div class="example-title">PaddleOCR 示例</div>
					<pre>{
  "endpoint": "http://127.0.0.1:8868/ocr",
  "template": "device_reading_v1",
  "timeout_ms": 15000
}</pre>
				</div>
			</div>
			<template #footer>
				<el-button @click="providerDialogVisible = false">取消</el-button>
				<el-button type="primary" @click="handleSubmitProvider">保存</el-button>
			</template>
		</el-dialog>
	</fs-page>
</template>

<script lang="ts" setup name="coffeeProvider">
import { onMounted, reactive, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { createProviderConfig, deleteProviderConfig, getProviderConfigs, testProviderConfig, toggleProviderConfig, updateProviderConfig } from '/@/api/coffee/provider';

const providers = ref<any[]>([]);
const selectedProvider = ref<any>(null);
const providerDialogVisible = ref(false);
const editingProviderId = ref<number | null>(null);
const providerConfigText = ref('{}');
const queryForm = reactive({
	provider_type: '',
	enabled: '',
});
const providerForm = reactive({
	provider_type: 'ocr' as 'map' | 'weather' | 'ocr' | 'storage',
	provider_name: '',
	display_name: '',
	enabled: true,
	priority: 50,
	timeout_ms: 3000,
	rate_limit_per_minute: 60,
	config_json: {} as Record<string, any>,
	secret_fields: [] as string[],
});

async function loadProviderConfigs(params: Record<string, any> = activeQueryParams()) {
	const data: any = await getProviderConfigs(params);
	providers.value = data?.results || [];
	if (selectedProvider.value) {
		selectedProvider.value = providers.value.find((item) => item.id === selectedProvider.value.id) || null;
	}
	return data;
}

function activeQueryParams() {
	return Object.fromEntries(Object.entries(queryForm).filter(([, value]) => value));
}

function selectProvider(row: any) {
	selectedProvider.value = row;
}

function resetProviderForm() {
	editingProviderId.value = null;
	Object.assign(providerForm, {
		provider_type: 'ocr',
		provider_name: '',
		display_name: '',
		enabled: true,
		priority: 50,
		timeout_ms: 3000,
		rate_limit_per_minute: 60,
		config_json: {},
		secret_fields: [],
	});
	providerConfigText.value = '{}';
}

function openProviderDialog(row?: any, focusSecret = false) {
	resetProviderForm();
	if (row) {
		editingProviderId.value = row.id;
		Object.assign(providerForm, {
			provider_type: row.provider_type,
			provider_name: row.provider_name,
			display_name: row.display_name,
			enabled: row.enabled,
			priority: row.priority,
			timeout_ms: row.timeout_ms,
			rate_limit_per_minute: row.rate_limit_per_minute,
			config_json: row.masked_config || {},
			secret_fields: row.secret_fields || [],
		});
		providerConfigText.value = JSON.stringify(row.masked_config || {}, null, 2);
	}
	if (focusSecret) {
		ElMessage.info('请在“设置密钥”中填写 JSON 配置，密钥字段保存后列表只展示脱敏值');
	}
	providerDialogVisible.value = true;
}

async function handleSearch() {
	await loadProviderConfigs(activeQueryParams());
}

async function handleReset() {
	queryForm.provider_type = '';
	queryForm.enabled = '';
	await loadProviderConfigs({});
}

function buildProviderPayload() {
	let configJson: Record<string, any> = {};
	try {
		configJson = providerConfigText.value ? JSON.parse(providerConfigText.value) : {};
	} catch (error) {
		ElMessage.error('设置密钥必须是合法 JSON');
		throw error;
	}
	return {
		...providerForm,
		config_json: configJson,
		secret_fields: [...providerForm.secret_fields],
	};
}

async function handleSubmitProvider() {
	const payload = buildProviderPayload();
	if (editingProviderId.value) {
		await updateProviderConfig(editingProviderId.value, payload);
		ElMessage.success('Provider 配置已更新');
	} else {
		await createProviderConfig(payload);
		ElMessage.success('Provider 配置已创建');
	}
	providerDialogVisible.value = false;
	await loadProviderConfigs();
}

async function handleToggle(row: any) {
	await toggleProviderConfig(row.id, !row.enabled);
	await loadProviderConfigs();
	ElMessage.success(row.enabled ? 'Provider 已停用' : 'Provider 已启用');
}

async function handleDelete(row: any) {
	await ElMessageBox.confirm(`确认删除 Provider「${row.display_name || row.provider_name}」？`, '删除确认', { type: 'warning' });
	await deleteProviderConfig(row.id);
	await loadProviderConfigs();
	ElMessage.success('Provider 配置已删除');
}

async function runConnectionTest(row: any) {
	await testProviderConfig(row.id);
	await loadProviderConfigs();
	ElMessage.success('连接测试已完成');
}

onMounted(() => {
	loadProviderConfigs();
});
</script>

<style scoped>
.coffee-provider-page {
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
.config-example-grid {
	display: grid;
	grid-template-columns: repeat(3, minmax(0, 1fr));
	gap: 12px;
}
.config-example {
	min-width: 0;
	padding: 12px;
	background: #f6f8f7;
	border: 1px solid #e2e8e4;
	border-radius: 6px;
}
.example-title {
	margin-bottom: 8px;
	color: #303133;
	font-weight: 600;
}
.config-example pre {
	overflow: auto;
	margin: 0;
	font-size: 12px;
	line-height: 1.5;
	white-space: pre-wrap;
}
.side-panel {
	min-width: 0;
	min-height: 360px;
}
.capability-box {
	display: flex;
	align-items: center;
	flex-wrap: wrap;
	gap: 8px;
	margin-top: 20px;
}
.capability-title {
	font-size: 13px;
	color: #606266;
}
.json-box {
	max-height: 360px;
	overflow: auto;
	margin-top: 20px;
	padding: 12px;
	background: #f6f8f7;
	border: 1px solid #e2e8e4;
	border-radius: 6px;
	white-space: pre-wrap;
}

@media (max-width: 640px) {
	.coffee-provider-page {
		grid-template-columns: minmax(0, 1fr);
		padding: 12px;
	}
}
</style>
