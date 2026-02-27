# Organic Basket – Fruits & Vegetables E‑commerce (Django)

Modern, responsive fruits & vegetables e‑commerce website built with Django, Bootstrap and Razorpay.

## 1. Features

- **Home page**: hero banner with fresh produce background, category cards, featured products.
- **Products**: fruits and vegetables listing, category filters, product detail page.
- **Cart**: add/update/remove items, cart total.
- **Checkout**: Razorpay payment integration (India), order creation and verification.
- **Orders**: order history, order detail with items and status.
- **Auth**: register/login/logout using Django auth, JWT endpoints via SimpleJWT for API access.
- **Admin**:
  - Manage products with image upload.
  - View orders in Django admin.
  - Custom analytics dashboard (total orders, revenue, products, top products, status breakdown).
- **UI/UX**:
  - Natural green eco‑friendly theme.
  - Glassmorphism navbar.
  - Animated hero section and product cards.
  - Dark & light mode toggle (saved in `localStorage`).
  - Fully responsive (Bootstrap 5).

## 2. Project structure (key files)

- `manage.py`
- `organic_shop/`
  - `settings.py` – DB, apps, static/media, REST/JWT, Razorpay keys.
  - `urls.py`
- `store/`
  - `models.py` – `Product`, `Cart`, `CartItem`, `Order`, `OrderItem`.
  - `views.py` – home, products, product detail, cart, checkout, payment verify, orders, analytics, auth views.
  - `urls.py`
  - `forms.py` – registration form.
  - `admin.py` – admin configuration.
  - `context_processors.py` – cart item count in navbar.
- `templates/`
  - `base.html` – layout, navbar, dark/light toggle.
  - `store/home.html`, `products.html`, `product_detail.html`, `cart.html`,
    `checkout.html`, `orders.html`, `order_detail.html`, `login.html`, `register.html`,
    `admin_dashboard.html`.
- `static/store/css/styles.css` – theme, animations, product cards, hero.
- `static/store/js/theme.js` – dark/light mode.

## 3. VS Code / Cursor setup (Windows)

1. **Open folder**
   - Open VS Code or Cursor.
   - `File -> Open Folder...` and select `c:\Users\THARUN REDDY\Desktop\vegetables site`.

2. **Create virtual environment**

   ```bash
   cd "c:\Users\THARUN REDDY\Desktop\vegetables site"
   python -m venv .venv
   ```

3. **Activate venv (PowerShell)**

   ```bash
   .venv\Scripts\Activate.ps1
   ```

4. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

5. **Select interpreter in VS Code**
   - Press `Ctrl+Shift+P` → “Python: Select Interpreter”.
   - Choose `.venv` from this project.

## 4. Django setup

1. **Apply migrations**

   ```bash
   python manage.py migrate
   ```

2. **Create superuser**

   ```bash
   python manage.py createsuperuser
   ```

3. **Run development server**

   ```bash
   python manage.py runserver
   ```

4. **Access the app**

   - Storefront: `http://127.0.0.1:8000/`
   - Admin: `http://127.0.0.1:8000/admin/`

## 5. Razorpay configuration

1. Create a Razorpay account and get **Test Key ID** and **Test Key Secret**.
2. Set environment variables (PowerShell example):

   ```powershell
   $env:RAZORPAY_KEY_ID = "your_test_key_id"
   $env:RAZORPAY_KEY_SECRET = "your_test_key_secret"
   ```

3. Restart the dev server so Django picks them up.

The checkout page uses Razorpay Checkout.js, creates a Razorpay order from Django, and verifies the payment via `/payment/verify/`.

## 6. JWT authentication (API)

This project uses **Django REST Framework + SimpleJWT**.

- Obtain token pair:

  ```http
  POST /api/token/
  {
    "username": "youruser",
    "password": "yourpassword"
  }
  ```

  Response includes `access` and `refresh` tokens.

- Refresh token:

  ```http
  POST /api/token/refresh/
  {
    "refresh": "<your_refresh_token>"
  }
  ```

You can protect DRF API views with JWT using `JWTAuthentication` (already set in `REST_FRAMEWORK` in `settings.py`).

## 7. Deployment notes (SQLite / static / media)

For production:

- Set `DEBUG = False` and configure `ALLOWED_HOSTS` in `organic_shop/settings.py`.
- Run:

  ```bash
  python manage.py collectstatic
  ```

- Ensure your server (e.g., Nginx) serves:
  - `/static/` from the `staticfiles/` directory.
  - `/media/` from the `media/` directory.
- Use environment variables for:
  - `SECRET_KEY` (do **not** use the default in production).
  - `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`.

This structure is compatible with common deployment platforms (Gunicorn + Nginx, or cloud PaaS) and is ready to be extended with a production database later.

