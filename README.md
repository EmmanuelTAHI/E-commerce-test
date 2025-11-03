# E-Commerce Django Application

A complete, modern e-commerce web application built with Django, featuring DaisyUI and TailwindCSS for beautiful, responsive design.

## Features

- **Product Management**: Full product catalog with categories, images, and stock management
- **Shopping Cart**: Add, update, and remove items from cart
- **User Authentication**: Registration and login system
- **Order Management**: Complete order processing with status tracking
- **Customer Reviews**: Product rating and review system
- **Address Management**: Multiple shipping addresses per customer
- **Responsive Design**: Beautiful UI using DaisyUI and TailwindCSS
- **Email Configuration**: SMTP support for order confirmations
- **Admin Panel**: Full-featured Django admin interface

## Tech Stack

- **Backend**: Django 5.2.7
- **Database**: SQLite (easily switchable to PostgreSQL)
- **Frontend**: TailwindCSS + DaisyUI
- **Icons**: Font Awesome
- **Image Processing**: Pillow

## Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd e_commerce
   ```

2. **Activate your virtual environment** (if not already activated)
   ```bash
   # On Windows
   venv\Scripts\activate

   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations** (if not already done)
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser** (to access admin panel)
   ```bash
   python manage.py createsuperuser
   ```

6. **Collect static files**
   ```bash
   python manage.py collectstatic
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Home page: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## Email Configuration

To enable email sending (for order confirmations, etc.), update the following in `mon_projet_ecommerce/settings.py`:

```python
EMAIL_HOST_USER = 'your-email@gmail.com'  # Your email
EMAIL_HOST_PASSWORD = 'your-app-password'  # Gmail App Password
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'  # Your email
```

**For Gmail users**, you need to:
1. Enable 2-Step Verification
2. Generate an App Password: https://myaccount.google.com/apppasswords

## Adding Products

You can add products in two ways:

1. **Using the Admin Panel** (Recommended)
   - Go to http://127.0.0.1:8000/admin/
   - Login with your superuser credentials
   - Click on "Categories" to add product categories
   - Click on "Products" to add products

2. **Using Django Shell or Management Command**
   ```bash
   python manage.py shell
   ```

## Project Structure

```
e_commerce/
├── mon_app_ecommerce/       # Main app
│   ├── models.py           # Database models
│   ├── views.py            # View functions
│   ├── urls.py             # URL routing
│   ├── admin.py            # Admin configuration
│   └── templates/          # HTML templates
│       └── mon_app_ecommerce/
│           ├── base.html
│           ├── home.html
│           ├── product_list.html
│           ├── product_detail.html
│           ├── cart.html
│           ├── checkout.html
│           ├── order_history.html
│           ├── order_detail.html
│           ├── account.html
│           ├── login.html
│           └── register.html
├── mon_projet_ecommerce/   # Project settings
│   ├── settings.py         # Django settings
│   └── urls.py             # Root URL configuration
├── static/                  # Static files (CSS, JS, images)
├── media/                   # User uploaded files (product images, etc.)
├── db.sqlite3              # SQLite database
└── manage.py               # Django management script
```

## Usage

### For Customers:
1. Register or Login
2. Browse products
3. Add products to cart
4. Proceed to checkout
5. View order history in your account

### For Administrators:
1. Login to admin panel at `/admin/`
2. Create categories and products
3. Manage orders and customers
4. Monitor inventory

## Key Pages

- **Home**: Product showcase and featured items
- **Products**: Browse all products with category filters
- **Product Detail**: View product details and reviews
- **Cart**: Manage shopping cart items
- **Checkout**: Place orders with shipping address
- **Order History**: View past orders
- **Account**: Manage profile and addresses
- **Admin Panel**: Full administrative interface

## Customization

### Changing the Theme
Edit `base.html` and change the `data-theme` attribute:
```html
<html lang="en" data-theme="light">
```
DaisyUI themes: light, dark, corporate, retro, cyberpunk, valentine, halloween, forest, aqua, luxery, dracula, cmyk, autumn, business, acid, lemonade, night, coffee, winter

### Styling
- All HTML templates use TailwindCSS classes
- DaisyUI components are used for consistent design
- Custom CSS can be added in the `<style>` section of `base.html`

## Database

By default, the project uses SQLite. To switch to PostgreSQL:

1. Install PostgreSQL and psycopg2:
   ```bash
   pip install psycopg2-binary
   ```

2. Update `settings.py`:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'your_db_name',
           'USER': 'your_db_user',
           'PASSWORD': 'your_db_password',
           'HOST': 'localhost',
           'PORT': '5432',
       }
   }
   ```

## Security Notes

- Change `SECRET_KEY` in `settings.py` before deploying
- Set `DEBUG = False` in production
- Add your domain to `ALLOWED_HOSTS`
- Use environment variables for sensitive data
- Enable HTTPS in production

## License

This project is for educational and commercial use.

## Support

For issues or questions, please contact the development team.
