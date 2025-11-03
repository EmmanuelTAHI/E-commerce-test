from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Home
    path("", views.home, name="home"),
    # Products
    path("products/", views.product_list, name="product_list"),
    path("products/<slug:slug>/", views.product_detail, name="product_detail"),
    # Cart
    path("cart/", views.cart, name="cart"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/<int:cart_id>/", views.update_cart, name="update_cart"),
    path("cart/remove/<int:cart_id>/", views.remove_from_cart, name="remove_from_cart"),
    # Checkout
    path("checkout/", views.checkout, name="checkout"),
    path("payment/<int:order_id>/", views.payment, name="payment"),
    # Orders
    path("orders/", views.order_history, name="order_history"),
    path("orders/<int:order_id>/", views.order_detail, name="order_detail"),
    # Account
    path("account/", views.account, name="account"),
    # Authentication
    path("login/", views.login_view, name="login"),
    path("register/", views.register, name="register"),
    path("verify-email/", views.verify_email, name="verify_email"),
    path("logout/", views.logout_view, name="logout"),
    # Reviews
    path("products/<int:product_id>/review/", views.add_review, name="add_review"),
    # Admin Dashboard
    path("dashboard/", views.dashboard, name="dashboard"),
    # Seller routes
    path("seller/register/", views.register_seller, name="register_seller"),
    path("seller/dashboard/", views.seller_dashboard, name="seller_dashboard"),
    path(
        "seller/products/add/",
        views.add_product_by_seller,
        name="add_product_by_seller",
    ),
    path(
        "seller/products/<int:product_id>/edit/",
        views.edit_product_by_seller,
        name="edit_product_by_seller",
    ),
]
