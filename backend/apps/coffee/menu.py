"""Coffee menu and role bootstrap helpers for django-vue3-admin.

The project keeps framework authentication, menu, button permission and data
range mechanisms intact. These helpers only register the coffee business menu
tree and four business roles into the existing dvadmin system tables.
"""

from dvadmin.system.models import Menu, MenuButton, Role, RoleMenuButtonPermission, RoleMenuPermission


COFFEE_MENU_DEFINITIONS = (
    {
        "web_path": "/coffee/events",
        "component_name": "coffeeEvent",
        "name": "采集事件",
        "name_en": "Collection Events",
        "component": "coffee/event/index",
        "sort": 1,
        "buttons": (
            ("查询", "Search", "coffee:event:Search", "/api/coffee/events/", 0),
            ("详情", "Detail", "coffee:event:Detail", "/api/coffee/events/{event_id}/", 0),
            ("审核通过", "Approve", "coffee:event:Approve", "/api/coffee/events/{event_id}/review/approve/", 1),
            ("审核退回", "Return", "coffee:event:Return", "/api/coffee/events/{event_id}/review/return/", 1),
            ("批量通过", "Bulk Approve", "coffee:event:BulkApprove", "/api/coffee/events/review/bulk-approve/", 1),
            ("批量退回", "Bulk Return", "coffee:event:BulkReturn", "/api/coffee/events/review/bulk-return/", 1),
        ),
    },
    {
        "web_path": "/coffee/photos",
        "component_name": "coffeePhoto",
        "name": "照片资产",
        "name_en": "Photo Assets",
        "component": "coffee/photo/index",
        "sort": 2,
        "buttons": (
            ("查询", "Search", "coffee:photo:Search", "/api/coffee/photos/", 0),
            ("审核通过", "Approve", "coffee:photo:Approve", "/api/coffee/photos/{photo_id}/review/", 1),
            ("退回补拍", "Return", "coffee:photo:Return", "/api/coffee/photos/{photo_id}/review/", 1),
        ),
    },
    {
        "web_path": "/coffee/ocr",
        "component_name": "coffeeOcr",
        "name": "OCR 校正",
        "name_en": "OCR Correction",
        "component": "coffee/ocr/index",
        "sort": 3,
        "buttons": (
            ("查询", "Search", "coffee:ocr:Search", "/api/coffee/ocr/jobs/", 0),
            ("保存校正", "Correct", "coffee:ocr:Correct", "/api/coffee/ocr-results/{id}/corrections/", 1),
        ),
    },
    {
        "web_path": "/coffee/provider",
        "component_name": "coffeeProvider",
        "name": "Provider 配置",
        "name_en": "Provider Config",
        "component": "coffee/provider/index",
        "sort": 4,
        "buttons": (
            ("查询", "Search", "coffee:provider:Search", "/api/coffee/provider-configs/", 0),
            ("新增配置", "Create", "coffee:provider:Create", "/api/coffee/provider-configs/", 1),
            ("编辑配置", "Edit", "coffee:provider:Edit", "/api/coffee/provider-configs/{id}/", 1),
            ("删除配置", "Delete", "coffee:provider:Delete", "/api/coffee/provider-configs/{id}/", 1),
            ("连接测试", "Test", "coffee:provider:Test", "/api/coffee/provider-configs/{id}/test/", 1),
        ),
    },
    {
        "web_path": "/coffee/statistics",
        "component_name": "coffeeStatistics",
        "name": "统计报表",
        "name_en": "Statistics",
        "component": "coffee/statistics/index",
        "sort": 5,
        "buttons": (
            ("采集进度", "Progress", "coffee:statistics:Progress", "/api/coffee/statistics/progress/", 0),
            ("质量统计", "Quality", "coffee:statistics:Quality", "/api/coffee/statistics/quality/", 0),
            ("绩效统计", "Performance", "coffee:statistics:Performance", "/api/coffee/statistics/performance/", 0),
        ),
    },
    {
        "web_path": "/coffee/export",
        "component_name": "coffeeExport",
        "name": "导出任务",
        "name_en": "Export Jobs",
        "component": "coffee/export/index",
        "sort": 6,
        "buttons": (
            ("查询", "Search", "coffee:export:Search", "/api/coffee/exports/", 0),
            ("新建导出", "Create", "coffee:export:Create", "/api/coffee/exports/", 1),
            ("取消导出", "Cancel", "coffee:export:Cancel", "/api/coffee/exports/{id}/cancel/", 1),
        ),
    },
    {
        "web_path": "/coffee/b-grade",
        "component_name": "coffeeBGrade",
        "name": "B 级规则",
        "name_en": "B Grade Rules",
        "component": "coffee/b-grade/index",
        "sort": 7,
        "buttons": (
            ("查询", "Search", "coffee:b-grade:Search", "/api/coffee/b-grade-rules/", 0),
            ("新增规则", "Create", "coffee:b-grade:Create", "/api/coffee/b-grade-rules/", 1),
            ("编辑规则", "Edit", "coffee:b-grade:Edit", "/api/coffee/b-grade-rules/{rule_code}/", 1),
            ("删除规则", "Delete", "coffee:b-grade:Delete", "/api/coffee/b-grade-rules/{rule_code}/", 1),
            ("模拟检查", "Check", "coffee:b-grade:Check", "/api/coffee/b-grade-rules/{rule_code}/check/", 1),
        ),
    },
)

