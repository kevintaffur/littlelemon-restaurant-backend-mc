from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from django.contrib.auth.models import User
from rest_framework import status
from .serializers import UserSerializer
from .serializers import MenuItemSerializer
from .models import MenuItem
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import Group
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import Cart
from .serializers import CartSerializer
from .models import Category
from django.forms.models import model_to_dict
from .serializers import OrderSerializer
from .serializers import OrderItemSerializer
from .models import Order, OrderItem
from rest_framework.throttling import AnonRateThrottle
from rest_framework.throttling import UserRateThrottle
from django.core.paginator import Paginator, EmptyPage

def get_value_from_user(req, dic, value):
    try:
        obj = req.data[value]
        if value == 'delivery_crew':
            obj = get_object_or_404(User, username=obj)

    except KeyError:
        return dic.get(value)

    return obj

# @api_view(['GET', 'POST'])
# def users(request):
#     if request.method == 'GET':
#         users = User.objects.all()
#         serialized_users = UserSerializer(users, many=True)
#         return Response(serialized_users.data, status.HTTP_200_OK)

# @api_view(['GET'])
# def current_user(request):
#     user_id = request.user.id
#     user = User.objects.get(id=user_id)
#     serialized_user = UserSerializer(user)
#     print(serialized_user.data)
#     return Response(serialized_user.data, status.HTTP_200_OK)

# @api_view(['POST'])
# def login(request):
#     serialized_user = UserSerializer(data=request.data)
#     if serialized_user.is_valid():
#         return Response({'data': serialized_user.data}, status.HTTP_200_OK)

