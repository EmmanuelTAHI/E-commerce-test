from django.contrib import admin
from .models import (
    Category,
    Product,
    ProductImage,
    Customer,
    Seller,
    Address,
    Cart,
    Order,
    OrderItem,
    Review,
    EmailVerification,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "created_at"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "price",
        "final_price",
        "stock",
        "is_featured",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_featured", "is_active", "category", "created_at"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline]


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["user", "phone", "birth_date"]
    search_fields = ["user__username", "user__email", "phone"]


@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = [
        "store_name",
        "user",
        "email",
        "phone",
        "city",
        "is_verified",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_verified", "is_active", "country", "created_at"]
    search_fields = ["store_name", "user__username", "user__email", "email", "phone"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["customer", "street_address", "city", "is_default"]
    list_filter = ["country", "is_default"]


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["customer", "product", "quantity", "created_at"]
    list_filter = ["created_at"]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "order_number",
        "customer",
        "status",
        "payment_status",
        "total_amount",
        "payment_date",
        "created_at",
    ]
    list_filter = ["status", "payment_status", "created_at", "payment_date"]
    search_fields = [
        "order_number",
        "customer__user__username",
        "customer__user__email",
    ]
    inlines = [OrderItemInline]
    readonly_fields = ["payment_date", "created_at", "updated_at"]
    fieldsets = (
        (
            "Informations de base",
            {
                "fields": (
                    "order_number",
                    "customer",
                    "total_amount",
                    "shipping_address",
                    "notes",
                )
            },
        ),
        (
            "Statut",
            {"fields": ("status", "payment_status", "payment_method", "payment_date")},
        ),
        ("Dates", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["product", "customer", "rating", "created_at"]
    list_filter = ["rating", "created_at"]


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ["email", "code", "verified", "created_at"]
    list_filter = ["verified", "created_at"]
    search_fields = ["email", "code"]
