from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("coffee", "0003_qualityreview"),
    ]

    operations = [
        migrations.CreateModel(
            name="PhotoUploadChunk",
            fields=[
                ("id", models.BigAutoField(help_text="Id", primary_key=True, serialize=False, verbose_name="Id")),
                ("description", models.CharField(blank=True, help_text="描述", max_length=255, null=True, verbose_name="描述")),
                ("modifier", models.CharField(blank=True, help_text="修改人", max_length=255, null=True, verbose_name="修改人")),
                ("dept_belong_id", models.CharField(blank=True, help_text="数据归属部门", max_length=255, null=True, verbose_name="数据归属部门")),
                ("update_datetime", models.DateTimeField(auto_now=True, help_text="修改时间", null=True, verbose_name="修改时间")),
                ("create_datetime", models.DateTimeField(auto_now_add=True, help_text="创建时间", null=True, verbose_name="创建时间")),
                ("upload_session_id", models.CharField(db_index=True, max_length=64, verbose_name="上传会话ID")),
                ("chunk_index", models.PositiveIntegerField(verbose_name="分片序号")),
                ("chunk_hash", models.CharField(max_length=128, verbose_name="分片Hash")),
                ("chunk_size", models.PositiveIntegerField(verbose_name="分片大小")),
                ("status", models.CharField(default="uploaded", max_length=32, verbose_name="状态")),
                ("uploaded_at", models.DateTimeField(blank=True, null=True, verbose_name="上传时间")),
                ("creator", models.ForeignKey(db_constraint=False, help_text="创建人", null=True, on_delete=django.db.models.deletion.SET_NULL, related_query_name="creator_query", to=settings.AUTH_USER_MODEL, verbose_name="创建人")),
                ("photo", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="upload_chunks", to="coffee.photoasset", verbose_name="照片")),
            ],
            options={
                "verbose_name": "咖啡照片上传分片",
                "verbose_name_plural": "咖啡照片上传分片",
                "db_table": "dvadmin_coffee_photo_upload_chunk",
                "unique_together": {("photo", "chunk_index")},
            },
        ),
        migrations.AddIndex(
            model_name="photouploadchunk",
            index=models.Index(fields=["photo", "status"], name="dvadmin_cof_photo_i_44f4b2_idx"),
        ),
        migrations.AddIndex(
            model_name="photouploadchunk",
            index=models.Index(fields=["upload_session_id", "chunk_index"], name="dvadmin_cof_upload__c3c4aa_idx"),
        ),
    ]
