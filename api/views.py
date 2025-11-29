from rest_framework import viewsets, status, generics, serializers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from .models import (
    User, Category, Restaurant, Product, Cart, CartItem,
    Order, OrderItem, DriverSchedule, Banner, AppSettings, TeamMember
)
from .serializers import (
    UserSerializer, UserRegistrationSerializer, LoginSerializer,
    CategorySerializer, RestaurantListSerializer, RestaurantDetailSerializer,
    ProductSerializer, CartSerializer, CartItemSerializer,
    OrderSerializer, CreateOrderSerializer, DriverScheduleSerializer,
    BannerSerializer, AppSettingsSerializer, DashboardStatsSerializer,
    DriverStatsSerializer, TeamMemberSerializer
)


# ==================== AUTH ====================

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass
        return Response({'detail': 'Logged out successfully'}, status=status.HTTP_200_OK)


# ==================== CATEGORIES ====================

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]


# ==================== RESTAURANTS ====================

class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.filter(is_active=True)
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RestaurantDetailSerializer
        return RestaurantListSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [IsAdminUser()]
        if self.action in ['update', 'partial_update', 'toggle_open', 'upload_image']:
            return [IsAuthenticated()]
        return [AllowAny()]
    
    def update(self, request, *args, **kwargs):
        restaurant = self.get_object()
        user = request.user
        if user.role != 'admin' and restaurant.manager != user:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        restaurant = self.get_object()
        user = request.user
        if user.role != 'admin' and restaurant.manager != user:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        category_id = request.query_params.get('category_id')
        if category_id:
            restaurants = self.queryset.filter(categories__id=category_id)
            serializer = self.get_serializer(restaurants, many=True)
            return Response(serializer.data)
        return Response([])
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        restaurants = self.queryset.filter(rating__gte=4.0)[:10]
        serializer = self.get_serializer(restaurants, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_open(self, request, pk=None):
        restaurant = self.get_object()
        user = request.user
        if user.role != 'admin' and restaurant.manager != user:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        restaurant.is_open = not restaurant.is_open
        restaurant.save()
        return Response({'is_open': restaurant.is_open})
    
    @action(detail=True, methods=['post'])
    def upload_image(self, request, pk=None):
        restaurant = self.get_object()
        user = request.user
        if user.role != 'admin' and restaurant.manager != user:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        if 'image' in request.FILES:
            restaurant.image = request.FILES['image']
            restaurant.save()
            return Response(RestaurantListSerializer(restaurant, context={'request': request}).data)
        return Response({'error': 'No image provided'}, status=400)


# ==================== PRODUCTS ====================

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_available=True)
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'upload_image']:
            return [IsAuthenticated()]
        return [AllowAny()]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.role == 'manager':
            restaurant = Restaurant.objects.filter(manager=user).first()
            if restaurant:
                return Product.objects.filter(restaurant=restaurant)
        return Product.objects.filter(is_available=True)
    
    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'manager':
            restaurant = Restaurant.objects.filter(manager=user).first()
            if restaurant:
                serializer.save(restaurant=restaurant)
            else:
                raise serializers.ValidationError("No restaurant found")
        else:
            serializer.save()
    
    @action(detail=False, methods=['get'])
    def by_restaurant(self, request):
        restaurant_id = request.query_params.get('restaurant_id')
        if restaurant_id:
            products = self.queryset.filter(restaurant_id=restaurant_id)
            serializer = self.get_serializer(products, many=True)
            return Response(serializer.data)
        return Response([])
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        products = self.queryset.filter(is_popular=True)[:20]
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        products = self.queryset.filter(is_featured=True)[:10]
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def upload_image(self, request, pk=None):
        product = self.get_object()
        if 'image' in request.FILES:
            product.image = request.FILES['image']
            product.save()
            return Response(ProductSerializer(product, context={'request': request}).data)
        return Response({'error': 'No image provided'}, status=400)


# ==================== CART ====================

class CartView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart


