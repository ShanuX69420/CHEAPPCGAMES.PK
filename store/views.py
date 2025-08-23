from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.db import transaction
from django.utils import timezone
from django.core.mail import send_mail

from .models import Game, Order, OrderItem, GameKey, GameCredential, OfflineCredentialAssignment, DeliveryLink, EmailAccessLink
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


def game_detail(request, pk, slug=None):
    game = get_object_or_404(Game, pk=pk)
    # related games by category
    related = Game.objects.filter(category=game.category).exclude(pk=game.pk)[:4]
    return render(request, 'store/detail.html', {
        'game': game,
        'related': related,
    })


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

            # allocate license keys and offline accounts
            partial = False
            lines = []
            for it in order.items.select_related('game'):
                needed = it.quantity
                if it.game.category == 'license-key':
                    available = list(GameKey.objects.filter(game=it.game, is_used=False)[:needed])
                    if len(available) < needed:
                        partial = True
                    for key_obj in available:
                        key_obj.is_used = True
                        key_obj.order = order
                        key_obj.assigned_at = timezone.now()
                        key_obj.save()
                    if available:
                        keys_text = '\n'.join([k.key for k in available])
                        lines.append(f"{it.game.title} ({len(available)}/{needed}):\n{keys_text}")
                    else:
                        lines.append(f"{it.game.title}: No keys available yet.")
                elif it.game.category == 'offline-account':
                    creds = list(GameCredential.objects.filter(game=it.game).order_by('id'))
                    if not creds:
                        partial = True
                    if creds:
                        count = len(creds)
                        start = it.game.rotation_index % count
                        for i in range(needed):
                            idx = (start + i) % count
                            c = creds[idx]
                            OfflineCredentialAssignment.objects.create(
                                order=order,
                                game=it.game,
                                username=c.username,
                                password=c.password,
                                notes=c.notes,
                            )
                        # advance rotation pointer
                        it.game.rotation_index = (start + needed) % count
                        it.game.save(update_fields=['rotation_index'])

            order.status = 'partial' if partial else 'completed'
            order.save()

            # create order access link (24h)
            import secrets
            order_token = secrets.token_urlsafe(32)
            order_link = DeliveryLink.objects.create(
                order=order,
                token=order_token,
                expires_at=timezone.now() + timezone.timedelta(hours=24),
            )

            # prepare email (send keys and offline credentials inline)
            subject = f"Your Cheappcgames Order #{order.id}"
            body = (
                f"Hello {order.name or 'there'}\n\n"
                f"Thank you for your purchase.\n"
                f"Order #: {order.id}\n"
            )
            if lines:
                body += "\n\nLicense Keys (if available):\n\n" + '\n\n'.join(lines)
            # include offline credentials inline (no numbering)
            if order.offline_assignments.exists():
                body += "\n\nOffline Account Credentials:\n"
                # group by game
                assignments = order.offline_assignments.select_related('game').order_by('game__title', 'created_at')
                grouped = {}
                for a in assignments:
                    grouped.setdefault(a.game, []).append(a)
                for game, creds in grouped.items():
                    body += f"\n{game.title}:\n"
                    if getattr(game, 'instructions', ''):
                        body += f"Instructions: {game.instructions}\n"
                    for c in creds:
                        body += f"Username: {c.username}\nPassword: {c.password}\n"
                        if c.notes:
                            body += f"Notes: {c.notes}\n"
                        body += "\n"
            # order page link
            url = request.build_absolute_uri(reverse('delivery_page', args=[order_link.token]))
            body += f"\nView your order page (valid 24 hours):\n{url}"

            body += "\n\nIf some items are missing, we'll deliver them shortly."
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


def buy_now(request, game_id):
    if request.method != 'POST':
        return redirect('game_detail', pk=game_id)
    try:
        qty = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        qty = 1
    if qty < 1:
        qty = 1
    # Replace cart with only this item for a clean checkout
    request.session['cart'] = {str(game_id): qty}
    request.session.modified = True
    return redirect('checkout')


def delivery_page(request, token):
    link = get_object_or_404(DeliveryLink, token=token)
    if not link.is_valid():
        return render(request, 'store/delivery_expired.html', status=410)
    # group assignments by game
    order = link.order
    assignments = order.offline_assignments.select_related('game').order_by('game__title', 'created_at')
    by_game = {}
    for a in assignments:
        by_game.setdefault(a.game, []).append(a)
    keys = list(GameKey.objects.filter(order=order).select_related('game'))
    items = list(order.items.select_related('game'))
    return render(request, 'store/delivery.html', {
        'order': order,
        'by_game': by_game,
        'link': link,
        'keys': keys,
        'items': items,
    })


def purchases_request(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        if email:
            import secrets
            token = secrets.token_urlsafe(32)
            expires_at = timezone.now() + timezone.timedelta(hours=24)
            EmailAccessLink.objects.create(email=email, token=token, expires_at=expires_at)
            url = request.build_absolute_uri(reverse('purchases_page', args=[token]))
            send_mail(
                'Your Cheappcgames purchases link',
                f'Hello,\n\nUse the link below to view all purchases associated with {email}. The link is valid for 24 hours.\n\n{url}\n\nIf you did not request this, you can ignore this email.',
                None,
                [email],
                fail_silently=True,
            )
            return render(request, 'store/purchases_sent.html', {'email': email})
    return render(request, 'store/purchases_request.html')


def purchases_page(request, token):
    link = get_object_or_404(EmailAccessLink, token=token)
    if not link.is_valid():
        return render(request, 'store/delivery_expired.html', status=410)
    orders = Order.objects.filter(email__iexact=link.email).order_by('-created_at')
    # preload related data
    gamekeys = {o.id: list(GameKey.objects.filter(order=o)) for o in orders}
    assignments = {o.id: list(o.offline_assignments.select_related('game').all()) for o in orders}
    for o in orders:
        setattr(o, 'keys_list', gamekeys.get(o.id, []))
        setattr(o, 'assignments_list', assignments.get(o.id, []))
    return render(request, 'store/purchases_list.html', {
        'link': link,
        'orders': orders,
    })
