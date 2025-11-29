from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import (
    User, Category, Restaurant, Product, Cart, CartItem,
    Order, OrderItem, DriverSchedule, Banner, AppSettings, TeamMember
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'role', 'phone', 'address', 'avatar', 'is_available']
        read_only_fields = ['id']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True)
    restaurant_name = serializers.CharField(write_only=True, required=False)
    restaurant_address = serializers.CharField(write_only=True, required=False)
    restaurant_phone = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 
                  'first_name', 'last_name', 'role', 'phone', 'address',
                  'restaurant_name', 'restaurant_address', 'restaurant_phone']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match'})
        if data.get('role') == 'manager' and not data.get('restaurant_name'):
            raise serializers.ValidationError({'restaurant_name': 'Restaurant name is required for managers'})
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        restaurant_name = validated_data.pop('restaurant_name', None)
        restaurant_address = validated_data.pop('restaurant_address', '')
        restaurant_phone = validated_data.pop('restaurant_phone', '')
        
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
        # Create cart for user
        Cart.objects.create(user=user)
        
        # Create restaurant for managers
        if user.role == 'manager' and restaurant_name:
            Restaurant.objects.create(
                name=restaurant_name,
                address=restaurant_address or 'Cotonou, Bénin',
                phone=restaurant_phone or user.phone,
                manager=user,
                is_active=True,
                is_open=True,
            )
        
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])
        if not user:
            # Try with username
            try:
                user_obj = User.objects.get(email=data['email'])
                user = authenticate(username=user_obj.username, password=data['password'])
            except User.DoesNotExist:
                pass
        
        if not user:
            raise serializers.ValidationError('Invalid credentials')
        
        if not user.is_active:
            raise serializers.ValidationError('User account is disabled')
        
        data['user'] = user
        return data


class CategorySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    filter = serializers.SerializerMethodField()
    emoji = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'icon', 'image', 'image_url', 'is_active', 'order', 'filter', 'emoji']
    
    def get_image_url(self, obj):
        if obj.image and obj.image.name:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return f'https://picsum.photos/seed/cat{obj.id}/200/200'
    
    def get_filter(self, obj):
        return obj.name.lower()
    
    def get_emoji(self, obj):
        emoji_map = {
            'pizza': '🍕',
            'burger': '🍔',
            'burgers': '🍔',
            'sushi': '🍣',
            'poulet': '🍗',
            'chicken': '🍗',
            'africain': '🍲',
            'african': '🍲',
            'dessert': '🍰',
            'desserts': '🍰',
            'boissons': '🥤',
            'drinks': '🥤',
            'salades': '🥗',
            'salads': '🥗',
            'poisson': '🐟',
            'fish': '🐟',
            'pâtes': '🍝',
            'pasta': '🍝',
            'grillades': '🥩',
            'grill': '🥩',
        }
        return emoji_map.get(obj.name.lower(), '🍽️')


class ProductSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    restaurant = serializers.PrimaryKeyRelatedField(
        queryset=Restaurant.objects.all(), required=False
    )
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), required=False, allow_null=True
    )
    image = serializers.ImageField(required=False)
    
    class Meta:
        model = Product
        fields = ['id', 'restaurant', 'restaurant_name', 'category', 'category_name',
                  'name', 'description', 'price', 'image', 'image_url', 
                  'is_available', 'is_popular', 'is_featured']
    
    def get_image_url(self, obj):
        if obj.image and obj.image.name:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return f'https://picsum.photos/seed/food{obj.id}/300/300'


class RestaurantListSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    cover_image_url = serializers.SerializerMethodField()
    categories = CategorySerializer(many=True, read_only=True)
    category = serializers.SerializerMethodField()
    
    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'description', 'image', 'image_url', 
                  'cover_image', 'cover_image_url', 'address', 'rating', 
                  'rating_count', 'delivery_time', 'delivery_fee', 
                  'minimum_order', 'is_open', 'categories', 'category']
    
    def get_category(self, obj):
        first_cat = obj.categories.first()
        return first_cat.name.lower() if first_cat else None
    
    def get_image_url(self, obj):
        if obj.image and obj.image.name:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return f'https://picsum.photos/seed/resto{obj.id}/400/300'
    
    def get_cover_image_url(self, obj):
        if obj.cover_image and obj.cover_image.name:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
        return f'https://picsum.photos/seed/cover{obj.id}/800/400'


class RestaurantDetailSerializer(RestaurantListSerializer):
    products = ProductSerializer(many=True, read_only=True)
    
    class Meta(RestaurantListSerializer.Meta):
        fields = RestaurantListSerializer.Meta.fields + ['products', 'phone']


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    subtotal = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'subtotal']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ['id', 'items', 'total', 'item_count', 'updated_at']
    
    def get_total(self, obj):
        return sum(item.subtotal for item in obj.items.all())
    
    def get_item_count(self, obj):
        return sum(item.quantity for item in obj.items.all())


class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'product_price', 'quantity', 'subtotal']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    restaurant_image = serializers.SerializerMethodField()
    driver_name = serializers.CharField(source='driver.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'restaurant', 'restaurant_name', 'restaurant_image',
                  'driver', 'driver_name', 'status', 'status_display', 
                  'total', 'delivery_fee', 'delivery_address', 
                  'customer_name', 'customer_phone', 'notes', 
                  'items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'total', 'created_at', 'updated_at']
    
    def get_restaurant_image(self, obj):
        if obj.restaurant.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.restaurant.image.url)
        return None


class CreateOrderSerializer(serializers.Serializer):
    delivery_address = serializers.CharField()
    customer_name = serializers.CharField()
    customer_phone = serializers.CharField()
    notes = serializers.CharField(required=False, allow_blank=True)


class DriverScheduleSerializer(serializers.ModelSerializer):
    day_display = serializers.CharField(source='get_day_display', read_only=True)
    
    class Meta:
        model = DriverSchedule
        fields = ['id', 'day', 'day_display', 'is_enabled', 'start_time', 'end_time']


class BannerSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    restaurant = serializers.PrimaryKeyRelatedField(
        queryset=Restaurant.objects.all(), required=False
    )
    image = serializers.ImageField(required=False)
    
    class Meta:
        model = Banner
        fields = ['id', 'restaurant', 'title', 'subtitle', 'image', 'image_url', 
                  'link_type', 'link_id', 'is_active', 'order']
        read_only_fields = ['restaurant']
    
    def get_image_url(self, obj):
        if obj.image and obj.image.name:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return f'https://picsum.photos/seed/banner{obj.id}/800/300'


class AppSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppSettings
        fields = ['key', 'value', 'description']


class DashboardStatsSerializer(serializers.Serializer):
    total_orders = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    today_revenue = serializers.IntegerField()
    total_products = serializers.IntegerField()


class DriverStatsSerializer(serializers.Serializer):
    total_deliveries = serializers.IntegerField()
    today_deliveries = serializers.IntegerField()
    pending_missions = serializers.IntegerField()
    is_available = serializers.BooleanField()


class TeamMemberSerializer(serializers.ModelSerializer):
    restaurant = serializers.PrimaryKeyRelatedField(
        queryset=Restaurant.objects.all(), required=False
    )
    
    class Meta:
        model = TeamMember
        fields = ['id', 'restaurant', 'name', 'role', 'phone', 'status', 'created_at']
        read_only_fields = ['id', 'restaurant', 'created_at']
