from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    discount_price = models.PositiveIntegerField(
        blank=True, null=True, validators=[MinValueValidator(0)]
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="products"
    )
    seller = models.ForeignKey(
        "Seller",
        on_delete=models.CASCADE,
        related_name="products",
        null=True,
        blank=True,
    )
    image = models.ImageField(upload_to="products/")
    stock = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def final_price(self):
        return self.discount_price if self.discount_price else self.price

    @property
    def discount_percentage(self):
        if self.discount_price and self.price:
            return int(((self.price - self.discount_price) / self.price) * 100)
        return 0

    @property
    def in_stock(self):
        return self.stock > 0


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images"
    )
    image = models.ImageField(upload_to="products/")
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.product.name} - Image"


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    birth_date = models.DateField(blank=True, null=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class Seller(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="seller_profile"
    )
    store_name = models.CharField(max_length=200)
    store_description = models.TextField(blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.TextField()
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default="Côte d'Ivoire")
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.store_name} - {self.user.username}"

    def get_total_products(self):
        return self.products.count()

    def get_active_products(self):
        return self.products.filter(is_active=True).count()

    def get_total_sales(self):
        from django.db.models import Sum, F

        # Calculer le total en multipliant price * quantity pour chaque OrderItem
        result = (
            OrderItem.objects.filter(
                product__seller=self, order__payment_status="paid"
            ).aggregate(total=Sum(F("price") * F("quantity")))["total"]
            or 0
        )
        return float(result) if result else 0


class Address(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="addresses"
    )
    street_address = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default="United States")
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Addresses"

    def __str__(self):
        return f"{self.street_address}, {self.city}"


class Cart(models.Model):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="cart_items",
        null=True,
        blank=True,
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_price(self):
        return self.product.final_price * self.quantity

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending Payment"),
        ("paid", "Paid"),
        ("failed", "Payment Failed"),
        ("refunded", "Refunded"),
    ]

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="orders"
    )
    order_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending"
    )
    total_amount = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    shipping_address = models.TextField()
    notes = models.TextField(blank=True)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    payment_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.order_number}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    price = models.PositiveIntegerField(validators=[MinValueValidator(0)])

    @property
    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class Review(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["product", "customer"]

    def __str__(self):
        return (
            f"{self.product.name} - {self.customer.user.username} ({self.rating} stars)"
        )


class EmailVerification(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} - {self.code}"
