import { request } from '/@/utils/service';

export const coffeeEventApiPrefix = '/api/coffee/events/';

export interface CoffeeReviewReturnPayload {
	return_reason: string;
	return_note?: string;
	return_items: string[];
}

export function getEventList(params: Record<string, any> = {}) {
	return request({
		url: '/api/coffee/events/',
		method: 'get',
		params,
	});
}

export function getEventDetail(eventId: string) {
	return request({
		url: `/api/coffee/events/${eventId}/`,
		method: 'get',
	});
}

export function approveEvent(eventId: string, review_note = '') {
	return request({
		url: `/api/coffee/events/${eventId}/review/approve/`,
		method: 'post',
		data: { review_note },
	});
}

export function returnEvent(eventId: string, payload: CoffeeReviewReturnPayload) {
	return request({
		url: `/api/coffee/events/${eventId}/review/return/`,
		method: 'post',
		data: payload,
	});
}

export function bulkApproveEvents(event_ids: string[], review_note = '') {
	return request({
		url: '/api/coffee/events/review/bulk-approve/',
		method: 'post',
		data: { event_ids, review_note },
	});
}

export function bulkReturnEvents(event_ids: string[], payload: CoffeeReviewReturnPayload) {
	return request({
		url: '/api/coffee/events/review/bulk-return/',
		method: 'post',
		data: { event_ids, ...payload },
	});
}
