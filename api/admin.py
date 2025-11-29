from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Count, Sum
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    User, Category, Restaurant, Product, Cart, CartItem,
    Order, OrderItem, DriverSchedule, Banner, AppSettings
)


# ==================== CUSTOM ADMIN SITE ====================

admin.site.site_header = "BeninEats Administration"
admin.site.site_title = "BeninEats Admin"
admin.site.index_title = "Tableau de Bord"


# ==================== USER ADMIN ====================

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role_badge', 'phone', 'availability_status', 'is_active', 'date_joined']
    list_filter = ['role', 'is_available', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'phone', 'first_name', 'last_name']
    ordering = ['-date_joined']
    list_per_page = 25
    
    fieldsets = UserAdmin.fieldsets + (
        ('🍽️ BeninEats Info', {
            'fields': ('role', 'phone', 'address', 'avatar', 'is_available'),
            'classes': ('wide',),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('🍽️ BeninEats Info', {
            'fields': ('role', 'phone', 'address'),
            'classes': ('wide',),
        }),
    )
    
    def role_badge(self, obj):
        colors = {
            'client': '#28a745',
            'driver': '#17a2b8',
            'manager': '#ffc107',
            'admin': '#dc3545',
        }
        color = colors.get(obj.role, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 15px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_role_display()
        )
    role_badge.short_description = 'Rôle'
    
    def availability_status(self, obj):
        if obj.role == 'driver':
            if obj.is_available:
                return format_html('<span style="color: #28a745;">● En ligne</span>')
            return format_html('<span style="color: #dc3545;">● Hors ligne</span>')
        return '-'
    availability_status.short_description = 'Statut'
    
    actions = ['make_available', 'make_unavailable']
    
    @admin.action(description='✅ Marquer comme disponible')
    def make_available(self, request, queryset):
        queryset.filter(role='driver').update(is_available=True)
    
    @admin.action(description='❌ Marquer comme indisponible')
    def make_unavailable(self, request, queryset):
        queryset.filter(role='driver').update(is_available=False)


# ==================== CATEGORY ADMIN ====================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon_preview', 'image_preview', 'restaurant_count', 'is_active', 'order']
    list_editable = ['is_active', 'order']
    search_fields = ['name']
    list_filter = ['is_active']
    ordering = ['order', 'name']
    
    def icon_preview(self, obj):
        return format_html('<i class="fas fa-{}"></i> {}', obj.icon, obj.icon)
    icon_preview.short_description = 'Icône'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 5px;"/>', obj.image.url)
        return '-'
    image_preview.short_description = 'Image'
    
    def restaurant_count(self, obj):
        count = obj.restaurants.count()
        return format_html('<span class="badge badge-info">{}</span>', count)
    restaurant_count.short_description = 'Restaurants'


# ==================== RESTAURANT ADMIN ====================

class ProductInline(admin.TabularInline):
    model = Product
    extra = 0
    fields = ['name', 'price', 'is_available', 'is_popular', 'is_featured']
    readonly_fields = []
    show_change_link = True


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ['image_preview', 'name', 'manager_link', 'rating_display', 
                    'product_count', 'order_count', 'status_badge', 'is_active']
    list_filter = ['is_open', 'is_active', 'categories', 'created_at']
    search_fields = ['name', 'address', 'phone', 'manager__username']
    filter_horizontal = ['categories']
    list_editable = ['is_active']
    ordering = ['-created_at']
    list_per_page = 20
    inlines = [ProductInline]
    
    fieldsets = (
        ('📝 Informations de base', {
            'fields': ('name', 'description', 'manager'),
        }),
        ('📷 Images', {
            'fields': ('image', 'cover_image'),
            'classes': ('collapse',),
        }),
        ('📍 Localisation & Contact', {
            'fields': ('address', 'phone'),
        }),
        ('⭐ Évaluations', {
            'fields': ('rating', 'rating_count'),
        }),
        ('🚚 Livraison', {
            'fields': ('delivery_time', 'delivery_fee', 'minimum_order'),
        }),
        ('🏷️ Catégories', {
            'fields': ('categories',),
        }),
        ('⚙️ Statut', {
            'fields': ('is_open', 'is_active'),
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 8px;"/>',
                obj.image.url
            )
        return format_html('<span style="color: #999;">Pas d\'image</span>')
    image_preview.short_description = 'Photo'
    
    def manager_link(self, obj):
        if obj.manager:
            url = reverse('admin:api_user_change', args=[obj.manager.id])
            return format_html('<a href="{}">{}</a>', url, obj.manager.username)
        return format_html('<span style="color: #999;">Non assigné</span>')
    manager_link.short_description = 'Gérant'
    
    def rating_display(self, obj):
        stars = '⭐' * int(obj.rating)
        return format_html('{} <small>({} avis)</small>', stars or '☆', obj.rating_count)
    rating_display.short_description = 'Note'
    
    def product_count(self, obj):
        count = obj.products.count()
        url = reverse('admin:api_product_changelist') + f'?restaurant__id__exact={obj.id}'
        return format_html('<a href="{}" class="badge badge-primary">{} produits</a>', url, count)
    product_count.short_description = 'Produits'
    
    def order_count(self, obj):
        count = obj.orders.count()
        url = reverse('admin:api_order_changelist') + f'?restaurant__id__exact={obj.id}'
        return format_html('<a href="{}" class="badge badge-success">{} commandes</a>', url, count)
    order_count.short_description = 'Commandes'
    
    def status_badge(self, obj):
        if obj.is_open:
            return format_html('<span style="color: #28a745; font-weight: bold;">🟢 Ouvert</span>')
        return format_html('<span style="color: #dc3545; font-weight: bold;">🔴 Fermé</span>')
    status_badge.short_description = 'Statut'
    
    actions = ['open_restaurants', 'close_restaurants']
    
    @admin.action(description='🟢 Ouvrir les restaurants sélectionnés')
    def open_restaurants(self, request, queryset):
        queryset.update(is_open=True)
        self.message_user(request, f'{queryset.count()} restaurant(s) ouvert(s)')
    
    @admin.action(description='🔴 Fermer les restaurants sélectionnés')
    def close_restaurants(self, request, queryset):
        queryset.update(is_open=False)
        self.message_user(request, f'{queryset.count()} restaurant(s) fermé(s)')


# ==================== PRODUCT ADMIN ====================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['image_preview', 'name', 'restaurant_link', 'category', 
                    'price_display', 'is_available', 'is_popular', 'is_featured']
    list_filter = ['restaurant', 'category', 'is_available', 'is_popular', 'is_featured', 'created_at']
    search_fields = ['name', 'description', 'restaurant__name']
    list_editable = ['is_available', 'is_popular', 'is_featured']
    ordering = ['-created_at']
    list_per_page = 25
    autocomplete_fields = ['restaurant', 'category']
    
    fieldsets = (
        ('📝 Informations', {
            'fields': ('name', 'description', 'restaurant', 'category'),
        }),
        ('💰 Prix', {
            'fields': ('price',),
        }),
        ('📷 Image', {
            'fields': ('image',),
        }),
        ('⚙️ Options', {
            'fields': ('is_available', 'is_popular', 'is_featured'),
            'classes': ('wide',),
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 5px;"/>',
                obj.image.url
            )
        return '-'
    image_preview.short_description = 'Photo'
    
    def restaurant_link(self, obj):
        url = reverse('admin:api_restaurant_change', args=[obj.restaurant.id])
        return format_html('<a href="{}">{}</a>', url, obj.restaurant.name)
    restaurant_link.short_description = 'Restaurant'
    
    def price_display(self, obj):
        return format_html('<strong>{} FCFA</strong>', f'{obj.price:,}')
    price_display.short_description = 'Prix'
    
    def availability_badge(self, obj):
        if obj.is_available:
            return format_html('<span style="color: #28a745;">✓ Disponible</span>')
        return format_html('<span style="color: #dc3545;">✗ Indisponible</span>')
    availability_badge.short_description = 'Disponibilité'
    
    def popular_badge(self, obj):
        if obj.is_popular:
            return format_html('<span style="color: #ffc107;">🔥 Populaire</span>')
        return '-'
    popular_badge.short_description = 'Populaire'
    
    def featured_badge(self, obj):
        if obj.is_featured:
            return format_html('<span style="color: #17a2b8;">⭐ À la une</span>')
        return '-'
    featured_badge.short_description = 'À la une'
    
    actions = ['mark_available', 'mark_unavailable', 'mark_popular', 'mark_featured']
    
    @admin.action(description='✅ Marquer comme disponible')
    def mark_available(self, request, queryset):
        queryset.update(is_available=True)
    
    @admin.action(description='❌ Marquer comme indisponible')
    def mark_unavailable(self, request, queryset):
        queryset.update(is_available=False)
    
    @admin.action(description='🔥 Marquer comme populaire')
    def mark_popular(self, request, queryset):
        queryset.update(is_popular=True)
    
    @admin.action(description='⭐ Marquer à la une')
    def mark_featured(self, request, queryset):
        queryset.update(is_featured=True)


# ==================== ORDER ADMIN ====================

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'product_name', 'product_price', 'quantity', 'subtotal_display']
    can_delete = False
    
    def subtotal_display(self, obj):
        return format_html('<strong>{} FCFA</strong>', f'{obj.subtotal:,}')
    subtotal_display.short_description = 'Sous-total'
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'customer_info', 'restaurant_link', 'items_count', 
                    'total_display', 'status_badge', 'driver_info', 'time_ago']
    list_filter = ['status', 'restaurant', 'created_at']
    search_fields = ['id', 'user__username', 'customer_name', 'customer_phone', 'restaurant__name']
    readonly_fields = ['created_at', 'updated_at', 'total']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 30
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('📋 Commande', {
            'fields': ('user', 'restaurant', 'status'),
        }),
        ('👤 Client', {
            'fields': ('customer_name', 'customer_phone', 'delivery_address'),
        }),
        ('💰 Paiement', {
            'fields': ('total', 'delivery_fee'),
        }),
        ('🚚 Livraison', {
            'fields': ('driver', 'notes'),
        }),
        ('📅 Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def order_id(self, obj):
        return format_html('<strong>#{}</strong>', str(obj.id)[-6:].upper())
    order_id.short_description = 'N° Commande'
    
    def customer_info(self, obj):
        return format_html(
            '<strong>{}</strong><br><small style="color: #666;">{}</small>',
            obj.customer_name, obj.customer_phone
        )
    customer_info.short_description = 'Client'
    
    def restaurant_link(self, obj):
        url = reverse('admin:api_restaurant_change', args=[obj.restaurant.id])
        return format_html('<a href="{}">{}</a>', url, obj.restaurant.name)
    restaurant_link.short_description = 'Restaurant'
    
    def items_count(self, obj):
        count = obj.items.count()
        return format_html('<span class="badge badge-info">{} article(s)</span>', count)
    items_count.short_description = 'Articles'
    
    def total_display(self, obj):
        total_with_delivery = obj.total + obj.delivery_fee
        return format_html(
            '<strong style="color: #28a745;">{} FCFA</strong>',
            f'{total_with_delivery:,}'
        )
    total_display.short_description = 'Total'
    
    def status_badge(self, obj):
        colors = {
            'pending': ('#ffc107', '⏳'),
            'accepted': ('#17a2b8', '✓'),
            'preparing': ('#fd7e14', '👨‍🍳'),
            'ready': ('#20c997', '📦'),
            'assigned': ('#6f42c1', '🚴'),
            'picked_up': ('#007bff', '🛵'),
            'delivering': ('#0dcaf0', '🚚'),
            'delivered': ('#28a745', '✅'),
            'cancelled': ('#dc3545', '❌'),
        }
        color, icon = colors.get(obj.status, ('#6c757d', '?'))
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 12px; font-size: 11px;">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    status_badge.short_description = 'Statut'
    
    def driver_info(self, obj):
        if obj.driver:
            status = '🟢' if obj.driver.is_available else '🔴'
            return format_html('{} {}', status, obj.driver.username)
        return format_html('<span style="color: #999;">Non assigné</span>')
    driver_info.short_description = 'Livreur'
    
    def time_ago(self, obj):
        from django.utils.timesince import timesince
        return format_html('<small style="color: #666;">Il y a {}</small>', timesince(obj.created_at))
    time_ago.short_description = 'Créée'
    
    actions = ['accept_orders', 'mark_preparing', 'mark_ready', 'mark_delivered', 'cancel_orders']
    
    @admin.action(description='✓ Accepter les commandes')
    def accept_orders(self, request, queryset):
        queryset.filter(status='pending').update(status='accepted')
    
    @admin.action(description='👨‍🍳 Marquer en préparation')
    def mark_preparing(self, request, queryset):
        queryset.filter(status='accepted').update(status='preparing')
    
    @admin.action(description='📦 Marquer comme prêt')
    def mark_ready(self, request, queryset):
        queryset.filter(status='preparing').update(status='ready')
    
    @admin.action(description='✅ Marquer comme livré')
    def mark_delivered(self, request, queryset):
        queryset.update(status='delivered')
    
    @admin.action(description='❌ Annuler les commandes')
    def cancel_orders(self, request, queryset):
        queryset.update(status='cancelled')


# ==================== CART ADMIN ====================

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['subtotal_display']
    
    def subtotal_display(self, obj):
        return format_html('{} FCFA', f'{obj.subtotal:,}')
    subtotal_display.short_description = 'Sous-total'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'items_count', 'total_display', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['updated_at']
    inlines = [CartItemInline]
    
    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'Articles'
    
    def total_display(self, obj):
        total = sum(item.subtotal for item in obj.items.all())
        return format_html('{} FCFA', f'{total:,}')
    total_display.short_description = 'Total'


# ==================== DRIVER SCHEDULE ADMIN ====================

@admin.register(DriverSchedule)
class DriverScheduleAdmin(admin.ModelAdmin):
    list_display = ['driver', 'day_display', 'schedule_display', 'status_badge']
    list_filter = ['driver', 'day', 'is_enabled']
    search_fields = ['driver__username']
    ordering = ['driver', 'day']
    
    def day_display(self, obj):
        days_fr = {
            'monday': 'Lundi', 'tuesday': 'Mardi', 'wednesday': 'Mercredi',
            'thursday': 'Jeudi', 'friday': 'Vendredi', 'saturday': 'Samedi', 'sunday': 'Dimanche'
        }
        return days_fr.get(obj.day, obj.day)
    day_display.short_description = 'Jour'
    
    def schedule_display(self, obj):
        if obj.is_enabled:
            return format_html('🕐 {} - {}', obj.start_time.strftime('%H:%M'), obj.end_time.strftime('%H:%M'))
        return '-'
    schedule_display.short_description = 'Horaires'
    
    def status_badge(self, obj):
        if obj.is_enabled:
            return format_html('<span style="color: #28a745;">✓ Actif</span>')
        return format_html('<span style="color: #999;">Inactif</span>')
    status_badge.short_description = 'Statut'


# ==================== BANNER ADMIN ====================

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['image_preview', 'title', 'subtitle', 'link_info', 'is_active', 'order']
    list_editable = ['is_active', 'order']
    search_fields = ['title', 'subtitle']
    list_filter = ['is_active', 'link_type']
    ordering = ['order']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 120px; height: 60px; object-fit: cover; border-radius: 5px;"/>',
                obj.image.url
            )
        return '-'
    image_preview.short_description = 'Image'
    
    def link_info(self, obj):
        if obj.link_type and obj.link_id:
            return format_html('{}#{}'.format(obj.link_type, obj.link_id))
        return '-'
    link_info.short_description = 'Lien'


# ==================== APP SETTINGS ADMIN ====================

@admin.register(AppSettings)
class AppSettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'description']
    search_fields = ['key', 'description']
    ordering = ['key']
