from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from mon_app_ecommerce.models import (
    Category,
    Product,
    Customer,
    Seller,
    Cart,
    Order,
    OrderItem,
    Address
)
from decimal import Decimal

class CategoryModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Electronics",
            slug="electronics",
            description="Electronic devices"
        )

    def test_category_creation(self):
        self.assertEqual(self.category.name, "Electronics")
        self.assertEqual(self.category.slug, "electronics")
        self.assertEqual(str(self.category), "Electronics")

class ProductModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Electronics",
            slug="electronics"
        )
        self.seller = Seller.objects.create(
            user=User.objects.create(username="seller1"),
            store_name="Tech Store",
            email="seller@example.com",
            phone="1234567890",
            address="123 Seller St"
        )
        self.product = Product.objects.create(
            name="Smartphone",
            slug="smartphone",
            description="A new smartphone",
            price=1000,
            category=self.category,
            seller=self.seller,
            stock=10
        )

    def test_product_creation(self):
        self.assertEqual(self.product.name, "Smartphone")
        self.assertEqual(self.product.price, 1000)
        self.assertTrue(self.product.in_stock)

    def test_product_discount(self):
        self.product.discount_price = 800
        self.product.save()
        self.assertEqual(self.product.discount_percentage, 20)
        self.assertEqual(self.product.final_price, 800)

class CustomerModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="customer1",
            password="testpass123"
        )
        self.customer = Customer.objects.create(
            user=self.user,
            phone="1234567890"
        )

    def test_customer_creation(self):
        self.assertEqual(str(self.customer), f"{self.user.first_name} {self.user.last_name}")
        self.assertEqual(self.customer.phone, "1234567890")

class CartModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Electronics", slug="electronics")
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.customer = Customer.objects.create(user=self.user)
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            price=100,
            category=self.category,
            stock=10
        )
        self.cart = Cart.objects.create(
            customer=self.customer,
            product=self.product,
            quantity=2
        )

    def test_cart_total_price(self):
        self.assertEqual(self.cart.total_price, 200)
        
    def test_cart_string_representation(self):
        self.assertEqual(str(self.cart), "Test Product (2)")

class OrderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.customer = Customer.objects.create(user=self.user)
        self.order = Order.objects.create(
            customer=self.customer,
            order_number="ORD123",
            total_amount=500,
            shipping_address="123 Test St"
        )

    def test_order_creation(self):
        self.assertEqual(self.order.order_number, "ORD123")
        self.assertEqual(self.order.status, "pending")
        self.assertEqual(self.order.payment_status, "pending")

class OrderItemModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Electronics", slug="electronics")
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            price=100,
            category=self.category,
            stock=10
        )
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.customer = Customer.objects.create(user=self.user)
        self.order = Order.objects.create(
            customer=self.customer,
            order_number="ORD123",
            total_amount=100,
            shipping_address="123 Test St"
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            price=self.product.price
        )

    def test_order_item_creation(self):
        self.assertEqual(self.order_item.quantity, 2)
        self.assertEqual(self.order_item.price, 100)
        self.assertEqual(self.order_item.quantity * self.order_item.price, 200)