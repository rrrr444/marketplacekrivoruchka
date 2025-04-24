from django.db.models import Avg, Sum, Count
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import F


class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    middle_name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    address = models.TextField(blank=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name="marketplace_user_groups",
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name="marketplace_user_permissions",
        blank=True,
    )


class Product(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    manufacturer = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/')
    rating = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


    def update_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            self.rating = reviews.aggregate(Avg('rating'))['rating__avg']
            self.save()


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Order(models.Model):
    PENDING = 'pending'
    SHIPPED = 'shipped'
    DELIVERED = 'delivered'

    STATUS_CHOICES = [
        (PENDING, 'В обработке'),
        (SHIPPED, 'Отправлено'),
        (DELIVERED, 'Доставлено'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    products = models.ManyToManyField('Product', through='OrderItem')  # Изменили items на products
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    address = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tracking_number = models.CharField(max_length=50, blank=True, null=True)



    def get_seller_total(self, seller):
        """Возвращает сумму заказа для конкретного продавца"""
        return self.order_items.filter(
            seller=seller
        ).annotate(
            item_total=F('product__price') * F('quantity')
        ).aggregate(
            total=Sum('item_total')
        )['total'] or 0

    def get_seller_items(self, seller):
        """Возвращает товары продавца в заказе"""
        return self.order_items.filter(seller=seller).select_related('product')

    def get_status_class(self):
        return {
            'pending': 'bg-info',
            'shipped': 'bg-warning',
            'delivered': 'bg-success'
        }.get(self.status, 'bg-secondary')

    def __str__(self):
        return f"Заказ #{self.id} - {self.get_status_display()}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    seller = models.ForeignKey(User, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if not self.seller_id:
            self.seller = self.product.seller
        super().save(*args, **kwargs)




class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField()
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Отзыв от {self.user.username} на {self.product.name}"


    class Meta:
        unique_together = ['product', 'user']  # Один отзыв на товар от пользователя

class News(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='news/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model, admin

User = get_user_model()

from django.contrib import admin

class Chat(models.Model):
    order = models.OneToOneField('Order', on_delete=models.CASCADE, related_name='chat')
    created_at = models.DateTimeField(auto_now_add=True)

    def get_seller(self):
        return self.order.order_items.first().seller if self.order.order_items.exists() else None

    def last_message(self):
        if hasattr(self, '_last_message'):
            return self._last_message
        msg = self.messages.last()
        self._last_message = f"{msg.sender.username}: {msg.text[:30]}..." if msg else "Нет сообщений"
        return self._last_message
    last_message.short_description = 'Последнее сообщение'  # Для админки

class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']