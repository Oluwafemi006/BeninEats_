# BeninEats Backend

Django REST API for the BeninEats mobile app.

## Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Seed initial data
python seed_data.py

# Run server
python manage.py runserver 0.0.0.0:8000
```

## API Endpoints

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login
- `POST /api/auth/refresh/` - Refresh token
- `GET /api/auth/profile/` - Get profile
- `PATCH /api/auth/profile/` - Update profile

### Categories
- `GET /api/categories/` - List all categories

### Restaurants
- `GET /api/restaurants/` - List all restaurants
- `GET /api/restaurants/{id}/` - Restaurant details with products
- `GET /api/restaurants/featured/` - Featured restaurants
- `GET /api/restaurants/by_category/?category_id=X` - Filter by category

### Products
- `GET /api/products/` - List all products
- `GET /api/products/{id}/` - Product details
- `GET /api/products/popular/` - Popular products
- `GET /api/products/featured/` - Featured products
- `GET /api/products/by_restaurant/?restaurant_id=X` - Filter by restaurant

### Cart
- `GET /api/cart/` - Get user cart
- `POST /api/cart/items/` - Add item to cart
- `PUT /api/cart/items/` - Update item quantity
- `DELETE /api/cart/items/?product_id=X` - Remove item
- `DELETE /api/cart/items/` - Clear cart

### Orders
- `GET /api/orders/` - List user orders
- `GET /api/orders/{id}/` - Order details
- `POST /api/orders/create_from_cart/` - Create order from cart
- `POST /api/orders/{id}/update_status/` - Update order status
- `GET /api/orders/pending/` - Pending orders (manager)

### Driver
- `GET /api/driver/schedule/my_schedule/` - Get schedule
- `POST /api/driver/schedule/update_day/` - Update day schedule
- `POST /api/driver/schedule/toggle_availability/` - Toggle availability
- `GET /api/driver/missions/` - Get missions
- `GET /api/driver/dashboard/` - Dashboard stats

### Manager
- `GET /api/manager/dashboard/` - Dashboard stats

### Banners & Settings
- `GET /api/banners/` - List banners
- `GET /api/settings/` - App settings

## Test Users

| Role    | Email             | Password |
|---------|-------------------|----------|
| Admin   | admin@benineats.com | admin123 |
| Client  | client@test.com   | test123  |
| Driver  | driver@test.com   | test123  |
| Manager | manager@test.com  | test123  |

## Admin Panel

Access admin at: http://localhost:8000/admin/
