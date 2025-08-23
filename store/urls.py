from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('game/<int:pk>/', views.game_detail, name='game_detail'),
    path('game/<int:pk>/<slug:slug>/', views.game_detail, name='game_detail_slug'),
    path('buy-now/<int:game_id>/', views.buy_now, name='buy_now'),
    path('cart/', views.cart_detail, name='cart'),
    path('cart/add/<int:game_id>/', views.cart_add, name='cart_add'),
    path('cart/update/<int:game_id>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:game_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),
]
