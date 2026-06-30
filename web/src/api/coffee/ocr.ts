import { request } from '/@/utils/service';

export interface CoffeeOcrCorrectionPayload {
	field_name: string;
	raw_value?: string;
	corrected_value: string;
	reason?: string;
}

export function getOcrJobs(params: Record<string, any> = {}) {
	return request({
		url: '/api/coffee/ocr/jobs/',
		method: 'get',
		params,
	});
}

export function saveOcrCorrection(ocrResultId: string, payload: CoffeeOcrCorrectionPayload) {
	return request({
		url: `/api/coffee/ocr-results/${ocrResultId}/corrections/`,
		method: 'post',
		data: payload,
	});
}
