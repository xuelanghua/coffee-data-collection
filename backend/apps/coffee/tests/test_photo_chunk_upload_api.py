from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.coffee.models import CollectionEvent, PhotoAsset, Plot, Point


class CoffeePhotoChunkUploadApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="collector-chunk",
            password="collector-pass",
            name="现场采集员",
            mobile="13800000004",
        )
        self.client.force_authenticate(self.user)
        self.plot = Plot.objects.create(
            plot_id="PL202606250301",
            task_code="TASK202606250003",
            name="现场圈选地块",
            boundary_geojson={"type": "Polygon", "coordinates": [[[100.0, 22.0], [100.001, 22.0], [100.001, 22.001], [100.0, 22.001], [100.0, 22.0]]]},
            area_mu=Decimal("12.34"),
            area_calc_method=Plot.AREA_GEODESIC,
            coordinate_system=Plot.COORD_GCJ02,
            source_type=Plot.SOURCE_APP_DRAWN,
            created_in_field=True,
        )
        self.point = Point.objects.create(
            point_id="PT202606250301",
            task_code=self.plot.task_code,
            plot=self.plot,
            longitude=Decimal("100.00050000"),
            latitude=Decimal("22.00050000"),
            coordinate_system=Point.COORD_GCJ02,
            source_type=Point.SOURCE_APP_SELECTED,
            created_in_field=True,
        )
        self.event = CollectionEvent.objects.create(
            event_id="EV202606250301",
            task_code=self.plot.task_code,
            plot=self.plot,
            point=self.point,
            idempotency_key="event-idem-chunk-001",
            manifest_hash="draft-manifest-hash",
        )

    def test_photo_chunk_upload_is_resumable_and_complete_validates_manifest(self):
        init_response = self.client.post(
            "/api/coffee/app/photos/init/",
            {
                "event_id": self.event.event_id,
                "photo_id": "PH202606250301",
                "category": PhotoAsset.CATEGORY_DEVICE_READING,
                "sha256": "whole-file-sha",
                "metadata": {"width": 1280},
            },
            format="json",
        )

        self.assertEqual(init_response.status_code, 200)
        self.assertRegex(init_response.data["data"]["upload_session_id"], r"^UP")

        first_chunk = self.client.put(
            "/api/coffee/app/photos/PH202606250301/chunks/0/",
            {"chunk_hash": "chunk-0-sha", "chunk_size": 1024},
            format="json",
        )
        duplicate_chunk = self.client.put(
            "/api/coffee/app/photos/PH202606250301/chunks/0/",
            {"chunk_hash": "chunk-0-sha", "chunk_size": 1024},
            format="json",
        )
        second_chunk = self.client.put(
            "/api/coffee/app/photos/PH202606250301/chunks/1/",
            {"chunk_hash": "chunk-1-sha", "chunk_size": 2048},
            format="json",
        )

        self.assertEqual(first_chunk.status_code, 200)
        self.assertEqual(duplicate_chunk.status_code, 200)
        self.assertEqual(second_chunk.status_code, 200)
        self.assertEqual(second_chunk.data["data"]["uploaded_chunks"], 2)

        incomplete_complete = self.client.post(
            "/api/coffee/app/photos/PH202606250301/complete/",
            {
                "original_file": "uploads/original/PH202606250301.jpg",
                "watermarked_file": "uploads/watermarked/PH202606250301.jpg",
                "sha256": "whole-file-sha",
                "precheck_status": PhotoAsset.PRECHECK_PASS,
                "chunk_count": 3,
                "chunk_hashes": ["chunk-0-sha", "chunk-1-sha", "chunk-2-sha"],
            },
            format="json",
        )

        self.assertEqual(incomplete_complete.status_code, 409)
        self.assertEqual(incomplete_complete.data["code"], "COFFEE_PHOTO_CHUNKS_INCOMPLETE")

        complete_response = self.client.post(
            "/api/coffee/app/photos/PH202606250301/complete/",
            {
                "original_file": "uploads/original/PH202606250301.jpg",
                "watermarked_file": "uploads/watermarked/PH202606250301.jpg",
                "sha256": "whole-file-sha",
                "precheck_status": PhotoAsset.PRECHECK_PASS,
                "chunk_count": 2,
                "chunk_hashes": ["chunk-0-sha", "chunk-1-sha"],
            },
            format="json",
        )

        self.assertEqual(complete_response.status_code, 200)
        self.assertEqual(complete_response.data["data"]["uploaded_chunk_count"], 2)
        self.assertEqual(complete_response.data["data"]["immutable_status"], PhotoAsset.IMMUTABLE_LOCKED)