@api_view(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def menu_items(request):
    if request.method == 'GET':
        menuitems = MenuItem.objects.all()
        category_name = request.query_params.get('category')
        to_price = request.query_params.get('to_price')
        search = request.query_params.get('search')
        ordering = request.query_params.get('ordering')
        perpage = request.query_params.get('perpage', default=3)
        page = request.query_params.get('page', default=1)

        if category_name:
            menuitems = menuitems.filter(category_id__slug=category_name)
        if to_price:
            menuitems = menuitems.filter(price__lte=to_price)
        if search:
            menuitems = menuitems.filter(title__icontains=search)
        if ordering:
            ordering_fields = ordering.split(',')
            menuitems = menuitems.order_by(*ordering_fields)

        if int(perpage) > 5:
            perpage = 5

        paginator = Paginator(menuitems, per_page=perpage)
        try:
            menuitems = paginator.page(number=page)
        except EmptyPage:
            menuitems = []

        serialized_menuitems = MenuItemSerializer(menuitems, many=True)
        return Response(serialized_menuitems.data, status.HTTP_200_OK)

    if request.method == 'POST':
        if request.user.groups.filter(name='Manager').exists():
            serialized_menuitem = MenuItemSerializer(data=request.data)
            if serialized_menuitem.is_valid(raise_exception=True):
                serialized_menuitem.save()

            return Response(serialized_menuitem.data, status.HTTP_201_CREATED)

    return Response({'message': 'You are not authorized.'}, status.HTTP_403_FORBIDDEN)

@api_view(['GET', 'PUT', 'POST', 'PATCH', 'DELETE'])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def single_menu_item(request, menuitem_id):
    if request.method == 'GET':
        menuitem = get_object_or_404(MenuItem, id=menuitem_id)
        serialized_menuitem = MenuItemSerializer(menuitem)

        return Response(serialized_menuitem.data, status.HTTP_200_OK)

    if request.user.groups.filter(name='Manager').exists():
        if request.method == 'PUT' or request.method == 'PATCH':
            menuitem = get_object_or_404(MenuItem, id=menuitem_id)
            menuitem_dic = model_to_dict(menuitem)

            title = get_value_from_user(request, menuitem_dic, 'title')
            price = get_value_from_user(request, menuitem_dic, 'price')
            featured = get_value_from_user(request, menuitem_dic, 'featured')
            category_id = get_value_from_user(request, menuitem_dic, 'category_id')

            MenuItem.objects.filter(id=menuitem_id).update(title=title, price=price, featured=featured, category_id=category_id)

            return Response({'message': 'updated'}, status.HTTP_200_OK)

        if request.method == 'DELETE':
            menuitem = get_object_or_404(MenuItem, id=menuitem_id)
            menuitem.delete()

            return Response({'message': 'done'}, status.HTTP_200_OK)

    return Response({'message': 'You are not authorized.'}, status.HTTP_403_FORBIDDEN)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def managers(request):
    if request.user.groups.filter(name='Manager').exists():
        if request.method == 'POST':
            username = request.data['username']
            if username:
                user = get_object_or_404(User, username=username)
                managers = Group.objects.get('Manager')
                managers.user_set.add(user)
                return Response({'message': 'done'}, status.HTTP_201_CREATED)

        if request.method == 'GET':
            users = User.objects.filter(groups__name='Manager')
            serialized_users = UserSerializer(users, many=True)
            return Response(serialized_users.data, status.HTTP_200_OK)

        return Response({'message': 'error'}, status.HTTP_400_BAD_REQUEST)

    return Response({'message': 'You are not authorized.'}, status.HTTP_403_FORBIDDEN)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def manager(request, user_id):
    if request.user.groups.filter(name='Manager').exists():
        user = get_object_or_404(User, id=user_id)
        managers = Group.objects.get('Manager')
        managers.user_set.remove(user)
        return Response({'message': 'done'}, status.HTTP_200_OK)

    return Response({'message': 'You are not authorized.'}, status.HTTP_403_FORBIDDEN)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def delivery_crew(request):
    if request.user.groups.filter(name='Manager').exists():
        if request.method == 'POST':
            username = request.data['username']
            if username:
                user = get_object_or_404(User, username=username)
                delivery_crew = Group.objects.get('Delivery crew')
                delivery_crew.user_set.add(user)
                return Response({'message': 'done'}, status.HTTP_201_CREATED)

        if request.method == 'GET':
            users = User.objects.filter(groups__name='Delivery crew')
            serialized_users = UserSerializer(users, many=True)
            return Response(serialized_users.data, status.HTTP_200_OK)

        return Response({'message': 'error'}, status.HTTP_400_BAD_REQUEST)

    return Response({'message': 'You are not authorized.'}, status.HTTP_403_FORBIDDEN)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def delivery(request, user_id):
    if request.user.groups.filter(name='Manager').exists():
        user = get_object_or_404(User, id=user_id)
        delivery_crew = Group.objects.get('Delivery crew')
        delivery_crew.user_set.remove(user)
        return Response({'message': 'done'}, status.HTTP_200_OK)

    return Response({'message': 'You are not authorized.'}, status.HTTP_403_FORBIDDEN)

@api_view(['GET', 'POST', 'DELETE'])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def cart(request):
    user = request.user
    if request.method == 'GET':
        cart = Cart.objects.filter(user__username=user.username)
        serialized_cart = CartSerializer(cart, many=True)
        return Response(serialized_cart.data, status.HTTP_200_OK)
    if request.method == 'POST':
        serialized_cart = CartSerializer(data=request.data, context={'request': request})

        if serialized_cart.is_valid(raise_exception=True):
            serialized_cart.save()
        return Response(serialized_cart.data, status.HTTP_201_CREATED)
    if request.method == 'DELETE':
        Cart.objects.filter(user_id=request.user.id).delete()
        return Response({'message': 'done'}, status.HTTP_200_OK)

@api_view(['GET', 'POST'])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def orders(request):
    if request.method == 'GET':
        if request.user.groups.filter(name='Manager').exists():
            orders = Order.objects.all()
        elif request.user.groups.filter(name='Delivery crew').exists():
            orders = Order.objects.filter(delivery_crew_id=request.user.id)
        else:
            orders = Order.objects.filter(user_id=request.user.id)

        status_param = request.query_params.get('status')
        total_param = request.query_params.get('total')
        ordering = request.query_params.get('ordering')
        perpage = request.query_params.get('perpage', default=3)
        page = request.query_params.get('page', default=1)

        if int(perpage) > 5:
            perpage = 5

        if status_param:
            orders = orders.filter(status=status_param)
        if total_param:
            orders = orders.filter(total__lte=total_param)
        if ordering:
            ordering_fields = ordering.split(',')
            orders = orders.order_by(*ordering_fields)

        paginator = Paginator(orders, per_page=perpage)
        try:
            orders = paginator.page(number=page)
        except EmptyPage:
            orders = []

        serialized_orders = OrderSerializer(orders, many=True)
        return Response(serialized_orders.data, status.HTTP_200_OK)

    if request.method == 'POST':
        user = request.user
        cart = Cart.objects.filter(user_id=user.id)

        total = 0
        for item in cart:
            item = model_to_dict(item)
            total += item.get('price')

        serialized_order = OrderSerializer(data={'total': total}, context={'request': request})
        if serialized_order.is_valid(raise_exception=True):
            order = serialized_order.save()

        order = model_to_dict(order)

        for item in cart:
            item_dic = model_to_dict(item)
            serialized_orderitem = OrderItemSerializer(
                data={
                    'order': order.get('id'),
                    'menuitem': item_dic.get('menuitem'),
                    'quantity': item_dic.get('quantity'),
                    'unit_price': item_dic.get('unit_price'),
                    'price': item_dic.get('price'),
                }
            )
            if serialized_orderitem.is_valid(raise_exception=True):
                serialized_orderitem.save()
                item.delete()

        return Response({'message': 'done'}, status.HTTP_200_OK)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def order(request, order_id):
    if request.method == 'GET':
        orderitems = OrderItem.objects.filter(order_id=order_id, order_id__user_id=request.user.id)

        if not orderitems:
            return Response({'message': 'You are not authorized.'}, status.HTTP_403_FORBIDDEN)

        serialized_orderitems = OrderItemSerializer(orderitems, many=True)
        return Response(serialized_orderitems.data, status.HTTP_200_OK)

    if request.method == 'PUT' or request.method == 'PATCH':
        order = get_object_or_404(Order, id=order_id)
        order_dic = model_to_dict(order)

        if request.user.groups.filter('Manager').exists():
            order_status = get_value_from_user(request, order_dic, 'status')
            delivery_crew = get_value_from_user(request, order_dic, 'delivery_crew')

            Order.objects.filter(id=order_id).update(status=order_status, delivery_crew=delivery_crew)

            return Response({'message': 'updated'}, status.HTTP_200_OK)

        if request.user.groups.filter('Delivery crew').exists():
            try:
                order_status = request.data.get('status')
            except KeyError:
                return Response({'message': 'Bad request.'}, status.HTTP_400_BAD_REQUEST)

            Order.objects.filter(id=order_id).update(status=order_status)

            return Response({'message': 'done'}, status.HTTP_200_OK)

    if request.user.groups.filter('Manager').exists():
        if request.method == 'DELETE':
            order = get_object_or_404(Order, id=order_id)
            order.delete()
            return Response({'message': 'done'}, status.HTTP_200_OK)

@api_view(['GET', 'POST'])
@throttle_classes([UserRateThrottle])
def item_of_the_day(request):
    if request.user.groups.filter(name='Manager').exists():
        if request.method == 'GET':
            item = MenuItem.objects.get(featured=True)
            serialized_item = MenuItemSerializer(item)

            return Response(serialized_item.data, status.HTTP_200_OK)

        if request.method == 'POST':
            menuitem_title = request.data.get('menuitem_title')
            MenuItem.objects.filter(featured=True).update(featured=False)
            MenuItem.objects.filter(title=menuitem_title).update(featured=True)

            return Response({'message': 'done'}, status.HTTP_200_OK)

    return Response({'message': 'You are not authorized.'}, status.HTTP_403_FORBIDDEN)