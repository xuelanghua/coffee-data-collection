from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from dvadmin.system.models import Dept, Role
from apps.coffee.menu import ensure_coffee_role_matrix
from apps.coffee.models import CollectionEvent, OCRCorrection, OCRResult, PhotoAsset, Plot, Point, QualityReview


class CoffeeWebPhotoOcrApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="photo-reviewer",
            password="reviewer-pass",
            name="图片审核员",
            mobile="13800000003",
        )
        self.client.force_authenticate(self.user)
        self.plot = Plot.objects.create(
            plot_id="PL202606250401",
            task_code="TASK202606250004",
            name="图片审核地块",
            boundary_geojson={"type": "Polygon", "coordinates": [[[100.0, 22.0], [100.001, 22.0], [100.001, 22.001], [100.0, 22.001], [100.0, 22.0]]]},
            area_mu=Decimal("12.50"),
            area_calc_method=Plot.AREA_GEODESIC,
            coordinate_system=Plot.COORD_GCJ02,
            source_type=Plot.SOURCE_APP_DRAWN,
            created_in_field=True,
        )
        self.point = Point.objects.create(
            point_id="PT202606250401",
            task_code=self.plot.task_code,
            plot=self.plot,
            longitude=Decimal("100.00050000"),
            latitude=Decimal("22.00050000"),
            coordinate_system=Point.COORD_GCJ02,
            source_type=Point.SOURCE_APP_SELECTED,
            created_in_field=True,
        )
        self.event = CollectionEvent.objects.create(
            event_id="EV202606250401",
            task_code=self.plot.task_code,
            plot=self.plot,
            point=self.point,
            idempotency_key="web-photo-ocr-idem-001",
            status=CollectionEvent.STATUS_SUBMITTED,
            manifest_hash="manifest-for-photo-review",
        )
        self.photo = PhotoAsset.objects.create(
            photo_id="PH202606250401",
            event=self.event,
            category=PhotoAsset.CATEGORY_DEVICE_READING,
            original_file="uploads/original/PH202606250401.jpg",
            watermarked_file="uploads/watermarked/PH202606250401.jpg",
            sha256="photo-hash-401",
            metadata_json={"gps": {"longitude": 100.0005, "latitude": 22.0005}, "device": "Android"},
            precheck_status=PhotoAsset.PRECHECK_PASS,
            review_status=PhotoAsset.REVIEW_PENDING,
            immutable_status=PhotoAsset.IMMUTABLE_LOCKED,
        )
        self.ocr_result = OCRResult.objects.create(
            ocr_result_id="OCR202606250401",
            photo=self.photo,
            provider=OCRResult.PROVIDER_MANUAL,
            status=OCRResult.STATUS_SUCCESS,
            raw_response_id="RAW202606250401",
            raw_response_json={"text": "空气温度 23.8"},
            structured_json={"air_temperature": {"value": "23.8", "confidence": 0.91}},
            confidence=Decimal("0.9100"),
        )

    def create_scoped_photo_ocr(self, suffix, dept_id):
        event = CollectionEvent.objects.create(
            event_id=f"EV20260625{suffix}",
            task_code=self.plot.task_code,
            plot=self.plot,
            point=self.point,
            idempotency_key=f"web-photo-ocr-scope-{suffix}",
            status=CollectionEvent.STATUS_SUBMITTED,
            manifest_hash=f"manifest-scope-{suffix}",
            dept_belong_id=str(dept_id),
        )
        photo = PhotoAsset.objects.create(
            photo_id=f"PH20260625{suffix}",
            event=event,
            category=PhotoAsset.CATEGORY_DEVICE_READING,
            sha256=f"photo-hash-{suffix}",
        )
        OCRResult.objects.create(
            ocr_result_id=f"OCR20260625{suffix}",
            photo=photo,
            provider=OCRResult.PROVIDER_MANUAL,
            status=OCRResult.STATUS_SUCCESS,
            raw_response_id=f"RAW20260625{suffix}",
            raw_response_json={"text": "风速 1.8"},
            structured_json={"wind_speed": {"value": "1.8", "confidence": 0.91}},
            confidence=Decimal("0.9100"),
        )
        return photo

    def test_photo_and_ocr_lists_are_limited_to_reviewer_department_but_admin_can_see_all(self):
        ensure_coffee_role_matrix()
        north_dept = Dept.objects.create(name="北区图片组", key="photo-north")
        south_dept = Dept.objects.create(name="南区图片组", key="photo-south")
        reviewer = get_user_model().objects.create_user(
            username="photo-dept-reviewer",
            password="reviewer-pass",
            name="北区图片审核员",
            mobile="13800000035",
            dept=north_dept,
        )
        reviewer.role.add(Role.objects.get(key="coffee_reviewer"))
        admin = get_user_model().objects.create_user(
            username="photo-dept-admin",
            password="admin-pass",
            name="图片管理员",
            mobile="13800000036",
        )
        admin.role.add(Role.objects.get(key="coffee_admin"))
        north_photo = self.create_scoped_photo_ocr("0511", north_dept.id)
        self.create_scoped_photo_ocr("0512", south_dept.id)

        self.client.force_authenticate(reviewer)
        photo_response = self.client.get("/api/coffee/photos/")
        ocr_response = self.client.get("/api/coffee/ocr/jobs/")

        self.assertEqual(photo_response.status_code, 200)
        self.assertEqual(photo_response.data["data"]["count"], 1)
        self.assertEqual(photo_response.data["data"]["results"][0]["photo_id"], north_photo.photo_id)
        self.assertEqual(ocr_response.status_code, 200)
        self.assertEqual(ocr_response.data["data"]["count"], 1)
        self.assertEqual(ocr_response.data["data"]["results"][0]["photo_id"], north_photo.photo_id)

        self.client.force_authenticate(admin)
        admin_photo_response = self.client.get("/api/coffee/photos/")
        admin_ocr_response = self.client.get("/api/coffee/ocr/jobs/")

        self.assertEqual(admin_photo_response.status_code, 200)
        self.assertEqual(admin_photo_response.data["data"]["count"], 3)
        self.assertEqual(admin_ocr_response.status_code, 200)
        self.assertEqual(admin_ocr_response.data["data"]["count"], 3)

    def test_web_photo_list_exposes_asset_metadata_and_ocr_summary(self):
        response = self.client.get("/api/coffee/photos/", {"review_status": PhotoAsset.REVIEW_PENDING})

        self.assertEqual(response.status_code, 200)
        data = response.data["data"]
        self.assertEqual(data["count"], 1)
        item = data["results"][0]
        self.assertEqual(item["photo_id"], self.photo.photo_id)
        self.assertEqual(item["event_id"], self.event.event_id)
        self.assertEqual(item["metadata"]["device"], "Android")
        self.assertEqual(item["ocr_count"], 1)
        self.assertEqual(item["latest_ocr_status"], OCRResult.STATUS_SUCCESS)

    def test_web_photo_review_updates_photo_status_and_records_photo_review(self):
        response = self.client.post(
            f"/api/coffee/photos/{self.photo.photo_id}/review/",
            {"status": PhotoAsset.REVIEW_APPROVED, "review_note": "照片清晰，水印完整"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.photo.refresh_from_db()
        self.assertEqual(self.photo.review_status, PhotoAsset.REVIEW_APPROVED)
        review = QualityReview.objects.get(event=self.event, review_type=QualityReview.REVIEW_TYPE_PHOTO)
        self.assertEqual(review.status, QualityReview.STATUS_APPROVED)
        self.assertEqual(review.result_json["photo_id"], self.photo.photo_id)

    def test_web_photo_return_requires_return_items(self):
        response = self.client.post(
            f"/api/coffee/photos/{self.photo.photo_id}/review/",
            {
                "status": PhotoAsset.REVIEW_RETURNED,
                "return_reason": "图片不清晰",
                "return_items": ["photo_blurry"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.photo.refresh_from_db()
        self.assertEqual(self.photo.review_status, PhotoAsset.REVIEW_RETURNED)
        review = QualityReview.objects.get(event=self.event, review_type=QualityReview.REVIEW_TYPE_PHOTO)
        self.assertEqual(review.status, QualityReview.STATUS_RETURNED)
        self.assertEqual(review.return_items, ["photo_blurry"])

    def test_web_ocr_jobs_list_and_correction_versioning(self):
        list_response = self.client.get("/api/coffee/ocr/jobs/", {"status": OCRResult.STATUS_SUCCESS})
        self.assertEqual(list_response.status_code, 200)
        item = list_response.data["data"]["results"][0]
        self.assertEqual(item["ocr_result_id"], self.ocr_result.ocr_result_id)
        self.assertEqual(item["photo_id"], self.photo.photo_id)
        self.assertEqual(item["event_id"], self.event.event_id)

        correction_response = self.client.post(
            f"/api/coffee/ocr-results/{self.ocr_result.ocr_result_id}/corrections/",
            {
                "field_name": "air_temperature",
                "raw_value": "23.8",
                "corrected_value": "23.6",
                "reason": "Web 人工校正设备采集屏幕",
            },
            format="json",
        )

        self.assertEqual(correction_response.status_code, 200)
        correction = OCRCorrection.objects.get(ocr_result=self.ocr_result, field_name="air_temperature")
        self.assertEqual(correction.corrected_value, "23.6")
        self.assertEqual(correction.version, 1)
