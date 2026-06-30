from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("coffee", "0007_bgraderule"),
    ]

    operations = [
        migrations.CreateModel(
            name="PhotoAnnotation",
            fields=[
                ("id", models.BigAutoField(help_text="Id", primary_key=True, serialize=False, verbose_name="Id")),
                ("description", models.CharField(blank=True, help_text="描述", max_length=255, null=True, verbose_name="描述")),
                ("modifier", models.CharField(blank=True, help_text="修改人", max_length=255, null=True, verbose_name="修改人")),
                ("dept_belong_id", models.CharField(blank=True, help_text="数据归属部门", max_length=255, null=True, verbose_name="数据归属部门")),
                ("update_datetime", models.DateTimeField(auto_now=True, help_text="修改时间", null=True, verbose_name="修改时间")),
                ("create_datetime", models.DateTimeField(auto_now_add=True, help_text="创建时间", null=True, verbose_name="创建时间")),
                ("annotation_id", models.CharField(db_index=True, max_length=64, verbose_name="标注ID")),
                ("label", models.CharField(max_length=64, verbose_name="标签")),
                ("shape_type", models.CharField(choices=[("bbox", "矩形框"), ("polygon", "多边形"), ("point", "点")], default="bbox", max_length=32, verbose_name="形状类型")),
                ("geometry_json", models.JSONField(default=dict, verbose_name="标注几何")),
                ("version", models.PositiveIntegerField(default=1, verbose_name="版本")),
                ("is_latest", models.BooleanField(default=True, verbose_name="最新版本")),
                ("source", models.CharField(choices=[("manual", "人工标注")], default="manual", max_length=32, verbose_name="来源")),
                ("annotated_by", models.CharField(blank=True, max_length=64, null=True, verbose_name="标注人")),
                ("note", models.CharField(blank=True, max_length=255, null=True, verbose_name="备注")),
                ("creator", models.ForeignKey(db_constraint=False, help_text="创建人", null=True, on_delete=django.db.models.deletion.SET_NULL, related_query_name="creator_query", to=settings.AUTH_USER_MODEL, verbose_name="创建人")),
                ("photo", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="annotations", to="coffee.photoasset", verbose_name="照片")),
            ],
            options={
                "verbose_name": "咖啡照片人工标注",
                "verbose_name_plural": "咖啡照片人工标注",
                "db_table": "dvadmin_coffee_photo_annotation",
                "unique_together": {("annotation_id", "version")},
            },
        ),
        migrations.AddIndex(
            model_name="photoannotation",
            index=models.Index(fields=["photo", "label", "is_latest"], name="dvadmin_cof_photo_i_7fa8b9_idx"),
        ),
        migrations.AddIndex(
            model_name="photoannotation",
            index=models.Index(fields=["photo", "annotation_id", "version"], name="dvadmin_cof_photo_i_25d78f_idx"),
        ),
    ]
