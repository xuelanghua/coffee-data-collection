<template>
	<fs-page class="coffee-provider-page">
		<el-card shadow="never" class="panel">
			<template #header>
				<div class="panel-header">
					<span>Provider 配置</span>
					<div class="header-actions">
						<el-button size="small" @click="loadProviderConfigs">刷新</el-button>
						<el-button size="small" @click="loadMapProviders">地图 Provider</el-button>
						<el-button v-permission="'coffee:provider:Create'" type="primary" size="small" @click="createDefaultProvider">新增 Mock 配置</el-button>
						<el-button v-permission="'coffee:provider:Create'" type="success" size="small" @click="createTencentMapProvider">腾讯地图</el-button>
						<el-button v-permission="'coffee:provider:Create'" type="success" size="small" @click="createBaiduMapProvider">百度地图</el-button>
					</div>
				</div>
			</template>
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
				<el-table-column label="操作" width="120" fixed="right">
					<template #default="{ row }">
						<el-button v-permission="'coffee:provider:Test'" type="primary" link @click.stop="runConnectionTest(row)">连接测试</el-button>
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
	</fs-page>
</template>

<script lang="ts" setup name="coffeeProvider">
import { onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { createProviderConfig, getProviderConfigs, testProviderConfig } from '/@/api/coffee/provider';

const providers = ref<any[]>([]);
const selectedProvider = ref<any>(null);

async function loadProviderConfigs(params: Record<string, any> = {}) {
	const data: any = await getProviderConfigs(params);
	providers.value = data?.results || [];
	return data;
}

async function loadMapProviders() {
	return loadProviderConfigs({ provider_type: 'map' });
}

function selectProvider(row: any) {
	selectedProvider.value = row;
}

async function createDefaultProvider() {
	await createProviderConfig({
		provider_type: 'ocr',
		provider_name: 'manual',
		display_name: '人工录入',
		enabled: true,
		priority: 99,
		timeout_ms: 1000,
		rate_limit_per_minute: 60,
		config_json: {},
		secret_fields: [],
	});
	await loadProviderConfigs();
	ElMessage.success('Provider 配置已创建');
}

async function createTencentMapProvider() {
	await createMapProvider('tencent_map', '腾讯地图', 'GCJ02');
}

async function createBaiduMapProvider() {
	await createMapProvider('baidu_map', '百度地图', 'BD09');
}

async function createMapProvider(providerName: string, displayName: string, coordinateSystem: string) {
	await createProviderConfig({
		provider_type: 'map',
		provider_name: providerName,
		display_name: displayName,
		enabled: true,
		priority: 30,
		timeout_ms: 3000,
		rate_limit_per_minute: 120,
		config_json: {
			endpoint: `https://${providerName}.example.test`,
			api_key: `${providerName}-mock-key`,
			coordinate_system: coordinateSystem,
			capabilities: ['reverse_geocode', 'boundary_polygon', 'area_recheck'],
		},
		secret_fields: ['api_key'],
	});
	await loadMapProviders();
	ElMessage.success(`${displayName} Provider 已创建`);
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
	grid-template-columns: minmax(0, 1fr) 360px;
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
.header-actions {
	display: flex;
	align-items: center;
	gap: 8px;
	flex-wrap: wrap;
	justify-content: flex-end;
}
.side-panel {
	min-width: 0;
}
.capability-box {
	display: flex;
	align-items: center;
	flex-wrap: wrap;
	gap: 8px;
	margin-top: 12px;
}
.capability-title {
	font-size: 13px;
	color: #606266;
}
.json-box {
	max-height: 360px;
	overflow: auto;
	margin-top: 12px;
	padding: 12px;
	background: #f6f8f7;
	border: 1px solid #e2e8e4;
	border-radius: 6px;
	white-space: pre-wrap;
}
</style>
