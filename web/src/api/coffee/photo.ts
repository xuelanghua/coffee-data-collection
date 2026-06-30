import { request } from '/@/utils/service';

export interface CoffeePhotoReviewPayload {
	status: 'approved' | 'returned';
	review_note?: string;
	return_reason?: string;
	return_items?: string[];
}

export interface CoffeePhotoAnnotationPayload {
	annotation_id?: string;
	label: string;
	shape_type: 'bbox' | 'polygon' | 'point';
	geometry: Record<string, any>;
	note?: string;
}

export function getPhotoList(params: Record<string, any> = {}) {
	return request({
		url: '/api/coffee/photos/',
		method: 'get',
		params,
	});
}

export function reviewPhoto(photoId: string, payload: CoffeePhotoReviewPayload) {
	return request({
		url: `/api/coffee/photos/${photoId}/review/`,
		method: 'post',
		data: payload,
	});
}

export function getPhotoAnnotations(photoId: string) {
	return request({
		url: `/api/coffee/photos/${photoId}/annotations/`,
		method: 'get',
	});
}

export function savePhotoAnnotation(photoId: string, payload: CoffeePhotoAnnotationPayload) {
	return request({
		url: `/api/coffee/photos/${photoId}/annotations/`,
		method: 'post',
		data: payload,
	});
}
