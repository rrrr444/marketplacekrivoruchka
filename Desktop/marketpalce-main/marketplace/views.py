from django.core.checks import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from django.db.models import Sum, Count, Avg, F  # Все агрегатные функции
from django.utils import timezone
from datetime import timedelta
from django.db.models import F
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Order
from .decorators import profile_complete_required
from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .models import Product, Cart, Order, OrderItem, Review, User, Notification
from .forms import (ProductForm, ReviewForm, ProfileForm,
                    OrderForm, CustomUserCreationForm, ShippingForm)
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Order
def home(request):
    products = Product.objects.order_by('-rating')
    query = request.GET.get('q')
    if query:
        products = products.filter(name__icontains=query) | products.filter(description__icontains=query)
    return render(request, 'marketplace/home.html', {'products': products})

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'marketplace/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'marketplace/login.html', {'form': form})

from django.shortcuts import redirect
@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)

    # Проверяем, может ли пользователь оставить отзыв
    can_review = Order.objects.filter(
        user=request.user,
        order_items__product=product,
        status=Order.DELIVERED
    ).exists() and not Review.objects.filter(
        user=request.user,
        product=product
    ).exists()

    if request.method == 'POST' and can_review:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()

            # Обновляем рейтинг товара
            product.update_rating()

            messages.success(request, "Ваш отзыв успешно сохранён!")
            # Перенаправляем на страницу товара с правильным pk
            return redirect('product_detail', pk=product.pk)  # Обновление редиректа
    else:
        form = ReviewForm()

    return render(request, 'marketplace/product_detail.html', {
        'product': product,
        'form': form,
        'can_review': can_review,
        'user_review': Review.objects.filter(user=request.user, product=product).first()
    })

@login_required
def cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'marketplace/cart.html', {
        'cart_items': cart_items,
        'total': total
    })

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={'quantity': 1}
    )
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('cart')

@login_required
def remove_from_cart(request, cart_id):
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    cart_item.delete()
    return redirect('cart')

@login_required
def checkout(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.total_price = sum(item.product.price * item.quantity for item in request.user.cart_set.all())
            order.save()
            for item in request.user.cart_set.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity
                )
            request.user.cart_set.all().delete()
            return redirect('orders')
    else:
        form = OrderForm()
    return render(request, 'marketplace/checkout.html', {'form': form})

@login_required
def orders(request):
    user_orders = Order.objects.filter(user=request.user).prefetch_related('order_items__product').order_by('-created_at')
    return render(request, 'marketplace/orders.html', {'orders': user_orders})


@login_required
def update_cart(request, cart_id, action):
    cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
    if action == 'increase':
        cart_item.quantity += 1
    elif action == 'decrease' and cart_item.quantity > 1:
        cart_item.quantity -= 1
    cart_item.save()
    return redirect('cart')


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import ProfileForm


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'marketplace/edit_profile.html', {'form': form})

@login_required
def complete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status == 'shipped':
        order.status = 'completed'
        order.save()
    return redirect('orders')

@login_required
def ship_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    # Проверяем что текущий пользователь - продавец товара в заказе
    if any(item.product.seller == request.user for item in order.items.all()):
        order.status = 'shipped'
        order.save()
    return redirect('seller_orders')


@login_required
def profile(request):
    user_products = Product.objects.filter(seller=request.user)
    return render(request, 'marketplace/profile.html', {
        'user_products': user_products
    })


def custom_logout(request):
    logout(request)
    messages.success(request, "Вы успешно вышли из системы")
    return redirect('home')

@login_required
@profile_complete_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            product.save()
            messages.success(request, 'Товар успешно добавлен!')
            return redirect('profile')
    else:
        form = ProductForm()
    return render(request, 'marketplace/add_product.html', {'form': form})


@login_required
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk, seller=request.user)

    if request.method == 'POST':
        print("Получен POST-запрос на редактирование товара")
        form = ProductForm(request.POST, request.FILES, instance=product)

        if form.is_valid():
            print("Форма валидна, сохраняем...")
            form.save()
            messages.success(request, 'Товар успешно обновлен!')
            return redirect('profile')
        else:
            print("Ошибки формы:", form.errors)
            messages.error(request, 'Исправьте ошибки в форме')
    else:
        form = ProductForm(instance=product)

    return render(request, 'marketplace/edit_product.html', {'form': form})
