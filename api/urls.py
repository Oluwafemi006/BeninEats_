from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView, LoginView, LogoutView, ProfileView,
    CategoryViewSet, RestaurantViewSet, ProductViewSet,
    CartView, CartItemView, OrderViewSet,
    DriverScheduleViewSet, DriverMissionsView,
    BannerViewSet, app_settings,
    manager_dashboard, manager_restaurant, driver_dashboard,
    AdminUserViewSet, TeamMemberViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'restaurants', RestaurantViewSet)
router.register(r'products', ProductViewSet)
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'driver/schedule', DriverScheduleViewSet, basename='driver-schedule')
router.register(r'banners', BannerViewSet)
router.register(r'team', TeamMemberViewSet, basename='team')
router.register(r'admin/users', AdminUserViewSet, basename='admin-users')

urlpatterns = [
    # Auth
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', ProfileView.as_view(), name='profile'),
    
    # Cart
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/items/', CartItemView.as_view(), name='cart-items'),
    
    # Driver
    path('driver/missions/', DriverMissionsView.as_view(), name='driver-missions'),
    path('driver/dashboard/', driver_dashboard, name='driver-dashboard'),
    
    # Manager
    path('manager/dashboard/', manager_dashboard, name='manager-dashboard'),
    path('manager/restaurant/', manager_restaurant, name='manager-restaurant'),
    
    # Settings
    path('settings/', app_settings, name='app-settings'),
    
    # Router URLs
    path('', include(router.urls)),
]
