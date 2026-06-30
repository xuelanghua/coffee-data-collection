import { request } from '/@/utils/service';

export interface CoffeeBGradeRulePayload {
	rule_name: string;
	task_id: string;
	metric: 'approved_event_count' | 'returned_event_count' | 'submitted_event_count';
	min_count?: number;
	max_count?: number;
	block_level: 'blocking' | 'warning';
	enabled: boolean;
}

export function getBGradeRules(params: Record<string, any> = {}) {
	return request({
		url: '/api/coffee/b-grade-rules/',
		method: 'get',
		params,
	});
}

export function createBGradeRule(data: CoffeeBGradeRulePayload) {
	return request({
		url: '/api/coffee/b-grade-rules/',
		method: 'post',
		data,
	});
}

export function checkBGradeRule(ruleCode: string) {
	return request({
		url: `/api/coffee/b-grade-rules/${ruleCode}/check/`,
		method: 'post',
		data: {},
	});
}
