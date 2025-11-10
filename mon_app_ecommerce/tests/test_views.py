from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from mon_app_ecommerce.models import (
    Category,
    Product,
    Customer,
    Seller,
    Cart,
    Order
)

class ViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.customer = Customer.objects.create(user=self.user)
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            price=100,
            category=self.category,
            stock=10,
            description='Test description'
        )

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mon_app_ecommerce/home.html')
        self.assertTrue('featured_products' in response.context)
        self.assertTrue('categories' in response.context)

    def test_product_list_view(self):
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mon_app_ecommerce/product_list.html')
        self.assertTrue('products' in response.context)

    def test_product_detail_view(self):
        response = self.client.get(
            reverse('product_detail', kwargs={'slug': self.product.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mon_app_ecommerce/product_detail.html')
        self.assertEqual(response.context['product'], self.product)

    def test_cart_view_authenticated(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mon_app_ecommerce/cart.html')

    def test_cart_view_unauthenticated(self):
        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/cart/')

    def test_add_to_cart(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('add_to_cart', kwargs={'product_id': self.product.id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Cart.objects.filter(
                customer=self.customer,
                product=self.product
            ).exists()
        )

class AuthenticationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'phone': '1234567890'
        }

    def test_user_registration(self):
        response = self.client.post(self.register_url, self.user_data, follow=True)
        self.assertEqual(response.status_code, 200)
        created_user = User.objects.filter(username='testuser').first()
        self.assertIsNotNone(created_user)
        self.assertEqual(created_user.email, 'test@example.com')

    def test_user_login(self):
        User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue('_auth_user_id' in self.client.session)

class CheckoutProcessTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.customer = Customer.objects.create(user=self.user)
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            price=100,
            category=self.category,
            stock=10
        )
        self.client.login(username='testuser', password='testpass123')

    def test_checkout_process(self):
        # Add item to cart
        self.client.get(
            reverse('add_to_cart', kwargs={'product_id': self.product.id})
        )
        
        # Test checkout view
        response = self.client.get(reverse('checkout'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mon_app_ecommerce/checkout.html')

        # Test order creation
        shipping_data = {
            'street_address': '123 Test St',
            'city': 'Test City',
            'state': 'Test State',
            'postal_code': '12345',
            'country': "Côte d'Ivoire"
        }
        response = self.client.post(reverse('checkout'), shipping_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Order.objects.filter(customer=self.customer).exists()
        )