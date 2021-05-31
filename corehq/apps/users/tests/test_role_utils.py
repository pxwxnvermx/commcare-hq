from django.test import TestCase

from corehq.apps.users.models import SQLUserRole, Permissions, UserRolePresets
from corehq.apps.users.role_utils import (
    get_or_create_role_with_permissions,
    init_domain_with_presets,
    reset_initial_roles_for_domain,
    archive_custom_roles_for_domain,
    unarchive_roles_for_domain,
    get_custom_roles_for_domain
)


class RoleUtilsTests(TestCase):
    domain = 'role-utils'

    @classmethod
    def setUpTestData(cls):
        cls.role1_permissions = Permissions(edit_web_users=True)
        cls.role1 = SQLUserRole.create(cls.domain, 'role1', permissions=cls.role1_permissions)

    @classmethod
    def tearDownClass(cls):
        for role in SQLUserRole.objects.get_by_domain(cls.domain):
            role.delete()
        super().tearDownClass()

    def test_get_or_create_role_with_permissions_create(self):
        permissions = Permissions(view_web_users=True)
        role = get_or_create_role_with_permissions(self.domain, 'new_role', permissions)
        self.assertNotEqual(role.get_id, self.role1.get_id)
        self.assertEqual(role.name, 'new_role')

    def test_get_or_create_role_with_permissions_get_existing(self):
        role = get_or_create_role_with_permissions(self.domain, 'new_role', self.role1_permissions)
        self.assertEqual(role.get_id, self.role1.get_id)
        self.assertEqual(role.name, 'role1')

    def test_init_domain_with_presets(self):
        self.addCleanup(self._delete_presets)
        init_domain_with_presets(self.domain)
        role_names = set(SQLUserRole.objects.filter(domain=self.domain).values_list("name", flat=True))
        self.assertEqual(role_names, set(UserRolePresets.INITIAL_ROLES) | {'role1'})

    def test_reset_initial_roles_for_domain(self):
        self.addCleanup(self._delete_presets)
        init_domain_with_presets(self.domain)
        role = SQLUserRole.objects.get(domain=self.domain, name=UserRolePresets.APP_EDITOR)
        original_permissions = role.permissions
        role.set_permissions([])

        self.assertEqual(role.permissions.to_list(), [])

        reset_initial_roles_for_domain(self.domain)

        self.assertEqual(role.permissions, original_permissions)

    def test_archive_custom_roles_for_domain(self):
        def _unarchive_custom_role():
            self.role1.is_archived = False
            self.role1.save()

        self.addCleanup(self._delete_presets)
        self.addCleanup(_unarchive_custom_role)
        init_domain_with_presets(self.domain)

        roles = SQLUserRole.objects.get_by_domain(self.domain, include_archived=True)
        self.assertEqual(len(roles), 5)

        archive_custom_roles_for_domain(self.domain)

        roles = SQLUserRole.objects.get_by_domain(self.domain, include_archived=False)
        self.assertEqual(len(roles), 4)

    def test_unarchive_roles_for_domain(self):
        self.addCleanup(self._delete_presets)
        init_domain_with_presets(self.domain)

        for role in SQLUserRole.objects.get_by_domain(self.domain):
            role.is_archived = True
            role.save()

        unarchived_role_count = len(SQLUserRole.objects.get_by_domain(self.domain, include_archived=False))
        self.assertEqual(unarchived_role_count, 0)

        unarchive_roles_for_domain(self.domain)

        unarchived_role_count = len(SQLUserRole.objects.get_by_domain(self.domain, include_archived=False))
        self.assertEqual(unarchived_role_count, 5)

    def test_get_custom_roles_for_domain(self):
        self.addCleanup(self._delete_presets)
        init_domain_with_presets(self.domain)
        roles = get_custom_roles_for_domain(self.domain)
        self.assertEqual([role.name for role in roles], ["role1"])

    def _delete_presets(self):
        for role in SQLUserRole.objects.get_by_domain(self.domain):
            if role.id != self.role1.id:
                role.delete()
