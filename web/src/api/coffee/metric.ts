import { request } from '/@/utils/service';

export interface CoffeeMetricDefinitionPayload {
	metric_code: string;
	metric_name: string;
	metric_group: 'progress' | 'quality' | 'performance';
	calculation_method: string;
	description?: string;
	unit?: string;
	enabled: boolean;
}

export function getMetricDefinitions(params: Record<string, any> = {}) {
	return request({
		url: '/api/coffee/metric-definitions/',
		method: 'get',
		params,
	});
}

export function createMetricDefinition(data: CoffeeMetricDefinitionPayload) {
	return request({
		url: '/api/coffee/metric-definitions/',
		method: 'post',
		data,
	});
}