COFFEE_ROLE_DEFINITIONS = {
    "coffee_collector": {
        "name": "咖啡采集员",
        "sort": 31,
        "menus": {"/coffee", "/coffee/events"},
        "buttons": {"coffee:event:Search", "coffee:event:Detail"},
        "data_range": 0,
    },
    "coffee_reviewer": {
        "name": "咖啡审核员",
        "sort": 32,
        "menus": {"/coffee", "/coffee/events", "/coffee/photos", "/coffee/ocr", "/coffee/b-grade"},
        "buttons": {
            "coffee:event:Search",
            "coffee:event:Detail",
            "coffee:event:Approve",
            "coffee:event:Return",
            "coffee:event:BulkApprove",
            "coffee:event:BulkReturn",
            "coffee:photo:Search",
            "coffee:photo:Approve",
            "coffee:photo:Return",
            "coffee:ocr:Search",
            "coffee:ocr:Correct",
            "coffee:b-grade:Search",
            "coffee:b-grade:Check",
        },
        "data_range": 1,
    },
    "coffee_admin": {
        "name": "咖啡管理员",
        "sort": 33,
        "menus": {"/coffee", "/coffee/events", "/coffee/photos", "/coffee/ocr", "/coffee/provider", "/coffee/statistics", "/coffee/export", "/coffee/b-grade"},
        "buttons": "all",
        "data_range": 3,
    },
    "coffee_viewer": {
        "name": "咖啡查看员",
        "sort": 34,
        "menus": {"/coffee", "/coffee/events", "/coffee/photos", "/coffee/statistics", "/coffee/export"},
        "buttons": {
            "coffee:event:Search",
            "coffee:event:Detail",
            "coffee:photo:Search",
            "coffee:statistics:Progress",
            "coffee:statistics:Quality",
            "coffee:statistics:Performance",
            "coffee:export:Search",
            "coffee:export:Create",
        },
        "data_range": 0,
    },
}


def ensure_coffee_menus():
    """Create or update the coffee Web menu tree and button permissions."""
    catalog, _ = Menu.objects.update_or_create(
        web_path="/coffee",
        component_name="",
        defaults={
            "name": "咖啡采集",
            "name_en": "Coffee Collection",
            "name_zh_tw": "咖啡採集",
            "icon": "iconfont icon-shuju",
            "sort": 30,
            "is_catalog": True,
            "component": "",
            "status": True,
            "cache": False,
            "visible": True,
        },
    )
    menu_ids = {"catalog_id": catalog.id}
    for definition in COFFEE_MENU_DEFINITIONS:
        menu, _ = Menu.objects.update_or_create(
            web_path=definition["web_path"],
            component_name=definition["component_name"],
            defaults={
                "parent": catalog,
                "name": definition["name"],
                "name_en": definition["name_en"],
                "name_zh_tw": definition["name"],
                "icon": "iconfont icon-shuju",
                "sort": definition["sort"],
                "is_catalog": False,
                "component": definition["component"],
                "status": True,
                "cache": False,
                "visible": True,
            },
        )
        if definition["web_path"] == "/coffee/events":
            menu_ids["event_menu_id"] = menu.id
        for name, name_en, value, api, method in definition["buttons"]:
            MenuButton.objects.update_or_create(
                value=value,
                defaults={
                    "menu": menu,
                    "name": name,
                    "name_en": name_en,
                    "name_zh_tw": name,
                    "api": api,
                    "method": method,
                },
            )
    return menu_ids


def ensure_coffee_role_matrix():
    """Create coffee roles and bind their menu/button/data-scope permissions."""
    ensure_coffee_menus()
    menus_by_path = {menu.web_path: menu for menu in Menu.objects.filter(web_path__startswith="/coffee")}
    all_button_values = set(MenuButton.objects.filter(menu__web_path__startswith="/coffee").values_list("value", flat=True))
    buttons_by_value = {button.value: button for button in MenuButton.objects.filter(value__in=all_button_values)}

    role_keys = []
    for key, definition in COFFEE_ROLE_DEFINITIONS.items():
        role, _ = Role.objects.update_or_create(
            key=key,
            defaults={
                "name": definition["name"],
                "sort": definition["sort"],
                "status": True,
            },
        )
        role_keys.append(key)

        for menu_path in definition["menus"]:
            RoleMenuPermission.objects.update_or_create(role=role, menu=menus_by_path[menu_path], defaults={})

        button_values = all_button_values if definition["buttons"] == "all" else definition["buttons"]
        for value in button_values:
            RoleMenuButtonPermission.objects.update_or_create(
                role=role,
                menu_button=buttons_by_value[value],
                defaults={"data_range": definition["data_range"]},
            )

    return {"roles": role_keys}