class CartItemView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Add item to cart"""
        cart, _ = Cart.objects.get_or_create(user=request.user)
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=404)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        return Response(CartSerializer(cart, context={'request': request}).data)
    
    def put(self, request):
        """Update item quantity"""
        cart = Cart.objects.get(user=request.user)
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity')
        
        try:
            cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
            if quantity <= 0:
                cart_item.delete()
            else:
                cart_item.quantity = quantity
                cart_item.save()
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found in cart'}, status=404)
        
        return Response(CartSerializer(cart, context={'request': request}).data)
    
    def delete(self, request):
        """Remove item or clear cart"""
        cart = Cart.objects.get(user=request.user)
        product_id = request.query_params.get('product_id')
        
        if product_id:
            CartItem.objects.filter(cart=cart, product_id=product_id).delete()
        else:
            cart.items.all().delete()
        
        return Response(CartSerializer(cart, context={'request': request}).data)


# ==================== ORDERS ====================

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Order.objects.all()
        elif user.role == 'manager':
            return Order.objects.filter(restaurant__manager=user)
        elif user.role == 'driver':
            return Order.objects.filter(driver=user)
        return Order.objects.filter(user=user)
    
    @action(detail=False, methods=['post'])
    def create_from_cart(self, request):
        """Create order from cart"""
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        cart = Cart.objects.get(user=request.user)
        if not cart.items.exists():
            return Response({'error': 'Cart is empty'}, status=400)
        
        # Get restaurant from first item
        first_item = cart.items.first()
        restaurant = first_item.product.restaurant
        
        # Calculate total
        total = sum(item.subtotal for item in cart.items.all())
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            restaurant=restaurant,
            total=total,
            delivery_fee=restaurant.delivery_fee,
            delivery_address=serializer.validated_data['delivery_address'],
            customer_name=serializer.validated_data['customer_name'],
            customer_phone=serializer.validated_data['customer_phone'],
            notes=serializer.validated_data.get('notes', '')
        )
        
        # Create order items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                product_name=cart_item.product.name,
                product_price=cart_item.product.price,
                quantity=cart_item.quantity
            )
        
        # Clear cart
        cart.items.all().delete()
        
        return Response(OrderSerializer(order, context={'request': request}).data, 
                       status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update order status"""
        order = self.get_object()
        new_status = request.data.get('status')
        driver_id = request.data.get('driver_id')
        
        if new_status:
            order.status = new_status
        if driver_id:
            order.driver_id = driver_id
            if not new_status:
                order.status = 'assigned'
        
        order.save()
        return Response(OrderSerializer(order, context={'request': request}).data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending orders for manager"""
        orders = self.get_queryset().filter(status__in=['pending', 'accepted', 'preparing', 'ready'])
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)


# ==================== DRIVER ====================

class DriverScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = DriverScheduleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return DriverSchedule.objects.filter(driver=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(driver=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_schedule(self, request):
        schedules = self.get_queryset()
        
        # If no schedule exists, create default
        if not schedules.exists():
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            for day in days:
                DriverSchedule.objects.create(
                    driver=request.user,
                    day=day,
                    is_enabled=day not in ['saturday', 'sunday']
                )
            schedules = self.get_queryset()
        
        serializer = self.get_serializer(schedules, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def toggle_availability(self, request):
        user = request.user
        user.is_available = not user.is_available
        user.save()
        return Response({'is_available': user.is_available})
    
    @action(detail=False, methods=['post'])
    def update_day(self, request):
        day = request.data.get('day')
        updates = {k: v for k, v in request.data.items() if k != 'day'}
        
        schedule, _ = DriverSchedule.objects.get_or_create(
            driver=request.user, day=day
        )
        
        for key, value in updates.items():
            setattr(schedule, key, value)
        schedule.save()
        
        return Response(DriverScheduleSerializer(schedule).data)


class DriverMissionsView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # Get assigned orders or ready orders without driver
        return Order.objects.filter(
            driver=user
        ) | Order.objects.filter(
            driver__isnull=True,
            status='ready'
        )


# ==================== BANNERS & SETTINGS ====================

class BannerViewSet(viewsets.ModelViewSet):
    queryset = Banner.objects.filter(is_active=True)
    serializer_class = BannerSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return [AllowAny()]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.role == 'manager':
            restaurant = Restaurant.objects.filter(manager=user).first()
            if restaurant:
                return Banner.objects.filter(restaurant=restaurant)
        return Banner.objects.filter(is_active=True)
    
    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'manager':
            restaurant = Restaurant.objects.filter(manager=user).first()
            if restaurant:
                serializer.save(restaurant=restaurant)
            else:
                raise serializers.ValidationError("No restaurant found")
        else:
            serializer.save()


@api_view(['GET'])
@permission_classes([AllowAny])
def app_settings(request):
    settings = AppSettings.objects.all()
    data = {s.key: s.value for s in settings}
    return Response(data)


# ==================== DASHBOARD STATS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def manager_restaurant(request):
    user = request.user
    if user.role not in ['manager', 'admin']:
        return Response({'error': 'Unauthorized'}, status=403)
    
    restaurant = Restaurant.objects.filter(manager=user).first()
    if not restaurant:
        return Response({'error': 'No restaurant found'}, status=404)
    
    return Response(RestaurantDetailSerializer(restaurant, context={'request': request}).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def manager_dashboard(request):
    user = request.user
    if user.role not in ['manager', 'admin']:
        return Response({'error': 'Unauthorized'}, status=403)
    
    if user.role == 'manager':
        orders = Order.objects.filter(restaurant__manager=user)
        products = Product.objects.filter(restaurant__manager=user)
    else:
        orders = Order.objects.all()
        products = Product.objects.all()
    
    today = timezone.now().date()
    today_orders = orders.filter(created_at__date=today)
    
    stats = {
        'total_orders': orders.count(),
        'pending_orders': orders.filter(status__in=['pending', 'accepted', 'preparing']).count(),
        'today_revenue': today_orders.aggregate(Sum('total'))['total__sum'] or 0,
        'total_products': products.count(),
    }
    
    return Response(DashboardStatsSerializer(stats).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def driver_dashboard(request):
    user = request.user
    if user.role != 'driver':
        return Response({'error': 'Unauthorized'}, status=403)
    
    deliveries = Order.objects.filter(driver=user)
    today = timezone.now().date()
    
    stats = {
        'total_deliveries': deliveries.filter(status='delivered').count(),
        'today_deliveries': deliveries.filter(status='delivered', updated_at__date=today).count(),
        'pending_missions': deliveries.exclude(status__in=['delivered', 'cancelled']).count(),
        'is_available': user.is_available,
    }
    
    return Response(DriverStatsSerializer(stats).data)


# ==================== TEAM MEMBERS ====================

class TeamMemberViewSet(viewsets.ModelViewSet):
    serializer_class = TeamMemberSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return TeamMember.objects.all()
        elif user.role == 'manager':
            return TeamMember.objects.filter(restaurant__manager=user)
        return TeamMember.objects.none()
    
    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'manager':
            restaurant = Restaurant.objects.filter(manager=user).first()
            if restaurant:
                serializer.save(restaurant=restaurant)
            else:
                raise serializers.ValidationError("No restaurant found for this manager")
        else:
            serializer.save()


# ==================== ADMIN ====================

class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def drivers(self, request):
        drivers = User.objects.filter(role='driver')
        serializer = self.get_serializer(drivers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def managers(self, request):
        managers = User.objects.filter(role='manager')
        serializer = self.get_serializer(managers, many=True)
        return Response(serializer.data)
