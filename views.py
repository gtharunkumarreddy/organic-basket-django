from decimal import Decimal
from urllib.parse import quote_plus

import razorpay
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, F, Count
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt

from .forms import RegisterForm
from .models import Cart, CartItem, Order, OrderItem, Product


def _get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def _build_upi_qr_url(order: Order) -> str:
    upi_id = getattr(settings, "UPI_ID", "tharunreddy153-1@okaxis")
    upi_name = getattr(settings, "UPI_NAME", "Tharun Reddy")
    amount = f"{order.total_amount:.2f}"
    upi_intent = (
        f"upi://pay?pa={quote_plus(upi_id)}&pn={quote_plus(upi_name)}"
        f"&am={amount}&cu=INR&tn={quote_plus(f'Order #{order.id}')}"
    )
    return (
        "https://api.qrserver.com/v1/create-qr-code/?size=360x360&data="
        f"{quote_plus(upi_intent)}"
    )


def home(request: HttpRequest) -> HttpResponse:
    featured_products = Product.objects.filter(is_featured=True, is_active=True)[:8]
    fruits = Product.objects.filter(category="fruit", is_active=True)[:4]
    vegetables = Product.objects.filter(category="vegetable", is_active=True)[:4]
    return render(
        request,
        "store/home.html",
        {
            "featured_products": featured_products,
            "fruits": fruits,
            "vegetables": vegetables,
        },
    )


def product_list(request: HttpRequest) -> HttpResponse:
    category = request.GET.get("category")
    products = Product.objects.filter(is_active=True)
    if category in {"fruit", "vegetable"}:
        products = products.filter(category=category)
    return render(request, "store/products.html", {"products": products, "category": category})


def product_detail(request: HttpRequest, pk: int) -> HttpResponse:
    product = get_object_or_404(Product, pk=pk, is_active=True)
    return render(request, "store/product_detail.html", {"product": product})


@login_required
def cart_detail(request: HttpRequest) -> HttpResponse:
    cart = _get_or_create_cart(request.user)
    return render(request, "store/cart.html", {"cart": cart})


@login_required
def add_to_cart(request: HttpRequest, product_id: int) -> HttpResponse:
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    cart = _get_or_create_cart(request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
        item.save()
    messages.success(request, f"Added {product.name} to cart.")
    return redirect("store:cart_detail")


@login_required
def update_cart_item(request: HttpRequest, item_id: int) -> HttpResponse:
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    quantity = int(request.POST.get("quantity", 1))
    if quantity <= 0:
        item.delete()
    else:
        item.quantity = quantity
        item.save()
    return redirect("store:cart_detail")


@login_required
def remove_cart_item(request: HttpRequest, item_id: int) -> HttpResponse:
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    item.delete()
    messages.info(request, "Item removed from cart.")
    return redirect("store:cart_detail")


@login_required
def checkout(request: HttpRequest) -> HttpResponse:
    cart = _get_or_create_cart(request.user)
    if not cart.items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("store:product_list")

    total_amount = cart.total_amount
    amount_paise = int(total_amount * Decimal("100"))

    def create_order_from_cart(order_status: str, razorpay_order_id: str = "") -> Order:
        order = Order.objects.create(
            user=request.user,
            total_amount=total_amount,
            status=order_status,
            razorpay_order_id=razorpay_order_id,
        )
        for item in cart.items.select_related("product"):
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
            )
        cart.items.all().delete()
        return order

    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        order = create_order_from_cart("pending")
        messages.info(
            request,
            "Razorpay is not configured. Complete payment using UPI QR.",
        )
        return redirect("store:upi_payment", pk=order.pk)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    try:
        razorpay_order = client.order.create(
            {"amount": amount_paise, "currency": "INR", "payment_capture": "1"}
        )
    except razorpay.errors.BadRequestError:
        order = create_order_from_cart("pending")
        messages.info(
            request,
            "Razorpay authentication failed. Complete payment using UPI QR.",
        )
        return redirect("store:upi_payment", pk=order.pk)

    order = create_order_from_cart("pending", razorpay_order["id"])

    context = {
        "order": order,
        "razorpay_order_id": razorpay_order["id"],
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        "amount": amount_paise,
        "currency": "INR",
    }
    return render(request, "store/checkout.html", context)


