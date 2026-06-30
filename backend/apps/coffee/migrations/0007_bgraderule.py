from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("coffee", "0006_exportjob"),
    ]

    operations = [
        migrations.CreateModel(
            name="BGradeRule",
            fields=[
                ("id", models.BigAutoField(help_text="Id", primary_key=True, serialize=False, verbose_name="Id")),
                ("description", models.CharField(blank=True, help_text="描述", max_length=255, null=True, verbose_name="描述")),
                ("modifier", models.CharField(blank=True, help_text="修改人", max_length=255, null=True, verbose_name="修改人")),
                ("dept_belong_id", models.CharField(blank=True, help_text="数据归属部门", max_length=255, null=True, verbose_name="数据归属部门")),
                ("update_datetime", models.DateTimeField(auto_now=True, help_text="修改时间", null=True, verbose_name="修改时间")),
                ("create_datetime", models.DateTimeField(auto_now_add=True, help_text="创建时间", null=True, verbose_name="创建时间")),
                ("rule_code", models.CharField(db_index=True, max_length=64, unique=True, verbose_name="规则编号")),
                ("rule_name", models.CharField(max_length=128, verbose_name="规则名称")),
                ("task_code", models.CharField(db_index=True, max_length=64, verbose_name="适用任务")),
                ("metric", models.CharField(choices=[("approved_event_count", "通过事件数量"), ("returned_event_count", "退回事件数量"), ("submitted_event_count", "已提交事件数量")], max_length=64, verbose_name="指标")),
                ("min_count", models.PositiveIntegerField(blank=True, null=True, verbose_name="最小数量")),
                ("max_count", models.PositiveIntegerField(blank=True, null=True, verbose_name="最大数量")),
                ("block_level", models.CharField(choices=[("blocking", "阻断"), ("warning", "警告")], default="blocking", max_length=32, verbose_name="阻断级别")),
                ("enabled", models.BooleanField(default=True, verbose_name="启用状态")),
                ("version", models.PositiveIntegerField(default=1, verbose_name="版本")),
                ("creator", models.ForeignKey(db_constraint=False, help_text="创建人", null=True, on_delete=django.db.models.deletion.SET_NULL, related_query_name="creator_query", to=settings.AUTH_USER_MODEL, verbose_name="创建人")),
            ],
            options={
                "verbose_name": "咖啡B级数量规则",
                "verbose_name_plural": "咖啡B级数量规则",
                "db_table": "dvadmin_coffee_b_grade_rule",
                "unique_together": {("task_code", "rule_name", "version")},
            },
        ),
        migrations.AddIndex(
            model_name="bgraderule",
            index=models.Index(fields=["task_code", "enabled"], name="dvadmin_cof_task_co_449854_idx"),
        ),
        migrations.AddIndex(
            model_name="bgraderule",
            index=models.Index(fields=["metric", "block_level"], name="dvadmin_cof_metric_3c98b7_idx"),
        ),
    ]
