from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.coffee.models import CollectionEvent, PhotoAsset, Plot, Point


class CoffeePhotoAnnotationApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="annotation-reviewer",
            password="reviewer-pass",
            name="标注审核员",
            mobile="13800000041",
        )
        self.client.force_authenticate(self.user)
        self.plot = Plot.objects.create(
            plot_id="PL202606260701",
            task_code="TASK202606260007",
            name="标注地块",
            boundary_geojson={"type": "Polygon", "coordinates": [[[100.0, 22.0], [100.001, 22.0], [100.001, 22.001], [100.0, 22.001], [100.0, 22.0]]]},
            area_mu=Decimal("9.80"),
            area_calc_method=Plot.AREA_GEODESIC,
            coordinate_system=Plot.COORD_GCJ02,
            source_type=Plot.SOURCE_APP_DRAWN,
            created_in_field=True,
        )
        self.point = Point.objects.create(
            point_id="PT202606260701",
            task_code=self.plot.task_code,
            plot=self.plot,
            longitude=Decimal("100.00050000"),
            latitude=Decimal("22.00050000"),
            coordinate_system=Point.COORD_GCJ02,
            source_type=Point.SOURCE_APP_SELECTED,
            created_in_field=True,
        )
        self.event = CollectionEvent.objects.create(
            event_id="EV202606260701",
            task_code=self.plot.task_code,
            plot=self.plot,
            point=self.point,
            idempotency_key="annotation-event-idem-001",
            status=CollectionEvent.STATUS_SUBMITTED,
            manifest_hash="annotation-manifest",
        )
        self.photo = PhotoAsset.objects.create(
            photo_id="PH202606260701",
            event=self.event,
            category=PhotoAsset.CATEGORY_FRUIT,
            original_file="uploads/original/PH202606260701.jpg",
            watermarked_file="uploads/watermarked/PH202606260701.jpg",
            sha256="annotation-photo-hash",
            precheck_status=PhotoAsset.PRECHECK_PASS,
            immutable_status=PhotoAsset.IMMUTABLE_LOCKED,
        )

    def test_photo_annotation_edits_create_versions_without_overwriting_history(self):
        first_response = self.client.post(
            f"/api/coffee/photos/{self.photo.photo_id}/annotations/",
            {
                "label": "coffee_cherry",
                "shape_type": "bbox",
                "geometry": {"x": 10, "y": 20, "width": 80, "height": 64},
                "note": "初始框选",
            },
            format="json",
        )

        self.assertEqual(first_response.status_code, 200)
        first = first_response.data["data"]
        self.assertEqual(first["version"], 1)
        self.assertTrue(first["is_latest"])
        self.assertEqual(first["geometry"]["width"], 80)

        second_response = self.client.post(
            f"/api/coffee/photos/{self.photo.photo_id}/annotations/",
            {
                "annotation_id": first["annotation_id"],
                "label": "coffee_cherry",
                "shape_type": "bbox",
                "geometry": {"x": 12, "y": 22, "width": 84, "height": 66},
                "note": "复核后微调",
            },
            format="json",
        )

        self.assertEqual(second_response.status_code, 200)
        second = second_response.data["data"]
        self.assertEqual(second["annotation_id"], first["annotation_id"])
        self.assertEqual(second["version"], 2)
        self.assertTrue(second["is_latest"])

        list_response = self.client.get(f"/api/coffee/photos/{self.photo.photo_id}/annotations/")

        self.assertEqual(list_response.status_code, 200)
        versions = list_response.data["data"]["results"]
        self.assertEqual(len(versions), 2)
        self.assertEqual([item["version"] for item in versions], [1, 2])
        self.assertFalse(versions[0]["is_latest"])
        self.assertEqual(versions[0]["geometry"]["width"], 80)
        self.assertEqual(versions[1]["geometry"]["width"], 84)

    def test_event_detail_includes_photo_annotation_versions(self):
        create_response = self.client.post(
            f"/api/coffee/photos/{self.photo.photo_id}/annotations/",
            {
                "label": "coffee_leaf",
                "shape_type": "polygon",
                "geometry": {"points": [[10, 20], [40, 20], [36, 48], [12, 45]]},
                "note": "叶片区域",
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, 200)

        detail_response = self.client.get(f"/api/coffee/events/{self.event.event_id}/")

        self.assertEqual(detail_response.status_code, 200)
        photo_block = detail_response.data["data"]["photos"][0]
        self.assertEqual(photo_block["photo"]["photo_id"], self.photo.photo_id)
        self.assertEqual(photo_block["annotations"][0]["label"], "coffee_leaf")
        self.assertEqual(photo_block["annotations"][0]["shape_type"], "polygon")
        self.assertEqual(photo_block["annotations"][0]["version"], 1)
