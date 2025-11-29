"""
Seed script to populate initial data
Run with: python manage.py shell < seed_data.py
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.models import Category, Restaurant, Product, Banner, AppSettings, User

# Create Categories
categories_data = [
    {'name': 'Tout', 'icon': 'grid', 'order': 0},
    {'name': 'Plats Locaux', 'icon': 'utensils', 'order': 1},
    {'name': 'Grillades', 'icon': 'flame', 'order': 2},
    {'name': 'Poissons', 'icon': 'fish', 'order': 3},
    {'name': 'Boissons', 'icon': 'cup-soda', 'order': 4},
    {'name': 'Desserts', 'icon': 'cake', 'order': 5},
    {'name': 'Fast Food', 'icon': 'pizza', 'order': 6},
]

categories = {}
for cat_data in categories_data:
    cat, created = Category.objects.get_or_create(
        name=cat_data['name'],
        defaults=cat_data
    )
    categories[cat.name] = cat
    print(f"Category: {cat.name} {'created' if created else 'exists'}")

# Create Restaurants
restaurants_data = [
    {
        'name': 'Chez Maman Aïcha',
        'description': 'Cuisine béninoise traditionnelle, plats faits maison avec amour',
        'address': 'Cotonou, Haie Vive, Rue 123',
        'phone': '+229 97 00 00 01',
        'rating': 4.8,
        'rating_count': 234,
        'delivery_time': '25-35 min',
        'delivery_fee': 500,
        'categories': ['Plats Locaux', 'Grillades'],
    },
    {
        'name': 'Le Roi du Poisson',
        'description': 'Spécialités de poissons frais, grillés ou braisés',
        'address': 'Cotonou, Akpakpa, Boulevard Principal',
        'phone': '+229 97 00 00 02',
        'rating': 4.5,
        'rating_count': 189,
        'delivery_time': '30-40 min',
        'delivery_fee': 600,
        'categories': ['Poissons', 'Grillades'],
    },
    {
        'name': 'Fast Délice',
        'description': 'Burgers, pizzas et snacks rapides',
        'address': 'Cotonou, Ganhi',
        'phone': '+229 97 00 00 03',
        'rating': 4.2,
        'rating_count': 156,
        'delivery_time': '20-30 min',
        'delivery_fee': 400,
        'categories': ['Fast Food', 'Boissons'],
    },
    {
        'name': 'Saveurs du Bénin',
        'description': 'Le meilleur de la gastronomie béninoise',
        'address': 'Porto-Novo, Centre Ville',
        'phone': '+229 97 00 00 04',
        'rating': 4.7,
        'rating_count': 312,
        'delivery_time': '35-45 min',
        'delivery_fee': 700,
        'categories': ['Plats Locaux', 'Desserts'],
    },
]

restaurants = []
for rest_data in restaurants_data:
    cat_names = rest_data.pop('categories')
    rest, created = Restaurant.objects.get_or_create(
        name=rest_data['name'],
        defaults=rest_data
    )
    for cat_name in cat_names:
        if cat_name in categories:
            rest.categories.add(categories[cat_name])
    restaurants.append(rest)
    print(f"Restaurant: {rest.name} {'created' if created else 'exists'}")

# Create Products
products_data = [
    # Chez Maman Aïcha
    {'restaurant': 0, 'category': 'Plats Locaux', 'name': 'Pâte Rouge avec Sauce Graine', 'price': 1500, 'is_popular': True},
    {'restaurant': 0, 'category': 'Plats Locaux', 'name': 'Riz au Gras', 'price': 1200, 'is_popular': True},
    {'restaurant': 0, 'category': 'Plats Locaux', 'name': 'Akassa avec Crabe', 'price': 2000},
    {'restaurant': 0, 'category': 'Grillades', 'name': 'Poulet Braisé', 'price': 3500, 'is_featured': True},
    {'restaurant': 0, 'category': 'Boissons', 'name': 'Jus de Bissap', 'price': 500},
    
    # Le Roi du Poisson
    {'restaurant': 1, 'category': 'Poissons', 'name': 'Tilapia Grillé', 'price': 4000, 'is_popular': True},
    {'restaurant': 1, 'category': 'Poissons', 'name': 'Capitaine Braisé', 'price': 5500, 'is_featured': True},
    {'restaurant': 1, 'category': 'Poissons', 'name': 'Crevettes Sautées', 'price': 6000},
    {'restaurant': 1, 'category': 'Plats Locaux', 'name': 'Ablo avec Sauce Poisson', 'price': 1800},
    
    # Fast Délice
    {'restaurant': 2, 'category': 'Fast Food', 'name': 'Burger Classic', 'price': 2500, 'is_popular': True},
    {'restaurant': 2, 'category': 'Fast Food', 'name': 'Pizza Margherita', 'price': 4500},
    {'restaurant': 2, 'category': 'Fast Food', 'name': 'Frites Portion', 'price': 800},
    {'restaurant': 2, 'category': 'Boissons', 'name': 'Coca-Cola 50cl', 'price': 500},
    {'restaurant': 2, 'category': 'Boissons', 'name': 'Fanta Orange 50cl', 'price': 500},
    
    # Saveurs du Bénin
    {'restaurant': 3, 'category': 'Plats Locaux', 'name': 'Wagasi Frit', 'price': 1000, 'is_popular': True},
    {'restaurant': 3, 'category': 'Plats Locaux', 'name': 'Amiwo', 'price': 1500},
    {'restaurant': 3, 'category': 'Desserts', 'name': 'Beignets Sucrés', 'price': 500, 'is_popular': True},
    {'restaurant': 3, 'category': 'Desserts', 'name': 'Yaourt Maison', 'price': 800},
]

for prod_data in products_data:
    rest_idx = prod_data.pop('restaurant')
    cat_name = prod_data.pop('category')
    
    prod, created = Product.objects.get_or_create(
        name=prod_data['name'],
        restaurant=restaurants[rest_idx],
        defaults={
            **prod_data,
            'category': categories.get(cat_name),
            'description': f"Délicieux {prod_data['name'].lower()} préparé avec soin"
        }
    )
    print(f"Product: {prod.name} {'created' if created else 'exists'}")

# Create Banners
banners_data = [
    {'title': 'Livraison Gratuite', 'subtitle': 'Sur votre première commande', 'order': 0},
    {'title': '-20% ce weekend', 'subtitle': 'Sur les grillades', 'order': 1},
    {'title': 'Nouveau Restaurant', 'subtitle': 'Découvrez Saveurs du Bénin', 'order': 2},
]

for banner_data in banners_data:
    banner, created = Banner.objects.get_or_create(
        title=banner_data['title'],
        defaults=banner_data
    )
    print(f"Banner: {banner.title} {'created' if created else 'exists'}")

# Create App Settings
settings_data = [
    {'key': 'app_name', 'value': 'BeninEats', 'description': 'Application name'},
    {'key': 'currency', 'value': 'FCFA', 'description': 'Currency symbol'},
    {'key': 'min_order_amount', 'value': '1000', 'description': 'Minimum order amount'},
    {'key': 'support_phone', 'value': '+229 97 00 00 00', 'description': 'Support phone number'},
    {'key': 'support_email', 'value': 'support@benineats.com', 'description': 'Support email'},
]

for setting_data in settings_data:
    setting, created = AppSettings.objects.get_or_create(
        key=setting_data['key'],
        defaults=setting_data
    )
    print(f"Setting: {setting.key} {'created' if created else 'exists'}")

# Create test users
test_users = [
    {'username': 'client1', 'email': 'client@test.com', 'role': 'client', 'password': 'test123'},
    {'username': 'driver1', 'email': 'driver@test.com', 'role': 'driver', 'password': 'test123'},
    {'username': 'manager1', 'email': 'manager@test.com', 'role': 'manager', 'password': 'test123'},
]

for user_data in test_users:
    password = user_data.pop('password')
    user, created = User.objects.get_or_create(
        username=user_data['username'],
        defaults=user_data
    )
    if created:
        user.set_password(password)
        user.save()
    print(f"User: {user.username} ({user.role}) {'created' if created else 'exists'}")

print("\n✅ Seed data completed!")
