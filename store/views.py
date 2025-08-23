from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.db import transaction
from django.utils import timezone
from django.core.mail import send_mail

from .models import Game, Order, OrderItem, GameKey
from .forms import CheckoutForm


def _is_htmx(request):
    return request.headers.get('HX-Request') == 'true'


def home(request):
    games = Game.objects.all().order_by('-id')
    category = request.GET.get('category')
    q = request.GET.get('q')
    sort = request.GET.get('sort')

    if category:
        games = games.filter(category=category)
    if q:
        games = games.filter(title__icontains=q)
    if sort == 'price-asc':
        games = games.order_by('price')
    elif sort == 'price-desc':
        games = games.order_by('-price')

    context = {
        'games': games,
        'category': category or '',
        'q': q or '',
        'sort': sort or '',
        'categories': [
            ('', 'All'),
            ('offline-account', 'Offline Account'),
            ('license-key', 'License Key'),
            ('account-rent', 'Account Rent'),
        ],
    }

    if _is_htmx(request):
        return render(request, 'store/partials/game_grid.html', context)
    return render(request, 'store/home.html', context)


# CART UTILITIES
def _get_cart(session):
    return session.setdefault('cart', {})


def _cart_totals(cart):
    item_list = []
    total = 0
    for game_id, qty in cart.items():
        try:
            game = Game.objects.get(id=int(game_id))
            qty = int(qty)
        except (Game.DoesNotExist, ValueError):
            continue
        subtotal = game.price * qty
        total += subtotal
        item_list.append({'game': game, 'qty': qty, 'subtotal': subtotal})
    return item_list, total


def cart_detail(request):
    cart = request.session.get('cart', {})
    items, total = _cart_totals(cart)
    return render(request, 'store/cart.html', {'items': items, 'total': total})


def cart_add(request, game_id):
    if request.method != 'POST':
        return HttpResponse(status=405)
    cart = _get_cart(request.session)
    cart[str(game_id)] = int(cart.get(str(game_id), 0)) + int(request.POST.get('quantity', 1))
    request.session.modified = True
    items, total = _cart_totals(cart)
    if _is_htmx(request):
        return render(request, 'store/partials/cart_count.html', {'items': items}, status=200)
    return redirect('cart')


def cart_update(request, game_id):
    if request.method != 'POST':
        return HttpResponse(status=405)
    cart = _get_cart(request.session)
    try:
        qty = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        qty = 1
    if qty < 1:
        qty = 1
    cart[str(game_id)] = qty
    request.session.modified = True
    if _is_htmx(request):
        items, total = _cart_totals(cart)
        return render(request, 'store/partials/cart_table.html', {'items': items, 'total': total, 'is_htmx': True})
    return redirect('cart')


def cart_remove(request, game_id):
    cart = _get_cart(request.session)
    cart.pop(str(game_id), None)
    request.session.modified = True
    if _is_htmx(request):
        items, total = _cart_totals(cart)
        return render(request, 'store/partials/cart_table.html', {'items': items, 'total': total, 'is_htmx': True})
    return redirect('cart')


@transaction.atomic
def checkout(request):
    cart = request.session.get('cart', {})
    items, total = _cart_totals(cart)
    if not items:
        return redirect('home')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(
                email=form.cleaned_data['email'],
                name=form.cleaned_data.get('name', ''),
            )
            # create order items
            for it in items:
                OrderItem.objects.create(
                    order=order,
                    game=it['game'],
                    quantity=it['qty'],
                    unit_price=it['game'].price,
                )

            # allocate keys
            partial = False
            lines = []
            for it in order.items.select_related('game'):
                needed = it.quantity
                available = list(GameKey.objects.filter(game=it.game, is_used=False)[:needed])
                if len(available) < needed:
                    partial = True
                for idx, key_obj in enumerate(available):
                    key_obj.is_used = True
                    key_obj.order = order
                    key_obj.assigned_at = timezone.now()
                    key_obj.save()
                if available:
                    keys_text = '\n'.join([k.key for k in available])
                    lines.append(f"{it.game.title} ({len(available)}/{needed}):\n{keys_text}")
                else:
                    lines.append(f"{it.game.title}: No keys available yet.")

            order.status = 'partial' if partial else 'completed'
            order.save()

            # send email
            subject = 'Your Game Order'
            body = (
                f"Hello {order.name or ''}\n\n"
                f"Thank you for your purchase. Here are your keys (if available):\n\n"
                + '\n\n'.join(lines)
                + "\n\nIf some items are missing, we'll deliver them shortly."
            )
            send_mail(subject, body, None, [order.email], fail_silently=True)

            # clear cart
            request.session['cart'] = {}
            request.session.modified = True
            return redirect('order_success', order_id=order.id)
    else:
        form = CheckoutForm()

    return render(request, 'store/checkout.html', {'form': form, 'items': items, 'total': total})


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'store/order_success.html', {'order': order})
