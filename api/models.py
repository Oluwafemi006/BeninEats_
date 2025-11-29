from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator

class User(AbstractUser):
    ROLE_CHOICES = [
        ('client', 'Client'),
        ('driver', 'Livreur'),
        ('manager', 'Gérant'),
        ('admin', 'Administrateur'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_available = models.BooleanField(default=True)  # For drivers
    
    def __str__(self):
        return f"{self.username} ({self.role})"


class Category(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50)  # Icon name for frontend
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class Restaurant(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='restaurants/')
    cover_image = models.ImageField(upload_to='restaurants/covers/', blank=True, null=True)
    address = models.TextField()
    phone = models.CharField(max_length=20, blank=True)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    rating_count = models.IntegerField(default=0)
    delivery_time = models.CharField(max_length=50, default='30-45 min')
    delivery_fee = models.IntegerField(default=500)
    minimum_order = models.IntegerField(default=1000)
    is_open = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    categories = models.ManyToManyField(Category, related_name='restaurants')
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name='managed_restaurants', limit_choices_to={'role': 'manager'})
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class Product(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.IntegerField(validators=[MinValueValidator(0)])
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.restaurant.name}"


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    
    class Meta:
        unique_together = ['cart', 'product']
    
    @property
    def subtotal(self):
        return self.product.price * self.quantity


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('accepted', 'Acceptée'),
        ('preparing', 'En préparation'),
        ('ready', 'Prête'),
        ('assigned', 'Assignée'),
        ('picked_up', 'Récupérée'),
        ('delivering', 'En livraison'),
        ('delivered', 'Livrée'),
        ('cancelled', 'Annulée'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='orders')
    driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='deliveries', limit_choices_to={'role': 'driver'})
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total = models.IntegerField(default=0)
    delivery_fee = models.IntegerField(default=500)
    delivery_address = models.TextField()
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=200)  # Store name at time of order
    product_price = models.IntegerField()  # Store price at time of order
    quantity = models.IntegerField(default=1)
    
    @property
    def subtotal(self):
        return self.product_price * self.quantity


class DriverSchedule(models.Model):
    DAY_CHOICES = [
        ('monday', 'Lundi'),
        ('tuesday', 'Mardi'),
        ('wednesday', 'Mercredi'),
        ('thursday', 'Jeudi'),
        ('friday', 'Vendredi'),
        ('saturday', 'Samedi'),
        ('sunday', 'Dimanche'),
    ]
    
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='schedules',
                               limit_choices_to={'role': 'driver'})
    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    is_enabled = models.BooleanField(default=True)
    start_time = models.TimeField(default='08:00')
    end_time = models.TimeField(default='18:00')
    
    class Meta:
        unique_together = ['driver', 'day']
        ordering = ['day']
    
    def __str__(self):
        return f"{self.driver.username} - {self.day}"


class Banner(models.Model):
    restaurant = models.ForeignKey(
        Restaurant, on_delete=models.CASCADE, 
        related_name='banners', null=True, blank=True
    )
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to='banners/', blank=True, null=True)
    link_type = models.CharField(max_length=50, blank=True)
    link_id = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.title


class AppSettings(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.CharField(max_length=255, blank=True)
    
    class Meta:
        verbose_name_plural = 'App Settings'
    
    def __str__(self):
        return self.key


class TeamMember(models.Model):
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('inactive', 'Inactif'),
    ]
    
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='team_members')
    name = models.CharField(max_length=200)
    role = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.role}"
