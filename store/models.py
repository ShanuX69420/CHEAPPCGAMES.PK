from django.db import models


class Game(models.Model):
    CATEGORY_CHOICES = [
        ('offline-account', 'Offline Account'),
        ('license-key', 'License Key'),
        ('account-rent', 'Account Rent'),
    ]

    title = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    image = models.URLField(help_text='Image URL', blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title

    @property
    def discount_percent(self):
        if self.original_price and self.original_price > 0 and self.original_price > self.price:
            return int(round((1 - (self.price / self.original_price)) * 100))
        return 0


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


class GameKey(models.Model):
    game = models.ForeignKey(Game, related_name='keys', on_delete=models.CASCADE)
    key = models.CharField(max_length=255, unique=True)
    is_used = models.BooleanField(default=False)
    order = models.ForeignKey(Order, related_name='assigned_keys', on_delete=models.SET_NULL, null=True, blank=True)
    assigned_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.game.title} - {'USED' if self.is_used else 'FREE'} - {self.key[:8]}..."

