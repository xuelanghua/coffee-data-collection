from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("coffee", "0004_photouploadchunk"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProviderConfig",
            fields=[
                ("id", models.BigAutoField(help_text="Id", primary_key=True, serialize=False, verbose_name="Id")),
                ("description", models.CharField(blank=True, help_text="描述", max_length=255, null=True, verbose_name="描述")),
                ("modifier", models.CharField(blank=True, help_text="修改人", max_length=255, null=True, verbose_name="修改人")),
                ("dept_belong_id", models.CharField(blank=True, help_text="数据归属部门", max_length=255, null=True, verbose_name="数据归属部门")),
                ("update_datetime", models.DateTimeField(auto_now=True, help_text="修改时间", null=True, verbose_name="修改时间")),
                ("create_datetime", models.DateTimeField(auto_now_add=True, help_text="创建时间", null=True, verbose_name="创建时间")),
                ("provider_type", models.CharField(choices=[("map", "地图"), ("weather", "天气"), ("ocr", "OCR"), ("storage", "存储")], db_index=True, max_length=32, verbose_name="Provider类型")),
                ("provider_name", models.CharField(db_index=True, max_length=64, verbose_name="Provider名称")),
                ("display_name", models.CharField(max_length=128, verbose_name="显示名称")),
                ("enabled", models.BooleanField(default=False, verbose_name="启用状态")),
                ("priority", models.PositiveIntegerField(default=100, verbose_name="优先级")),
                ("timeout_ms", models.PositiveIntegerField(default=15000, verbose_name="超时毫秒")),
                ("rate_limit_per_minute", models.PositiveIntegerField(default=60, verbose_name="每分钟限流")),
                ("config_status", models.CharField(choices=[("missing", "未配置"), ("configured", "已配置"), ("tested", "测试通过"), ("blocked", "阻塞")], default="missing", max_length=32, verbose_name="配置状态")),
                ("config_json", models.JSONField(blank=True, default=dict, verbose_name="配置JSON")),
                ("secret_fields", models.JSONField(blank=True, default=list, verbose_name="敏感字段")),
                ("version", models.PositiveIntegerField(default=1, verbose_name="版本")),
                ("creator", models.ForeignKey(db_constraint=False, help_text="创建人", null=True, on_delete=django.db.models.deletion.SET_NULL, related_query_name="creator_query", to=settings.AUTH_USER_MODEL, verbose_name="创建人")),
            ],
            options={
                "verbose_name": "咖啡Provider配置",
                "verbose_name_plural": "咖啡Provider配置",
                "db_table": "dvadmin_coffee_provider_config",
                "unique_together": {("provider_type", "provider_name", "version")},
            },
        ),
        migrations.AddIndex(
            model_name="providerconfig",
            index=models.Index(fields=["provider_type", "enabled"], name="dvadmin_cof_provide_217f24_idx"),
        ),
        migrations.AddIndex(
            model_name="providerconfig",
            index=models.Index(fields=["config_status", "priority"], name="dvadmin_cof_config__22263b_idx"),
        ),
    ]
