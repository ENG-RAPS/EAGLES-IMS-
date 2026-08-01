from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from store.models import Category, Product, Supplier
from user.models import Branch, Profile


class ProductCreationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='storeuser', password='StrongPass123!')
        self.branch = Branch.objects.create(name='Store Branch', location='HQ')
        Profile.objects.create(user=self.user, branch=self.branch, role='STORE_OFFICER')
        self.category = Category.objects.create(name='Consumables')
        self.supplier = Supplier.objects.create(company_name='Acme Supplies', phone='0712345678')
        self.client.force_login(self.user)

    def test_product_create_auto_generates_item_code_when_missing(self):
        response = self.client.post(reverse('store:product_create'), {
            'name': 'Gloves',
            'category': self.category.id,
            'description': 'Test stock item',
            'unit': 'piece',
            'quantity': 10,
            'minimum_stock_level': 3,
            'supplier': self.supplier.id,
            'storage_location': 'Shelf A',
        })

        self.assertEqual(response.status_code, 302)
        product = Product.objects.get(name='Gloves')
        self.assertTrue(product.item_code)
        self.assertNotEqual(product.item_code, '')