@login_required
def upi_payment(request: HttpRequest, pk: int) -> HttpResponse:
    order = get_object_or_404(Order, pk=pk, user=request.user)
    upi_id = getattr(settings, "UPI_ID", "tharunreddy153-1@okaxis")
    upi_name = getattr(settings, "UPI_NAME", "Tharun Reddy")
    qr_url = getattr(settings, "UPI_QR_IMAGE_URL", "") or _build_upi_qr_url(order)
    return render(
        request,
        "store/upi_payment.html",
        {"order": order, "upi_id": upi_id, "upi_name": upi_name, "qr_url": qr_url},
    )


@login_required
def upi_payment_done(request: HttpRequest, pk: int) -> HttpResponse:
    if request.method != "POST":
        return redirect("store:upi_payment", pk=pk)

    order = get_object_or_404(Order, pk=pk, user=request.user)
    if order.status != "pending":
        messages.info(request, "Payment is already submitted for this order.")
        return redirect("store:order_detail", pk=order.pk)

    transaction_id = request.POST.get("transaction_id", "").strip()
    order.status = "paid"
    if transaction_id:
        order.razorpay_payment_id = transaction_id
        order.save(update_fields=["status", "razorpay_payment_id", "updated_at"])
    else:
        order.save(update_fields=["status", "updated_at"])

    messages.success(
        request, "Payment submitted. Order confirmed and waiting for admin approval."
    )
    return redirect("store:order_detail", pk=order.pk)


@csrf_exempt
def payment_verify(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    data = request.POST
    order_id = data.get("razorpay_order_id")
    payment_id = data.get("razorpay_payment_id")
    signature = data.get("razorpay_signature")

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    try:
        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            }
        )
    except razorpay.errors.SignatureVerificationError:
        Order.objects.filter(razorpay_order_id=order_id).update(status="cancelled")
        return JsonResponse({"status": "failure"})

    order = Order.objects.filter(razorpay_order_id=order_id).first()
    if order:
        order.status = "paid"
        order.razorpay_payment_id = payment_id
        order.razorpay_signature = signature
        order.save()
    return JsonResponse({"status": "success"})


@login_required
def order_list(request: HttpRequest) -> HttpResponse:
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "store/orders.html", {"orders": orders})


@login_required
def order_detail(request: HttpRequest, pk: int) -> HttpResponse:
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, "store/order_detail.html", {"order": order})


def register_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful.")
            return redirect("store:home")
    else:
        form = RegisterForm()
    return render(request, "store/register.html", {"form": form})


def login_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Logged in successfully.")
            return redirect("store:home")
        messages.error(request, "Invalid credentials.")
    return render(request, "store/login.html")


def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("store:home")


def staff_check(user):
    return user.is_staff or user.is_superuser


@user_passes_test(staff_check)
def admin_dashboard(request: HttpRequest) -> HttpResponse:
    total_orders = Order.objects.count()
    total_revenue = (
        Order.objects.filter(status__in=["paid", "processing", "shipped", "delivered"])
        .aggregate(total=Sum("total_amount"))
        .get("total")
        or 0
    )
    total_products = Product.objects.count()

    status_breakdown = (
        Order.objects.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )

    top_products = (
        OrderItem.objects.values("product__name")
        .annotate(total_qty=Sum("quantity"), revenue=Sum(F("price") * F("quantity")))
        .order_by("-total_qty")[:5]
    )
    pending_approvals = Order.objects.filter(status="paid").select_related("user").order_by(
        "-created_at"
    )[:20]

    context = {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "total_products": total_products,
        "status_breakdown": status_breakdown,
        "top_products": top_products,
        "pending_approvals": pending_approvals,
    }
    return render(request, "store/admin_dashboard.html", context)


@user_passes_test(staff_check)
def approve_order(request: HttpRequest, pk: int) -> HttpResponse:
    if request.method != "POST":
        return redirect("store:admin_dashboard")

    order = get_object_or_404(Order, pk=pk)
    if order.status == "paid":
        order.status = "processing"
        order.save(update_fields=["status", "updated_at"])
        messages.success(request, f"Order #{order.pk} approved.")
    else:
        messages.info(request, f"Order #{order.pk} is not waiting for approval.")
    return redirect("store:admin_dashboard")
