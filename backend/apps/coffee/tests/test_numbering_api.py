from decimal import Decimal
from datetime import date

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.coffee.models import CollectionEvent, PhotoAsset, Plot, Point


class CoffeeNumberingApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="collector-numbering",
            password="collector-pass",
            name="现场采集员",
            mobile="13800000003",
        )
        self.client.force_authenticate(self.user)

    def test_app_create_flow_generates_server_side_formal_ids_when_omitted(self):
        boundary = {
            "type": "Polygon",
            "coordinates": [
                [
                    [100.0, 22.0],
                    [100.001, 22.0],
                    [100.001, 22.001],
                    [100.0, 22.001],
                    [100.0, 22.0],
                ]
            ],
        }

        plot_response = self.client.post(
            "/api/coffee/app/plots/",
            {
                "task_id": "TASK202606240005",
                "name": "现场圈选地块",
                "boundary_geojson": boundary,
                "area_mu": "12.34",
                "area_calc_method": Plot.AREA_GEODESIC,
                "coordinate_system": Plot.COORD_GCJ02,
                "source_type": Plot.SOURCE_APP_DRAWN,
                "idempotency_key": "plot-numbering-001",
            },
            format="json",
        )

        self.assertEqual(plot_response.status_code, 200)
        plot_id = plot_response.data["data"]["plot_id"]
        self.assertRegex(plot_id, r"^PL\d{8}\d{4}$")

        point_response = self.client.post(
            "/api/coffee/app/points/",
            {
                "task_id": "TASK202606240005",
                "plot_id": plot_id,
                "longitude": "100.0005",
                "latitude": "22.0005",
                "coordinate_system": Point.COORD_GCJ02,
                "source_type": Point.SOURCE_APP_SELECTED,
                "idempotency_key": "point-numbering-001",
            },
            format="json",
        )

        self.assertEqual(point_response.status_code, 200)
        point_id = point_response.data["data"]["point_id"]
        self.assertRegex(point_id, r"^PT\d{8}\d{4}$")

        event_response = self.client.post(
            "/api/coffee/app/events/",
            {
                "task_id": "TASK202606240005",
                "plot_id": plot_id,
                "point_id": point_id,
                "idempotency_key": "event-numbering-001",
                "manifest_hash": "draft-manifest-hash",
            },
            format="json",
        )

        self.assertEqual(event_response.status_code, 200)
        event_id = event_response.data["data"]["event_id"]
        self.assertRegex(event_id, r"^EV\d{8}\d{4}$")

        photo_response = self.client.post(
            "/api/coffee/app/photos/init/",
            {
                "event_id": event_id,
                "category": PhotoAsset.CATEGORY_DEVICE_READING,
                "sha256": "abc123",
                "metadata": {"width": 1280},
            },
            format="json",
        )

        self.assertEqual(photo_response.status_code, 200)
        photo_id = photo_response.data["data"]["photo_id"]
        self.assertRegex(photo_id, r"^PH\d{8}\d{4}$")
        self.assertTrue(Plot.objects.filter(plot_id=plot_id).exists())
        self.assertTrue(Point.objects.filter(point_id=point_id).exists())
        self.assertTrue(CollectionEvent.objects.filter(event_id=event_id).exists())
        self.assertTrue(PhotoAsset.objects.filter(photo_id=photo_id).exists())

    def test_numbering_sequence_increments_within_same_prefix_and_day(self):
        today = date.today().strftime("%Y%m%d")
        Plot.objects.create(
            plot_id=f"PL{today}0001",
            task_code="TASK202606240006",
            name="已有地块",
            boundary_geojson={"type": "Polygon", "coordinates": [[[100, 22], [100.001, 22], [100.001, 22.001], [100, 22.001], [100, 22]]]},
            area_mu=Decimal("12.34"),
            area_calc_method=Plot.AREA_GEODESIC,
            coordinate_system=Plot.COORD_GCJ02,
            source_type=Plot.SOURCE_APP_DRAWN,
        )

        response = self.client.post(
            "/api/coffee/app/plots/",
            {
                "task_id": "TASK202606240006",
                "name": "新增地块",
                "boundary_geojson": {"type": "Polygon", "coordinates": [[[100, 22], [100.001, 22], [100.001, 22.001], [100, 22.001], [100, 22]]]},
                "area_mu": "12.34",
                "area_calc_method": Plot.AREA_GEODESIC,
                "coordinate_system": Plot.COORD_GCJ02,
                "source_type": Plot.SOURCE_APP_DRAWN,
                "idempotency_key": "plot-numbering-002",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["plot_id"], f"PL{today}0002")
