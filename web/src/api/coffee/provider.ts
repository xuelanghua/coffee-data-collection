import { request } from '/@/utils/service';

export interface CoffeeProviderConfigPayload {
	provider_type: 'map' | 'weather' | 'ocr' | 'storage';
	provider_name: string;
	display_name: string;
	enabled: boolean;
	priority: number;
	timeout_ms: number;
	rate_limit_per_minute: number;
	config_json: Record<string, any>;
	secret_fields: string[];
}

export function getProviderConfigs(params: Record<string, any> = {}) {
	return request({
		url: '/api/coffee/provider-configs/',
		method: 'get',
		params,
	});
}

export function createProviderConfig(data: CoffeeProviderConfigPayload) {
	return request({
		url: '/api/coffee/provider-configs/',
		method: 'post',
		data,
	});
}

export function updateProviderConfig(providerId: number, data: CoffeeProviderConfigPayload) {
	return request({
		url: `/api/coffee/provider-configs/${providerId}/`,
		method: 'put',
		data,
	});
}

export function deleteProviderConfig(providerId: number) {
	return request({
		url: `/api/coffee/provider-configs/${providerId}/`,
		method: 'delete',
	});
}

export function toggleProviderConfig(providerId: number, enabled: boolean) {
	return request({
		url: `/api/coffee/provider-configs/${providerId}/toggle/`,
		method: 'post',
		data: { enabled },
	});
}

export function testProviderConfig(providerId: number) {
	return request({
		url: `/api/coffee/provider-configs/${providerId}/test/`,
		method: 'post',
		data: {},
	});
}
