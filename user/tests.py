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
