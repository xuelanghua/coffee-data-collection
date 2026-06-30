from decimal import Decimal

from django.test import TestCase

from apps.coffee.models import (
    CollectionEvent,
    EventFieldValue,
    MeasurementRecord,
    Plot,
    PlotBoundaryVersion,
    Point,
)


class CoffeeDomainModelTests(TestCase):
    def test_field_drawn_plot_point_event_and_device_measurements_are_persisted(self):
        plot = Plot.objects.create(
            plot_id="PL202606240001",
            task_code="TASK202606240001",
            name="现场圈选地块",
            boundary_geojson={
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
            },
            area_mu=Decimal("12.34"),
            area_calc_method=Plot.AREA_GEODESIC,
            coordinate_system=Plot.COORD_GCJ02,
            source_type=Plot.SOURCE_APP_DRAWN,
            created_in_field=True,
        )

        PlotBoundaryVersion.objects.create(
            plot=plot,
            version=1,
            boundary_geojson=plot.boundary_geojson,
            area_mu=plot.area_mu,
            area_calc_method=Plot.AREA_GEODESIC,
            coordinate_system=Plot.COORD_GCJ02,
            source_type=Plot.SOURCE_APP_DRAWN,
        )

        point = Point.objects.create(
            point_id="PT202606240001",
            task_code=plot.task_code,
            plot=plot,
            longitude=Decimal("100.0005"),
            latitude=Decimal("22.0005"),
            altitude=Decimal("1200.50"),
            coordinate_system=Point.COORD_GCJ02,
            source_type=Point.SOURCE_APP_SELECTED,
            created_in_field=True,
        )

        event = CollectionEvent.objects.create(
            event_id="EV202606240001",
            task_code=plot.task_code,
            plot=plot,
            point=point,
            idempotency_key="idem-202606240001",
            status=CollectionEvent.STATUS_DRAFT,
            manifest_hash="manifest-hash",
        )

        measurement = MeasurementRecord.objects.create(
            event=event,
            device_no="ENV-001",
            wind_speed=Decimal("1.80"),
            wind_direction="东南",
            air_temperature=Decimal("23.60"),
            air_humidity=Decimal("72.00"),
            atmospheric_pressure=Decimal("90.80"),
            rainfall=Decimal("0.00"),
            soil_moisture=Decimal("38.50"),
            soil_temperature=Decimal("21.40"),
            soil_salinity=Decimal("0.18"),
            soil_ph=Decimal("6.40"),
            source_photo_id="PH202606240001",
            ocr_result_id="OCR202606240001",
        )

        field_value = EventFieldValue.objects.create(
            event=event,
            field_code="air_temperature",
            field_label="空气温度",
            value_number=Decimal("23.60"),
            value_text="23.6",
            unit="摄氏度",
            source_type=EventFieldValue.SOURCE_OCR,
            source_photo_id="PH202606240001",
            ocr_result_id="OCR202606240001",
            ocr_raw_value="23.8",
            ocr_confidence=Decimal("0.91"),
            corrected_from="23.8",
            correction_reason="人工核对设备采集屏幕",
        )

        self.assertEqual(plot.review_status, Plot.REVIEW_PENDING)
        self.assertEqual(point.review_status, Point.REVIEW_PENDING)
        self.assertEqual(plot.boundary_versions.count(), 1)
        self.assertEqual(measurement.soil_ph, Decimal("6.40"))
        self.assertEqual(field_value.source_type, EventFieldValue.SOURCE_OCR)
