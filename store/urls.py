from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('cart/', views.cart_detail, name='cart'),
    path('cart/add/<int:game_id>/', views.cart_add, name='cart_add'),
    path('cart/update/<int:game_id>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:game_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('order/success/<int:order_id>/', views.order_success, name='order_success'),
]

