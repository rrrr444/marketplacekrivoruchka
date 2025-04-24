from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import (Product, Cart, Order, Review, User, News,
                     OrderItem, Chat, Message)

admin.site.site_header = "Панель администратора Marketplace"
admin.site.index_title = "Управление маркетплейсом"
admin.site.site_title = "Админка"

# Упрощенная регистрация базовых моделей
admin.site.register(User)
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(Review)
admin.site.register(News)


# Кастомные админ-классы
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_link', 'product', 'seller', 'quantity', 'price')
    list_filter = ('seller',)
    search_fields = ('order__id', 'product__name', 'seller__username')

    def order_link(self, obj):
        url = reverse('admin:marketplace_order_change', args=[obj.order.id])
        return format_html('<a href="{}">Заказ #{}</a>', url, obj.order.id)

    order_link.short_description = 'Заказ'

    def price(self, obj):
        return obj.product.price * obj.quantity

    price.short_description = 'Сумма'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'sellers_list', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('id', 'user__username')
    readonly_fields = ('created_at', 'updated_at')

    def sellers_list(self, obj):
        sellers = set(item.seller.username for item in obj.order_items.all())
        return ", ".join(sellers)

    sellers_list.short_description = 'Продавцы'


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('sender', 'text', 'timestamp', 'is_read')
    ordering = ('-timestamp',)
    can_delete = False


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_link', 'buyer', 'seller', 'created_at', 'message_count', 'last_message')
    list_filter = ('created_at',)
    search_fields = ('order__id', 'order__user__username')
    inlines = [MessageInline]

    def order_link(self, obj):
        url = reverse('admin:marketplace_order_change', args=[obj.order.id])
        return format_html('<a href="{}">Заказ #{}</a>', url, obj.order.id)

    order_link.short_description = 'Заказ'

    def buyer(self, obj):
        return obj.order.user.username

    buyer.short_description = 'Покупатель'

    def seller(self, obj):
        seller = obj.get_seller()
        return seller.username if seller else '-'

    seller.short_description = 'Продавец'

    def message_count(self, obj):
        return obj.messages.count()

    message_count.short_description = 'Сообщений'

    def last_message(self, obj):
        return obj.last_message()

    last_message.short_description = 'Последнее сообщение'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat_link', 'sender', 'short_text', 'timestamp', 'is_read')
    list_filter = ('timestamp', 'is_read')
    search_fields = ('text', 'sender__username')
    list_editable = ('is_read',)
    readonly_fields = ('timestamp',)

    def chat_link(self, obj):
        url = reverse('admin:marketplace_chat_change', args=[obj.chat.id])
        return format_html('<a href="{}">Чат #{}</a>', url, obj.chat.id)

    chat_link.short_description = 'Чат'

    def short_text(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text

    short_text.short_description = 'Текст'