<template>
	<fs-page class="coffee-b-grade-page">
		<el-card shadow="never" class="panel">
			<template #header>
				<div class="panel-header">
					<span>B 级规则</span>
					<div class="header-actions">
						<el-button @click="loadRules()">刷新</el-button>
						<el-button v-permission="'coffee:b-grade:Create'" type="primary" @click="openRuleDialog()">新增规则</el-button>
					</div>
				</div>
			</template>

			<el-form :inline="true" :model="queryForm" class="filter-form" label-width="84px">
				<el-form-item label="任务编号">
					<el-input v-model.trim="queryForm.task_id" clearable placeholder="TASK202606250001" style="width: 190px" />
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

			<el-table :data="rules" size="small" @row-click="selectRule">
				<el-table-column prop="rule_code" label="规则编号" min-width="160" />
				<el-table-column prop="rule_name" label="规则名称" min-width="170" />
				<el-table-column prop="task_id" label="任务" min-width="150" />
				<el-table-column prop="metric" label="指标" min-width="150" />
				<el-table-column prop="min_count" label="最小" width="80" />
				<el-table-column prop="max_count" label="最大" width="80" />
				<el-table-column prop="block_level" label="阻断级别" width="110" />
				<el-table-column prop="enabled" label="启用" width="80">
					<template #default="{ row }">
						<el-tag :type="row.enabled ? 'success' : 'info'" size="small">{{ row.enabled ? '启用' : '停用' }}</el-tag>
					</template>
				</el-table-column>
				<el-table-column label="操作" width="230" fixed="right">
					<template #default="{ row }">
						<el-button v-permission="'coffee:b-grade:Check'" type="primary" link @click.stop="simulateRule(row)">模拟检查</el-button>
						<el-button v-permission="'coffee:b-grade:Edit'" type="primary" link @click.stop="openRuleDialog(row)">编辑</el-button>
						<el-button v-permission="'coffee:b-grade:Edit'" type="primary" link @click.stop="handleToggle(row)">启停</el-button>
						<el-button v-permission="'coffee:b-grade:Delete'" type="primary" link @click.stop="handleDelete(row)">删除</el-button>
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

		<el-dialog v-model="ruleDialogVisible" title="规则弹窗" width="640px">
			<el-alert
				class="dialog-help"
				title="规则配置说明：最小数量和最大数量至少填写一个；阻断表示不满足时不能通过，警告表示记录风险但可继续；保存后可先用模拟检查验证。"
				type="info"
				:closable="false"
				show-icon
			/>
			<el-form :model="ruleForm" label-width="108px">
				<el-form-item label="规则名称">
					<el-input v-model.trim="ruleForm.rule_name" placeholder="B级通过数至少2条" />
				</el-form-item>
				<el-form-item label="任务编号">
					<el-input v-model.trim="ruleForm.task_id" placeholder="TASK202606250001" />
				</el-form-item>
				<el-form-item label="指标">
					<el-select v-model="ruleForm.metric">
						<el-option label="通过事件数量" value="approved_event_count" />
						<el-option label="退回事件数量" value="returned_event_count" />
						<el-option label="已提交事件数量" value="submitted_event_count" />
					</el-select>
				</el-form-item>
				<el-form-item label="最小数量">
					<el-input-number v-model="ruleForm.min_count" :min="0" />
				</el-form-item>
				<el-form-item label="最大数量">
					<el-input-number v-model="ruleForm.max_count" :min="0" />
				</el-form-item>
				<el-form-item label="阻断级别">
					<el-radio-group v-model="ruleForm.block_level">
						<el-radio-button label="blocking">阻断</el-radio-button>
						<el-radio-button label="warning">警告</el-radio-button>
					</el-radio-group>
				</el-form-item>
				<el-form-item label="启停">
					<el-switch v-model="ruleForm.enabled" />
				</el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="ruleDialogVisible = false">取消</el-button>
				<el-button type="primary" @click="handleSubmitRule">保存</el-button>
			</template>
		</el-dialog>
	</fs-page>
</template>

<script lang="ts" setup name="coffeeBGrade">
import { onMounted, reactive, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { checkBGradeRule, createBGradeRule, deleteBGradeRule, getBGradeRules, toggleBGradeRule, updateBGradeRule } from '/@/api/coffee/b-grade';

const rules = ref<any[]>([]);
const selectedRule = ref<any>(null);
const result = ref<any>(null);
const ruleDialogVisible = ref(false);
const editingRuleCode = ref('');
const queryForm = reactive({
	task_id: '',
	enabled: '',
});
const ruleForm = reactive({
	rule_name: '',
	task_id: '',
	metric: 'approved_event_count' as 'approved_event_count' | 'returned_event_count' | 'submitted_event_count',
	min_count: 1 as number | undefined,
	max_count: undefined as number | undefined,
	block_level: 'blocking' as 'blocking' | 'warning',
	enabled: true,
});

async function loadRules(params: Record<string, any> = activeQueryParams()) {
	const data: any = await getBGradeRules(params);
	rules.value = data?.results || [];
	return data;
}

function activeQueryParams() {
	return Object.fromEntries(Object.entries(queryForm).filter(([, value]) => value));
}

function selectRule(row: any) {
	selectedRule.value = row;
}

function resetRuleForm() {
	editingRuleCode.value = '';
	Object.assign(ruleForm, {
		rule_name: '',
		task_id: '',
		metric: 'approved_event_count',
		min_count: 1,
		max_count: undefined,
		block_level: 'blocking',
		enabled: true,
	});
}

function openRuleDialog(row?: any) {
	resetRuleForm();
	if (row) {
		editingRuleCode.value = row.rule_code;
		Object.assign(ruleForm, {
			rule_name: row.rule_name,
			task_id: row.task_id,
			metric: row.metric,
			min_count: row.min_count,
			max_count: row.max_count,
			block_level: row.block_level,
			enabled: row.enabled,
		});
	}
	ruleDialogVisible.value = true;
}

async function handleSearch() {
	await loadRules(activeQueryParams());
}

async function handleReset() {
	queryForm.task_id = '';
	queryForm.enabled = '';
	await loadRules({});
}

async function handleSubmitRule() {
	const payload = { ...ruleForm };
	if (editingRuleCode.value) {
		await updateBGradeRule(editingRuleCode.value, payload);
		ElMessage.success('B 级规则已更新');
	} else {
		await createBGradeRule(payload);
		ElMessage.success('B 级规则已创建');
	}
	ruleDialogVisible.value = false;
	await loadRules();
}

async function handleToggle(row: any) {
	await toggleBGradeRule(row.rule_code, !row.enabled);
	await loadRules();
	ElMessage.success(row.enabled ? '规则已停用' : '规则已启用');
}

async function handleDelete(row: any) {
	await ElMessageBox.confirm(`确认删除规则「${row.rule_name}」？`, '删除确认', { type: 'warning' });
	await deleteBGradeRule(row.rule_code);
	await loadRules();
	result.value = null;
	ElMessage.success('B 级规则已删除');
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
	gap: 20px;
	padding: 20px;
}
.panel {
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
.header-actions {
	display: flex;
	align-items: center;
	gap: 8px;
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
.result-panel {
	min-height: 180px;
}
.json-box {
	max-height: 180px;
	overflow: auto;
	margin-top: 20px;
	padding: 12px;
	background: #f6f8f7;
	border: 1px solid #e2e8e4;
	border-radius: 6px;
	white-space: pre-wrap;
}
</style>
