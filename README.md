# Django-E-commerce

A simple and complete e-commerce website built with **Django**.  
You can add products, manage users, handle carts, and accept payments with **Stripe**.  
It’s made for developers who want a working online store they can extend or customize.

---

## Overview

Django-E-commerce is a straightforward online store built using Django.  
It provides all the core features needed for an e-commerce platform:  
- Product management  
- User authentication  
- Shopping cart  
- Checkout and payment with Stripe  
- Admin dashboard for managing users, products, and orders  

---

## Features

- User registration, login, and password reset  
- Product creation, editing, and deletion  
- Add products to cart and proceed to checkout  
- Stripe integration for secure online payments  
- Django admin panel for management  

---

## Tech Stack

- **Backend:** Django 4.2+  
- **Language:** Python 3.8+  
- **Frontend:** HTML, CSS, JavaScript (Django templates)  
- **Payments:** Stripe  
- **Additional Libraries:** Django Taggit, Django Countries, Pillow, Select2  


---

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/Lachi1921/Django-E-comnmerce.git
cd Django-E-comnmerce
````

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate the virtual environment:

* **Windows:**

  ```bash
  venv\Scripts\activate
  ```
* **macOS/Linux:**

  ```bash
  source venv/bin/activate
  ```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file or set variables manually:

```
STRIPE_PUBLIC_KEY=your_public_key
STRIPE_SECRET_KEY=your_secret_key
```

These are required for Stripe payments to work.

### 5. Apply database migrations

```bash
python manage.py migrate
```

### 6. Create a superuser

```bash
python manage.py createsuperuser
```

### 7. Run the development server

```bash
python manage.py runserver
```

Then open your browser and visit:

```
http://127.0.0.1:8000
```

The admin panel is available at:

```
http://127.0.0.1:8000/admin
```

---

## Development Notes

* Django admin is used for product and order management.
* To extend functionality, add new views, models, or templates.