@login_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk, seller=request.user)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Товар успешно удалён!')
        return redirect('profile')
    return render(request, 'marketplace/delete_product.html', {'product': product})
def base_context(request):
    if request.user.is_authenticated:
        return {'cart_items_count': Cart.objects.filter(user=request.user).count()}
    return {}

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'marketplace/order_history.html', {'orders': orders})


from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta


@login_required
def seller_orders(request):
    # Получаем заказы за последние 30 дней
    time_threshold = timezone.now() - timedelta(days=30)

    # Получаем только товары текущего продавца
    seller_items = OrderItem.objects.filter(
        seller=request.user,
        order__created_at__gte=time_threshold
    )

    # Альтернативный способ расчёта без использования models.F
    total_sales = sum(
        item.product.price * item.quantity
        for item in seller_items.select_related('product')
    )

    # Общая статистика продаж
    sales_stats = {
        'total_sales': total_sales,
        'total_orders': seller_items.values('order').distinct().count(),
        'total_items': seller_items.aggregate(
            total=Sum('quantity')
        )['total'] or 0,
    }

    if sales_stats['total_orders'] > 0:
        sales_stats['avg_order'] = sales_stats['total_sales'] / sales_stats['total_orders']
    else:
        sales_stats['avg_order'] = 0

    # Последние 10 заказов
    orders = Order.objects.filter(
        order_items__seller=request.user
    ).distinct().order_by('-created_at')[:10]

    context = {
        'orders': orders,
        'sales_stats': sales_stats,
        'time_threshold': time_threshold.date(),
    }
    return render(request, 'marketplace/seller_orders.html', context)


