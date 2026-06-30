import { request } from '/@/utils/service';

export function getProgressStatistics(params: Record<string, any> = {}) {
	return request({
		url: '/api/coffee/statistics/progress/',
		method: 'get',
		params,
	});
}

export function getQualityStatistics(params: Record<string, any> = {}) {
	return request({
		url: '/api/coffee/statistics/quality/',
		method: 'get',
		params,
	});
}

export function getPerformanceStatistics(params: Record<string, any> = {}) {
	return request({
		url: '/api/coffee/statistics/performance/',
		method: 'get',
		params,
	});
}
