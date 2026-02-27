from django.conf import settings
from django.db import models


class Category(models.Model):
    """
    Subcategory for products, e.g. 'Common fruits', 'Leafy vegetables'.
    """

    KIND_CHOICES = (
        ("fruit", "Fruit"),
        ("vegetable", "Vegetable"),
    )

    name = models.CharField(max_length=100)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)

    class Meta:
        unique_together = ("name", "kind")
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["kind", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_kind_display()})"


class Product(models.Model):
    CATEGORY_CHOICES = (
        ("fruit", "Fruit"),
        ("vegetable", "Vegetable"),
    )

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    # High-level category: Fruit / Vegetable
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    # Detailed subcategory, e.g. "Tropical fruits", "Leafy vegetables"
    subcategory = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    stock_qty = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/")
    is_featured = models.BooleanField(default=False)
    # Overall availability flag, used for storefront visibility
    is_available = models.BooleanField(default=True)
    # Legacy active flag kept for backwards compatibility
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="carts"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Cart #{self.pk} for {self.user}"

    @property
    def total_amount(self):
        return sum(item.subtotal for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("cart", "product")

    @property
    def subtotal(self):
        return self.product.price * self.quantity


class Order(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    razorpay_order_id = models.CharField(max_length=200, blank=True)
    razorpay_payment_id = models.CharField(max_length=200, blank=True)
    razorpay_signature = models.CharField(max_length=200, blank=True)

    def __str__(self) -> str:
        return f"Order #{self.pk} by {self.user}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=8, decimal_places=2)

    @property
    def subtotal(self):
        return self.price * self.quantity

