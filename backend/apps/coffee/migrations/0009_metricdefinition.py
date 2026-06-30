from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("coffee", "0008_photoannotation"),
    ]

    operations = [
        migrations.CreateModel(
            name="MetricDefinition",
            fields=[
                ("id", models.BigAutoField(help_text="Id", primary_key=True, serialize=False, verbose_name="Id")),
                ("description", models.CharField(blank=True, help_text="描述", max_length=255, null=True, verbose_name="描述")),
                ("modifier", models.CharField(blank=True, help_text="修改人", max_length=255, null=True, verbose_name="修改人")),
                ("dept_belong_id", models.CharField(blank=True, help_text="数据归属部门", max_length=255, null=True, verbose_name="数据归属部门")),
                ("update_datetime", models.DateTimeField(auto_now=True, help_text="修改时间", null=True, verbose_name="修改时间")),
                ("create_datetime", models.DateTimeField(auto_now_add=True, help_text="创建时间", null=True, verbose_name="创建时间")),
                ("metric_code", models.CharField(db_index=True, max_length=64, verbose_name="指标编码")),
                ("metric_name", models.CharField(max_length=128, verbose_name="指标名称")),
                ("metric_group", models.CharField(choices=[("progress", "采集进度"), ("quality", "质量统计"), ("performance", "绩效统计")], db_index=True, max_length=32, verbose_name="指标分组")),
                ("calculation_method", models.CharField(max_length=255, verbose_name="计算口径")),
                ("unit", models.CharField(blank=True, max_length=32, null=True, verbose_name="单位")),
                ("enabled", models.BooleanField(default=True, verbose_name="启用状态")),
                ("version", models.PositiveIntegerField(default=1, verbose_name="版本")),
                ("creator", models.ForeignKey(db_constraint=False, help_text="创建人", null=True, on_delete=django.db.models.deletion.SET_NULL, related_query_name="creator_query", to=settings.AUTH_USER_MODEL, verbose_name="创建人")),
            ],
            options={
                "verbose_name": "咖啡统计指标口径",
                "verbose_name_plural": "咖啡统计指标口径",
                "db_table": "dvadmin_coffee_metric_definition",
                "unique_together": {("metric_code", "version")},
            },
        ),
        migrations.AddIndex(
            model_name="metricdefinition",
            index=models.Index(fields=["metric_group", "enabled"], name="dvadmin_cof_metric__e8cf3f_idx"),
        ),
        migrations.AddIndex(
            model_name="metricdefinition",
            index=models.Index(fields=["metric_code", "version"], name="dvadmin_cof_metric__31ad99_idx"),
        ),
    ]
