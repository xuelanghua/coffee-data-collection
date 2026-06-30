from django.test import TestCase

from apps.coffee.menu import ensure_coffee_menus, ensure_coffee_role_matrix
from dvadmin.system.models import Menu, MenuButton, Role, RoleMenuButtonPermission, RoleMenuPermission


class CoffeeMenuInitializationTests(TestCase):
    def test_ensure_coffee_menus_creates_catalog_event_menu_and_review_buttons_idempotently(self):
        first = ensure_coffee_menus()
        second = ensure_coffee_menus()

        catalog = Menu.objects.get(web_path="/coffee")
        event_menu = Menu.objects.get(web_path="/coffee/events")

        self.assertEqual(first["event_menu_id"], second["event_menu_id"])
        self.assertTrue(catalog.is_catalog)
        self.assertEqual(event_menu.parent, catalog)
        self.assertEqual(event_menu.component, "coffee/event/index")
        self.assertEqual(event_menu.component_name, "coffeeEvent")
        self.assertTrue(MenuButton.objects.filter(menu=event_menu, value="coffee:event:Search", api="/api/coffee/events/", method=0).exists())
        self.assertTrue(MenuButton.objects.filter(menu=event_menu, value="coffee:event:Approve", api="/api/coffee/events/{event_id}/review/approve/", method=1).exists())
        self.assertTrue(MenuButton.objects.filter(menu=event_menu, value="coffee:event:BulkReturn", api="/api/coffee/events/review/bulk-return/", method=1).exists())
        self.assertEqual(Menu.objects.filter(web_path="/coffee/events").count(), 1)

    def test_ensure_coffee_role_matrix_creates_roles_menus_and_button_permissions(self):
        result = ensure_coffee_role_matrix()

        expected_roles = {
            "coffee_collector": {"menus": {"/coffee", "/coffee/events"}, "data_range": 0},
            "coffee_reviewer": {"menus": {"/coffee", "/coffee/events", "/coffee/photos", "/coffee/ocr", "/coffee/b-grade"}, "data_range": 1},
            "coffee_admin": {
                "menus": {"/coffee", "/coffee/events", "/coffee/photos", "/coffee/ocr", "/coffee/provider", "/coffee/statistics", "/coffee/export", "/coffee/b-grade"},
                "data_range": 3,
            },
            "coffee_viewer": {"menus": {"/coffee", "/coffee/events", "/coffee/photos", "/coffee/statistics", "/coffee/export"}, "data_range": 0},
        }

        self.assertEqual(set(result["roles"]), set(expected_roles))
        for role_key, expectation in expected_roles.items():
            role = Role.objects.get(key=role_key)
            menu_paths = set(RoleMenuPermission.objects.filter(role=role).values_list("menu__web_path", flat=True))
            self.assertEqual(menu_paths, expectation["menus"])

        collector = Role.objects.get(key="coffee_collector")
        collector_buttons = set(RoleMenuButtonPermission.objects.filter(role=collector).values_list("menu_button__value", flat=True))
        self.assertEqual(collector_buttons, {"coffee:event:Search", "coffee:event:Detail"})

        reviewer = Role.objects.get(key="coffee_reviewer")
        reviewer_buttons = set(RoleMenuButtonPermission.objects.filter(role=reviewer).values_list("menu_button__value", flat=True))
        self.assertIn("coffee:event:Approve", reviewer_buttons)
        self.assertIn("coffee:photo:Return", reviewer_buttons)
        self.assertIn("coffee:ocr:Correct", reviewer_buttons)
        self.assertNotIn("coffee:provider:Create", reviewer_buttons)

        admin = Role.objects.get(key="coffee_admin")
        all_button_values = set(MenuButton.objects.filter(menu__web_path__startswith="/coffee").values_list("value", flat=True))
        admin_buttons = set(RoleMenuButtonPermission.objects.filter(role=admin).values_list("menu_button__value", flat=True))
        self.assertEqual(admin_buttons, all_button_values)

        viewer = Role.objects.get(key="coffee_viewer")
        viewer_buttons = set(RoleMenuButtonPermission.objects.filter(role=viewer).values_list("menu_button__value", flat=True))
        self.assertIn("coffee:statistics:Performance", viewer_buttons)
        self.assertNotIn("coffee:event:Approve", viewer_buttons)
        self.assertNotIn("coffee:provider:Create", viewer_buttons)

        reviewer_ranges = set(RoleMenuButtonPermission.objects.filter(role=reviewer).values_list("data_range", flat=True))
        admin_ranges = set(RoleMenuButtonPermission.objects.filter(role=admin).values_list("data_range", flat=True))
        self.assertEqual(reviewer_ranges, {expected_roles["coffee_reviewer"]["data_range"]})
        self.assertEqual(admin_ranges, {expected_roles["coffee_admin"]["data_range"]})
