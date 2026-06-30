import { request } from '/@/utils/service';

export interface CoffeeExportJobPayload {
	export_type: 'event_detail' | 'photo_asset' | 'ocr_correction' | 'quality_review' | 'statistics' | 'dataset_package';
	filters?: Record<string, any>;
}

export function getExportJobs(params: Record<string, any> = {}) {
	return request({
		url: '/api/coffee/exports/',
		method: 'get',
		params,
	});
}

export function createExportJob(data: CoffeeExportJobPayload) {
	return request({
		url: '/api/coffee/exports/',
		method: 'post',
		data,
	});
}

export function cancelExportJob(jobCode: string) {
	return request({
		url: `/api/coffee/exports/${jobCode}/cancel/`,
		method: 'post',
		data: {},
	});
}
