from decimal import Decimal
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from dvadmin.system.models import Dept, Role
from apps.coffee.menu import ensure_coffee_role_matrix
from apps.coffee.models import CollectionEvent, ExportJob, PhotoAsset, Plot, Point, QualityReview


class CoffeeStatisticsExportApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="stats-admin",
            password="stats-pass",
            name="统计管理员",
            mobile="13800000005",
        )
        self.client.force_authenticate(self.user)
        self.plot = Plot.objects.create(
            plot_id="PL202606250501",
            task_code="TASK202606250005",
            name="统计地块",
            boundary_geojson={"type": "Polygon", "coordinates": [[[100.0, 22.0], [100.001, 22.0], [100.001, 22.001], [100.0, 22.001], [100.0, 22.0]]]},
            area_mu=Decimal("8.50"),
            area_calc_method=Plot.AREA_GEODESIC,
            coordinate_system=Plot.COORD_GCJ02,
            source_type=Plot.SOURCE_APP_DRAWN,
            created_in_field=True,
        )
        self.point = Point.objects.create(
            point_id="PT202606250501",
            task_code=self.plot.task_code,
            plot=self.plot,
            longitude=Decimal("100.00050000"),
            latitude=Decimal("22.00050000"),
            coordinate_system=Point.COORD_GCJ02,
            source_type=Point.SOURCE_APP_SELECTED,
            created_in_field=True,
        )
        self.submitted_event = CollectionEvent.objects.create(
            event_id="EV202606250501",
            task_code=self.plot.task_code,
            plot=self.plot,
            point=self.point,
            collector_id="collector-a",
            idempotency_key="stats-idem-001",
            status=CollectionEvent.STATUS_SUBMITTED,
            manifest_hash="stats-manifest-001",
        )
        self.approved_event = CollectionEvent.objects.create(
            event_id="EV202606250502",
            task_code=self.plot.task_code,
            plot=self.plot,
            point=self.point,
            collector_id="collector-a",
            idempotency_key="stats-idem-002",
            status=CollectionEvent.STATUS_APPROVED,
            manifest_hash="stats-manifest-002",
        )
        self.returned_event = CollectionEvent.objects.create(
            event_id="EV202606250503",
            task_code=self.plot.task_code,
            plot=self.plot,
            point=self.point,
            collector_id="collector-b",
            idempotency_key="stats-idem-003",
            status=CollectionEvent.STATUS_RETURNED,
            manifest_hash="stats-manifest-003",
        )
        PhotoAsset.objects.create(
            photo_id="PH202606250501",
            event=self.submitted_event,
            category=PhotoAsset.CATEGORY_DEVICE_READING,
            sha256="hash-501",
            precheck_status=PhotoAsset.PRECHECK_PASS,
            review_status=PhotoAsset.REVIEW_APPROVED,
            immutable_status=PhotoAsset.IMMUTABLE_LOCKED,
        )
        PhotoAsset.objects.create(
            photo_id="PH202606250502",
            event=self.returned_event,
            category=PhotoAsset.CATEGORY_ENVIRONMENT,
            sha256="hash-502",
            precheck_status=PhotoAsset.PRECHECK_WARNING,
            review_status=PhotoAsset.REVIEW_RETURNED,
            immutable_status=PhotoAsset.IMMUTABLE_LOCKED,
        )
        QualityReview.objects.create(
            event=self.approved_event,
            review_type=QualityReview.REVIEW_TYPE_EVENT,
            status=QualityReview.STATUS_APPROVED,
            reviewer_id=str(self.user.id),
            version=1,
        )
        QualityReview.objects.create(
            event=self.returned_event,
            review_type=QualityReview.REVIEW_TYPE_EVENT,
            status=QualityReview.STATUS_RETURNED,
            reviewer_id=str(self.user.id),
            return_reason="照片不清",
            return_items=["photo_quality"],
            version=1,
        )

    def test_progress_quality_and_performance_statistics(self):
        progress = self.client.get("/api/coffee/statistics/progress/")
        self.assertEqual(progress.status_code, 200)
        self.assertEqual(progress.data["data"]["total_events"], 3)
        self.assertEqual(progress.data["data"]["status_counts"][CollectionEvent.STATUS_APPROVED], 1)

        quality = self.client.get("/api/coffee/statistics/quality/")
        self.assertEqual(quality.status_code, 200)
        self.assertEqual(quality.data["data"]["photo_review_counts"][PhotoAsset.REVIEW_RETURNED], 1)
        self.assertEqual(quality.data["data"]["return_reason_counts"]["照片不清"], 1)

        performance = self.client.get("/api/coffee/statistics/performance/")
        self.assertEqual(performance.status_code, 200)
        first = performance.data["data"]["collectors"][0]
        self.assertEqual(first["collector_id"], "collector-a")
        self.assertEqual(first["event_count"], 2)
        self.assertEqual(first["approved_count"], 1)

    def test_export_job_create_list_and_cancel(self):
        create_response = self.client.post(
            "/api/coffee/exports/",
            {
                "export_type": "event_detail",
                "filters": {"task_id": self.plot.task_code},
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, 200)
        job = create_response.data["data"]
        self.assertEqual(job["status"], "queued")
        self.assertEqual(job["progress"], 0)

        list_response = self.client.get("/api/coffee/exports/")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.data["data"]["count"], 1)

        cancel_response = self.client.post(f"/api/coffee/exports/{job['job_code']}/cancel/", {}, format="json")
        self.assertEqual(cancel_response.status_code, 200)
        self.assertEqual(cancel_response.data["data"]["status"], "cancelled")

    def test_dataset_package_export_create_enqueues_celery_task_after_commit(self):
        with patch("apps.coffee.tasks.run_export_job.delay") as delay:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(
                    "/api/coffee/exports/",
                    {
                        "export_type": ExportJob.TYPE_DATASET_PACKAGE,
                        "filters": {"event_id": self.submitted_event.event_id},
                    },
                    format="json",
                )

        self.assertEqual(response.status_code, 200)
        job = response.data["data"]
        self.assertEqual(job["status"], ExportJob.STATUS_QUEUED)
        delay.assert_called_once_with(job["job_code"])

    def test_dataset_package_export_job_generates_offline_package(self):
        from apps.coffee.export_jobs import process_export_job

        job = ExportJob.objects.create(
            job_code="EX202606250599",
            export_type=ExportJob.TYPE_DATASET_PACKAGE,
            filters_json={"event_id": self.submitted_event.event_id},
            status=ExportJob.STATUS_QUEUED,
            progress=0,
            created_by=str(self.user.id),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            package = process_export_job(job, Path(temp_dir))
            job.refresh_from_db()

            self.assertEqual(job.status, ExportJob.STATUS_SUCCESS)
            self.assertEqual(job.progress, 100)
            self.assertEqual(job.file_path, package["package_dir"])
            self.assertEqual(job.file_sha256, package["package_hash"])
            self.assertTrue((Path(job.file_path) / "manifest.json").exists())
            self.assertTrue((Path(job.file_path) / "index.html").exists())

    def test_dataset_package_export_job_can_be_processed_by_celery_task_entry(self):
        from apps.coffee.tasks import run_export_job

        job = ExportJob.objects.create(
            job_code="EX202606250598",
            export_type=ExportJob.TYPE_DATASET_PACKAGE,
            filters_json={"event_id": self.submitted_event.event_id},
            status=ExportJob.STATUS_QUEUED,
            progress=0,
            created_by=str(self.user.id),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_export_job(job.job_code, output_root=temp_dir)
            job.refresh_from_db()

            self.assertEqual(result["job_code"], job.job_code)
            self.assertEqual(result["status"], ExportJob.STATUS_SUCCESS)
            self.assertEqual(job.status, ExportJob.STATUS_SUCCESS)
            self.assertEqual(job.progress, 100)
            self.assertEqual(result["file_path"], job.file_path)
            self.assertEqual(result["file_sha256"], job.file_sha256)
            self.assertTrue((Path(job.file_path) / "manifest.json").exists())
            self.assertTrue(hasattr(run_export_job, "delay"))

    def test_statistics_and_export_lists_are_limited_to_reviewer_department_but_admin_can_see_exports(self):
        ensure_coffee_role_matrix()
        north_dept = Dept.objects.create(name="北区统计组", key="stats-north")
        south_dept = Dept.objects.create(name="南区统计组", key="stats-south")
        reviewer = get_user_model().objects.create_user(
            username="stats-dept-reviewer",
            password="stats-dept-pass",
            name="北区统计员",
            mobile="13800000037",
            dept=north_dept,
        )
        reviewer.role.add(Role.objects.get(key="coffee_reviewer"))
        admin = get_user_model().objects.create_user(
            username="stats-dept-admin",
            password="stats-admin-pass",
            name="统计管理员",
            mobile="13800000038",
        )
        admin.role.add(Role.objects.get(key="coffee_admin"))
        north_event = CollectionEvent.objects.create(
            event_id="EV202606250521",
            task_code=self.plot.task_code,
            plot=self.plot,
            point=self.point,
            collector_id="north-collector",
            idempotency_key="stats-dept-north",
            status=CollectionEvent.STATUS_APPROVED,
            manifest_hash="stats-dept-north-manifest",
            dept_belong_id=str(north_dept.id),
        )
        south_event = CollectionEvent.objects.create(
            event_id="EV202606250522",
            task_code=self.plot.task_code,
            plot=self.plot,
            point=self.point,
            collector_id="south-collector",
            idempotency_key="stats-dept-south",
            status=CollectionEvent.STATUS_RETURNED,
            manifest_hash="stats-dept-south-manifest",
            dept_belong_id=str(south_dept.id),
        )
        PhotoAsset.objects.create(
            photo_id="PH202606250521",
            event=north_event,
            category=PhotoAsset.CATEGORY_DEVICE_READING,
            sha256="stats-dept-north-photo",
            review_status=PhotoAsset.REVIEW_APPROVED,
            precheck_status=PhotoAsset.PRECHECK_PASS,
        )
        PhotoAsset.objects.create(
            photo_id="PH202606250522",
            event=south_event,
            category=PhotoAsset.CATEGORY_DEVICE_READING,
            sha256="stats-dept-south-photo",
            review_status=PhotoAsset.REVIEW_RETURNED,
            precheck_status=PhotoAsset.PRECHECK_WARNING,
        )
        QualityReview.objects.create(
            event=north_event,
            review_type=QualityReview.REVIEW_TYPE_EVENT,
            status=QualityReview.STATUS_APPROVED,
            reviewer_id=str(reviewer.id),
            version=1,
        )
        QualityReview.objects.create(
            event=south_event,
            review_type=QualityReview.REVIEW_TYPE_EVENT,
            status=QualityReview.STATUS_RETURNED,
            reviewer_id=str(reviewer.id),
            return_reason="跨部门退回",
            version=1,
        )
        ExportJob.objects.create(
            job_code="EX202606250521",
            export_type=ExportJob.TYPE_EVENT_DETAIL,
            filters_json={},
            status=ExportJob.STATUS_QUEUED,
            created_by=str(reviewer.id),
            dept_belong_id=str(north_dept.id),
        )
        ExportJob.objects.create(
            job_code="EX202606250522",
            export_type=ExportJob.TYPE_EVENT_DETAIL,
            filters_json={},
            status=ExportJob.STATUS_QUEUED,
            created_by=str(reviewer.id),
            dept_belong_id=str(south_dept.id),
        )

        self.client.force_authenticate(reviewer)
        progress = self.client.get("/api/coffee/statistics/progress/")
        quality = self.client.get("/api/coffee/statistics/quality/")
        performance = self.client.get("/api/coffee/statistics/performance/")
        exports = self.client.get("/api/coffee/exports/")

        self.assertEqual(progress.status_code, 200)
        self.assertEqual(progress.data["data"]["total_events"], 1)
        self.assertEqual(progress.data["data"]["status_counts"][CollectionEvent.STATUS_APPROVED], 1)
        self.assertEqual(quality.status_code, 200)
        self.assertEqual(quality.data["data"]["photo_review_counts"][PhotoAsset.REVIEW_APPROVED], 1)
        self.assertNotIn("跨部门退回", quality.data["data"]["return_reason_counts"])
        self.assertEqual(performance.status_code, 200)
        self.assertEqual(performance.data["data"]["collectors"][0]["collector_id"], "north-collector")
        self.assertEqual(exports.status_code, 200)
        self.assertEqual(exports.data["data"]["count"], 1)
        self.assertEqual(exports.data["data"]["results"][0]["job_code"], "EX202606250521")

        self.client.force_authenticate(admin)
        admin_exports = self.client.get("/api/coffee/exports/")

        self.assertEqual(admin_exports.status_code, 200)
        self.assertEqual(admin_exports.data["data"]["count"], 2)
