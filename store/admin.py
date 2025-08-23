from django.contrib import admin
from .models import Game, Order, OrderItem, GameKey


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'original_price', 'slug')
    search_fields = ('title',)
    list_filter = ('category',)
    prepopulated_fields = {"slug": ("title",)}


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'created_at', 'status', 'total_amount')
    list_filter = ('status', 'created_at')
    search_fields = ('email',)
    inlines = [OrderItemInline]


@admin.register(GameKey)
class GameKeyAdmin(admin.ModelAdmin):
    list_display = ('game', 'key', 'is_used', 'order', 'assigned_at')
    list_filter = ('is_used', 'game')
    search_fields = ('key',)
