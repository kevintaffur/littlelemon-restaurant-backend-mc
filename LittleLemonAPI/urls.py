from django.urls import path
from . import views

urlpatterns = [
    # # User registration and token generation.
    # path('users', views.users, name='users'),
    # path('users/me', views.current_user, name='current_user'),
    # path('token/login', views.login, name='login'),

    # Menu items.
    path('menu-items', views.menu_items, name='menu_items'),
    path('menu-items/<int:menuitem_id>', views.single_menu_item, name='single_menu_item'),

    # User group managment.
    path('groups/manager/users', views.managers, name='managers'),
    path('groups/manager/users/<int:user_id>', views.manager, name='manager'),
    path('groups/delivery-crew/users', views.delivery_crew, name='delivery_crew'),
    path('groups/delivery-crew/users/<int:user_id>', views.delivery, name='delivery'),

    # Cart.
    path('cart/menu-items', views.cart, name='cart'),

    # Order managment.
    path('orders', views.orders, name='orders'),
    path('orders/<int:order_id>', views.order, name='order'),

    # Item of the day.
    path('item-of-the-day', views.item_of_the_day, name='item_of_the_day'),
]