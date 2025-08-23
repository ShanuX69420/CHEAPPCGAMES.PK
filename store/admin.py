from django.contrib import admin
from .models import Game, Order, OrderItem, GameKey, GameCredential, OfflineCredentialAssignment, DeliveryLink, EmailAccessLink


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'original_price', 'slug')
    search_fields = ('title',)
    list_filter = ('category',)
    prepopulated_fields = {"slug": ("title",)}


@admin.register(GameCredential)
class GameCredentialAdmin(admin.ModelAdmin):
    list_display = ('game', 'username', 'notes')
    list_filter = ('game',)
    search_fields = ('username', 'game__title')


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


@admin.register(OfflineCredentialAssignment)
class OfflineCredentialAssignmentAdmin(admin.ModelAdmin):
    list_display = ('order', 'game', 'username', 'created_at')
    list_filter = ('game', 'created_at')
    search_fields = ('order__email', 'username')


@admin.register(DeliveryLink)
class DeliveryLinkAdmin(admin.ModelAdmin):
    list_display = ('order', 'token', 'created_at', 'expires_at')
    search_fields = ('token', 'order__email')


@admin.register(EmailAccessLink)
class EmailAccessLinkAdmin(admin.ModelAdmin):
    list_display = ('email', 'token', 'created_at', 'expires_at')
    search_fields = ('email', 'token')
