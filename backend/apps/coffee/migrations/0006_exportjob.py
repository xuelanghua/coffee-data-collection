from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("coffee", "0005_providerconfig"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExportJob",
            fields=[
                ("id", models.BigAutoField(help_text="Id", primary_key=True, serialize=False, verbose_name="Id")),
                ("description", models.CharField(blank=True, help_text="描述", max_length=255, null=True, verbose_name="描述")),
                ("modifier", models.CharField(blank=True, help_text="修改人", max_length=255, null=True, verbose_name="修改人")),
                ("dept_belong_id", models.CharField(blank=True, help_text="数据归属部门", max_length=255, null=True, verbose_name="数据归属部门")),
                ("update_datetime", models.DateTimeField(auto_now=True, help_text="修改时间", null=True, verbose_name="修改时间")),
                ("create_datetime", models.DateTimeField(auto_now_add=True, help_text="创建时间", null=True, verbose_name="创建时间")),
                ("job_code", models.CharField(db_index=True, max_length=64, unique=True, verbose_name="导出任务编号")),
                ("export_type", models.CharField(choices=[("event_detail", "采集事件明细"), ("photo_asset", "照片资产清单"), ("ocr_correction", "OCR结果和修正记录"), ("quality_review", "质检审核记录"), ("statistics", "统计报表"), ("dataset_package", "数据集包")], max_length=32, verbose_name="导出类型")),
                ("filters_json", models.JSONField(blank=True, default=dict, verbose_name="筛选条件")),
                ("status", models.CharField(choices=[("queued", "排队"), ("running", "处理中"), ("success", "完成"), ("failed", "失败"), ("expired", "已过期"), ("cancelled", "已取消")], default="queued", max_length=32, verbose_name="状态")),
                ("progress", models.PositiveIntegerField(default=0, verbose_name="进度")),
                ("file_path", models.CharField(blank=True, max_length=512, null=True, verbose_name="文件路径")),
                ("file_sha256", models.CharField(blank=True, max_length=128, null=True, verbose_name="文件SHA256")),
                ("created_by", models.CharField(blank=True, max_length=64, null=True, verbose_name="创建人")),
                ("expires_at", models.DateTimeField(blank=True, null=True, verbose_name="过期时间")),
                ("error_message", models.CharField(blank=True, max_length=255, null=True, verbose_name="错误信息")),
                ("creator", models.ForeignKey(db_constraint=False, help_text="创建人", null=True, on_delete=django.db.models.deletion.SET_NULL, related_query_name="creator_query", to=settings.AUTH_USER_MODEL, verbose_name="创建人")),
            ],
            options={
                "verbose_name": "咖啡导出任务",
                "verbose_name_plural": "咖啡导出任务",
                "db_table": "dvadmin_coffee_export_job",
            },
        ),
        migrations.AddIndex(
            model_name="exportjob",
            index=models.Index(fields=["export_type", "status"], name="dvadmin_cof_export__62f054_idx"),
        ),
        migrations.AddIndex(
            model_name="exportjob",
            index=models.Index(fields=["created_by", "create_datetime"], name="dvadmin_cof_created_81275b_idx"),
        ),
    ]
