from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from user.models import Branch, Department, Profile


class RegistrationRoleTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name='Main Branch', location='HQ')
        self.department = Department.objects.create(name='IT', branch=self.branch)

    def test_registration_keeps_the_selected_role_on_profile(self):
        response = self.client.post(reverse('user:register'), {
            'username': 'biomeduser',
            'first_name': 'Biomed',
            'last_name': 'User',
            'email': 'biomed@example.com',
            'phone': '0712345678',
            'address': 'Nairobi',
            'branch': self.branch.id,
            'department': self.department.id,
            'role': 'BIOMED_TECHNICIAN',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })

        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='biomeduser')
        self.assertFalse(user.is_active)
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.role, 'BIOMED_TECHNICIAN')
        self.assertEqual(profile.branch, self.branch)
        self.assertEqual(profile.department, self.department)


class ProfileAnd404PageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='profiletester',
            email='profile@example.com',
            password='StrongPass123!'
        )

    def test_profile_page_has_home_button(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('user:profile'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Return to Home')
        self.assertContains(response, reverse('dashboard-index'))

    def test_unknown_url_uses_custom_404_template(self):
        response = self.client.get('/this-url-does-not-exist/')

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'Page Not Found', status_code=404)
        self.assertContains(response, 'Return to Dashboard', status_code=404)