@login_required
def confirm_receipt(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status != 'shipped':
        messages.error(request, 'Нельзя подтвердить неотправленный заказ')
        return redirect('order_history')

    if request.method == 'POST':
        order.status = 'completed'
        order.save()
        messages.success(request, 'Заказ успешно подтвержден')
        return redirect('order_history')

    return render(request, 'marketplace/confirm_shipment.html', {'order': order})


from django.db.models import Q




@login_required
def mark_order_shipped(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Проверка что пользователь - продавец в этом заказе
    if not order.items.filter(product__seller=request.user).exists():
        raise PermissionDenied

    if request.method == 'POST':
        form = ShippingForm(request.POST, instance=order)
        if form.is_valid():
            order = form.save(commit=False)
            order.status = 'shipped'
            order.save()

            # Уведомление для покупателя
            Notification.objects.create(
                user=order.user,
                message=f"Ваш заказ #{order.id} был отправлен. Трек-номер: {order.tracking_number}",
                order=order
            )

            messages.success(request, 'Заказ успешно помечен как отправленный')
            return redirect('seller_orders')
    else:
        form = ShippingForm(instance=order)

    return render(request, 'marketplace/mark_shipped.html', {
        'order': order,
        'form': form
    })


@login_required
def notifications(request):
    notifications = request.user.notifications.all()
    # Помечаем как прочитанные при просмотре
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'marketplace/notifications.html', {'notifications': notifications})


@login_required
def checkout(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.total_price = sum(item.product.price * item.quantity for item in request.user.cart_set.all())
            order.save()

            # Переносим товары в заказ
            for item in request.user.cart_set.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    seller=item.product.seller
                )

                # Уведомление для продавца
                Notification.objects.create(
                    user=item.product.seller,
                    message=f"Новый заказ #{order.id} на ваш товар {item.product.name}",
                    order=order
                )

            # Очищаем корзину
            request.user.cart_set.all().delete()

            messages.success(request, 'Заказ успешно оформлен!')
            return redirect('order_history')
    else:
        form = OrderForm(initial={'address': request.user.address})

    return render(request, 'marketplace/checkout.html', {'form': form})\

@login_required
def mark_all_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    messages.success(request, "Все уведомления помечены как прочитанные")
    return redirect('notifications')


@login_required
def sales_list(request):
    sales = Order.objects.filter(product__seller=request.user)
    return render(request, 'marketplace/sales_list.html', {'sales': sales})
from django.contrib.auth.decorators import login_required
from .models import Order, OrderItem

login_required


def seller_orders(request):
    time_threshold = timezone.now() - timedelta(days=30)

    # Статистика продаж
    sales_stats = {
        'total_sales': OrderItem.objects.filter(
            seller=request.user,
            order__created_at__gte=time_threshold
        ).annotate(
            item_total=F('product__price') * F('quantity')
        ).aggregate(
            total=Sum('item_total')
        )['total'] or 0,
        'total_orders': Order.objects.filter(
            order_items__seller=request.user,
            created_at__gte=time_threshold
        ).distinct().count(),
        'total_items': OrderItem.objects.filter(
            seller=request.user,
            order__created_at__gte=time_threshold
        ).aggregate(
            total=Sum('quantity')
        )['total'] or 0,
    }

    if sales_stats['total_orders'] > 0:
        sales_stats['avg_order'] = sales_stats['total_sales'] / sales_stats['total_orders']
    else:
        sales_stats['avg_order'] = 0

    # Последние заказы
    orders = Order.objects.filter(
        order_items__seller=request.user
    ).distinct().order_by('-created_at')[:10]

    return render(request, 'marketplace/seller_orders.html', {
        'orders': orders,
        'sales_stats': sales_stats,
        'time_threshold': time_threshold.date(),
    })

@login_required
def buyer_orders(request):
    orders = Order.objects.filter(buyer=request.user)
    return render(request, 'marketplace/buyer_orders.html', {'orders': orders})





@login_required
def sales_list(request):
    """Список продаж для продавца"""
    sales = Order.objects.filter(product__seller=request.user).select_related('product', 'buyer')
    return render(request, 'marketplace/sales_list.html', {'sales': sales})


from django.shortcuts import render, get_object_or_404
from .models import Order

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Показываем только те товары, которые относятся к текущему пользователю-продавцу
    seller_items = order.order_items.filter(seller=request.user)

    return render(request, 'marketplace/order_detail.html', {
        'order': order,
        'seller_items': seller_items,
    })


@login_required
def confirm_shipment(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if not order.order_items.filter(seller=request.user).exists():
        raise PermissionDenied

    if request.method == 'POST':
        tracking_number = request.POST.get('tracking_number', '')
        order.status = Order.SHIPPED
        order.tracking_number = tracking_number
        order.save()

        Notification.objects.create(
            user=order.user,
            message=f"Ваш заказ #{order.id} отправлен. Трек: {tracking_number}",
            order=order
        )

        messages.success(request, "Заказ помечен как отправленный")
        return redirect('seller_orders')

    return render(request, 'marketplace/confirm_shipment.html', {'order': order})




@login_required
def confirm_delivery(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status != Order.SHIPPED:
        messages.error(request, "Можно подтвердить только отправленные заказы")
        return redirect('order_detail', order_id=order.id)

    if request.method == 'POST':
        order.status = Order.DELIVERED
        order.save()
        messages.success(request, "Получение подтверждено!")
        return redirect('order_detail', order_id=order.id)

    return render(request, 'marketplace/confirm_delivery.html', {'order': order})

from .models import News

def news_list(request):
    news_items = News.objects.order_by('-created_at')
    return render(request, 'marketplace/news_list.html', {'news_items': news_items})


from django.http import JsonResponse
from django.views.decorators.http import require_GET
from marketplace.models import Product

@require_GET
def product_autocomplete(request):
    query = request.GET.get('q', '')
    results = Product.objects.filter(name__icontains=query)[:10]
    data = [{'id': p.id, 'name': p.name} for p in results]
    return JsonResponse(data, safe=False)

from django.shortcuts import render
from django.http import JsonResponse
from .models import Product

# Для автоподсказок
from django.http import JsonResponse
from django.db.models import Q


def autocomplete(request):
    query = request.GET.get('q', '').strip()
    if not query or len(query) < 2:
        return JsonResponse([], safe=False)

    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(manufacturer__icontains=query)
    )[:5]

    suggestions = [{
        'name': p.name,
        'url': p.get_absolute_url(),
        'price': str(p.price)
    } for p in products]

    return JsonResponse(suggestions, safe=False)


# Для результатов поиска
def search_results(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return redirect('home')

    products = Product.objects.filter(
        models.Q(name__icontains=query) |
        models.Q(description__icontains=query) |
        models.Q(manufacturer__icontains=query)
    ).select_related('seller').order_by('-rating')

    return render(request, 'marketplace/search_results.html', {
        'products': products,
        'query': query
    })