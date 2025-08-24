from django.db import models
from django.core.validators import FileExtensionValidator


class Game(models.Model):
    CATEGORY_CHOICES = [
        ('offline-account', 'Offline Account'),
        ('online-account', 'Online Account'),
        ('account-rent', 'Account Rent'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    image = models.URLField(help_text='Image URL', blank=True)
    description = models.TextField(blank=True)
    instructions = models.TextField(blank=True, help_text='Optional instructions shown on delivery page for offline accounts')
    rotation_index = models.PositiveIntegerField(default=0, help_text='Round-robin pointer for offline account credentials')

    def __str__(self):
        return self.title

    @property
    def discount_percent(self):
        if self.original_price and self.original_price > 0 and self.original_price > self.price:
            return int(round((1 - (self.price / self.original_price)) * 100))
        return 0

    def save(self, *args, **kwargs):
        from django.utils.text import slugify
        if not self.slug:
            base = slugify(self.title) or 'game'
            slug = base
            idx = 1
            Model = self.__class__
            while Model.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                idx += 1
                slug = f"{base}-{idx}"
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('game_detail', args=[self.pk])


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('partial', 'Partial Delivery'),
    ]

    email = models.EmailField()
    name = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Order #{self.id} - {self.email}"

    @property
    def total_amount(self):
        return sum(item.subtotal for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.game.title} x{self.quantity}"

    @property
    def subtotal(self):
        return self.unit_price * self.quantity



class GameCredential(models.Model):
    game = models.ForeignKey(Game, related_name='credentials', on_delete=models.CASCADE)
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    notes = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.game.title} - {self.username}"


class OfflineCredentialAssignment(models.Model):
    order = models.ForeignKey(Order, related_name='offline_assignments', on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.order_id} - {self.game.title} ({self.username})"


class DeliveryLink(models.Model):
    order = models.OneToOneField(Order, related_name='delivery_link', on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        from django.utils import timezone
        return timezone.now() <= self.expires_at

    def __str__(self):
        return f"DeliveryLink for Order #{self.order_id}"


class EmailAccessLink(models.Model):
    email = models.EmailField()
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        from django.utils import timezone
        return timezone.now() <= self.expires_at

    def __str__(self):
        return f"EmailAccessLink for {self.email}"


class ChatMessage(models.Model):
    SENDER_CHOICES = [
        ('customer', 'Customer'),
        ('admin', 'Admin'),
    ]
    order = models.ForeignKey(Order, related_name='chat_messages', on_delete=models.CASCADE)
    sender = models.CharField(max_length=20, choices=SENDER_CHOICES, default='customer')
    message = models.TextField(blank=True)
    image = models.FileField(upload_to='chat_uploads/%Y/%m/%d', null=True, blank=True,
                             validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif', 'webp'])])
    is_read = models.BooleanField(default=False, help_text='Marked read by staff when viewed')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"ChatMessage(order={self.order_id}, sender={self.sender})"


class OrderChat(Order):
    class Meta:
        proxy = True
        verbose_name = 'Chat'
        verbose_name_plural = 'Chats'
