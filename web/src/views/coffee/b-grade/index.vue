<template>
	<fs-page class="coffee-b-grade-page">
		<el-card shadow="never" class="panel">
			<template #header>
				<div class="panel-header">
					<span>B 级规则</span>
					<div>
						<el-button size="small" @click="loadRules">刷新</el-button>
						<el-button type="primary" size="small" @click="createDefaultRule">新增规则</el-button>
					</div>
				</div>
			</template>
			<el-table :data="rules" size="small" @row-click="selectRule">
				<el-table-column prop="rule_code" label="规则编号" min-width="160" />
				<el-table-column prop="rule_name" label="规则名称" min-width="170" />
				<el-table-column prop="task_id" label="任务" min-width="150" />
				<el-table-column prop="metric" label="指标" min-width="150" />
				<el-table-column prop="min_count" label="最小" width="80" />
				<el-table-column prop="max_count" label="最大" width="80" />
				<el-table-column prop="block_level" label="阻断级别" width="110" />
				<el-table-column prop="enabled" label="启用" width="80" />
				<el-table-column label="操作" width="112" fixed="right">
					<template #default="{ row }">
						<el-button type="primary" link @click.stop="simulateRule(row)">模拟检查</el-button>
					</template>
				</el-table-column>
			</el-table>
		</el-card>

		<el-card shadow="never" class="panel result-panel">
			<template #header>
				<span>检查结果</span>
			</template>
			<el-empty v-if="!result" description="请选择规则并模拟检查" />
			<template v-else>
				<el-descriptions :column="3" border>
					<el-descriptions-item label="状态">{{ result.status }}</el-descriptions-item>
					<el-descriptions-item label="实际数量">{{ result.actual_count }}</el-descriptions-item>
					<el-descriptions-item label="阻断">{{ result.blocking ? '是' : '否' }}</el-descriptions-item>
				</el-descriptions>
				<pre class="json-box">{{ result.failed_reasons }}</pre>
			</template>
		</el-card>
	</fs-page>
</template>

<script lang="ts" setup name="coffeeBGrade">
import { onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { checkBGradeRule, createBGradeRule, getBGradeRules } from '/@/api/coffee/b-grade';

const rules = ref<any[]>([]);
const selectedRule = ref<any>(null);
const result = ref<any>(null);

async function loadRules(params: Record<string, any> = {}) {
	const data: any = await getBGradeRules(params);
	rules.value = data?.results || [];
	return data;
}

function selectRule(row: any) {
	selectedRule.value = row;
}

async function createDefaultRule() {
	await createBGradeRule({
		rule_name: 'B级通过数至少1条',
		task_id: 'TASK-DEMO',
		metric: 'approved_event_count',
		min_count: 1,
		block_level: 'blocking',
		enabled: true,
	});
	await loadRules();
	ElMessage.success('B 级规则已创建');
}

async function simulateRule(row: any) {
	result.value = await checkBGradeRule(row.rule_code);
	ElMessage.success('模拟检查完成');
}

onMounted(() => {
	loadRules();
});
</script>

<style scoped>
.coffee-b-grade-page {
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
.result-panel {
	min-height: 180px;
}
.json-box {
	max-height: 180px;
	overflow: auto;
	margin-top: 12px;
	padding: 12px;
	background: #f6f8f7;
	border: 1px solid #e2e8e4;
	border-radius: 6px;
	white-space: pre-wrap;
}
</style>
