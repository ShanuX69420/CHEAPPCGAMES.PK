from django.contrib import admin
from django.db.models import Max, Count, Q
from .models import Game, Order, OrderItem, GameCredential, OfflineCredentialAssignment, DeliveryLink, EmailAccessLink, ChatMessage, OrderChat


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


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 1
    fields = ('message', 'created_at')
    readonly_fields = ('created_at',)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in instances:
            if isinstance(obj, ChatMessage) and not obj.pk:
                obj.sender = 'admin'
                obj.is_read = True
            obj.save()
        formset.save_m2m()


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'created_at', 'status', 'total_amount')
    list_filter = ('status', 'created_at')
    search_fields = ('email',)
    inlines = [OrderItemInline]




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


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('order', 'sender', 'short_message', 'created_at')
    list_filter = ('sender', 'created_at')
    search_fields = ('order__email', 'message')

    def short_message(self, obj):
        return (obj.message[:60] + '…') if len(obj.message) > 60 else obj.message
    short_message.short_description = 'Message'


@admin.register(OrderChat)
class ChatOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'created_at', 'last_message_at', 'unread_messages')
    search_fields = ('email', 'id')
    change_form_template = 'admin/store/orderchat/change_form.html'
    inlines = []
    fields = []

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.annotate(
            last_message=Max('chat_messages__created_at'),
            unread=Count('chat_messages', filter=Q(chat_messages__sender='customer', chat_messages__is_read=False)),
        )
        return qs.filter(last_message__isnull=False).order_by('-last_message')

    def last_message_at(self, obj):
        return obj.last_message
    last_message_at.admin_order_field = 'last_message'
    last_message_at.short_description = 'Last message'

    def unread_messages(self, obj):
        return obj.unread
    unread_messages.admin_order_field = 'unread'
    unread_messages.short_description = 'Unread'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        # Mark customer messages as read when viewing the chat
        try:
            ChatMessage.objects.filter(order_id=object_id, sender='customer', is_read=False).update(is_read=True)
        except Exception:
            pass
        return super().change_view(request, object_id, form_url, extra_context)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom = [
            path('<path:object_id>/reply/', self.admin_site.admin_view(self.reply_view), name='store_orderchat_reply'),
            path('<path:object_id>/messages/', self.admin_site.admin_view(self.messages_view), name='store_orderchat_messages'),
            path('unread-count/', self.admin_site.admin_view(self.unread_count_view), name='store_orderchat_unread'),
            path('badge/', self.admin_site.admin_view(self.badge_view), name='store_orderchat_badge'),
        ]
        return custom + urls

    def reply_view(self, request, object_id):
        from django.shortcuts import redirect
        if request.method == 'POST' and request.user.has_perm('store.change_order'):
            text = (request.POST.get('message') or '').strip()
            image = request.FILES.get('image')
            # basic validation for image
            if image and not getattr(image, 'content_type', '').startswith('image/'):
                image = None
            if image and getattr(image, 'size', 0) > 5 * 1024 * 1024:
                image = None
            if text or image:
                ChatMessage.objects.create(order_id=object_id, sender='admin', message=text, image=image, is_read=True)
        from django.urls import reverse
        return redirect(reverse('admin:store_orderchat_change', args=[object_id]))

    def messages_view(self, request, object_id):
        from django.shortcuts import render
        msgs = ChatMessage.objects.filter(order_id=object_id)
        return render(request, 'store/partials/chat_messages.html', {'messages': msgs, 'viewer': 'admin'})

    def unread_count_view(self, request):
        from django.http import JsonResponse
        count = ChatMessage.objects.filter(sender='customer', is_read=False).count()
        return JsonResponse({'unread': count})

    def badge_view(self, request):
        from django.shortcuts import render
        count = ChatMessage.objects.filter(sender='customer', is_read=False).count()
        return render(request, 'admin/partials/chat_badge.html', {'unread': count})

    # Using default admin change form with inline; no extra URLs


 
