import unittest
from pathlib import Path


class DeliveryDocumentationIndexTests(unittest.TestCase):
    def setUp(self):
        self.index = Path("docs/delivery/交付文档索引.md")

    def test_delivery_documentation_index_lists_required_handover_materials(self):
        self.assertTrue(self.index.exists(), "docs/delivery/交付文档索引.md must exist")
        content = self.index.read_text(encoding="utf-8")

        for heading in (
            "交付范围",
            "阶段门禁",
            "运行与验证",
            "真实服务门禁",
            "证据报告",
            "BLOCKED",
        ):
            self.assertIn(heading, content)

        for required_path in (
            "docs/manual/普洱咖啡数据采集系统开发任务书-UAIDF重写版.md",
            "docs/design/系统架构设计.md",
            "docs/design/数据库设计.md",
            "docs/api/API契约说明.md",
            "docs/ui/App页面设计说明.md",
            "docs/ui/Web管理端页面设计说明.md",
            "automation/acceptance.yaml",
            "automation/state.json",
            "automation/runbook.md",
            "scripts/verify-all.sh",
            "scripts/check-delivery-gates.py",
            "reports/development/S3-full-local-verify-dry-run.md",
        ):
            self.assertIn(required_path, content)
            self.assertTrue(Path(required_path).exists(), f"{required_path} referenced by delivery index must exist")


if __name__ == "__main__":
    unittest.main()
