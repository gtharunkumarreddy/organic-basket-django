from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from . import views

app_name = "store"

urlpatterns = [
    path("", views.home, name="home"),
    path("products/", views.product_list, name="product_list"),
    path("products/<int:pk>/", views.product_detail, name="product_detail"),
    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path(
        "cart/update/<int:item_id>/",
        views.update_cart_item,
        name="update_cart_item",
    ),
    path(
        "cart/remove/<int:item_id>/",
        views.remove_cart_item,
        name="remove_cart_item",
    ),
    path("checkout/", views.checkout, name="checkout"),
    path("checkout/upi/<int:pk>/", views.upi_payment, name="upi_payment"),
    path("checkout/upi/<int:pk>/done/", views.upi_payment_done, name="upi_payment_done"),
    path("payment/verify/", views.payment_verify, name="payment_verify"),
    path("orders/", views.order_list, name="order_list"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),
    path("dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("dashboard/orders/<int:pk>/approve/", views.approve_order, name="approve_order"),
    path("auth/register/", views.register_view, name="register"),
    path("auth/login/", views.login_view, name="login"),
    path("auth/logout/", views.logout_view, name="logout"),
    # JWT API endpoints
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
