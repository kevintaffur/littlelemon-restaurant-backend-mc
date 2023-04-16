from rest_framework import serializers
from .models import Category, MenuItem, Cart, Order, OrderItem
from django.contrib.auth.models import User
from datetime import datetime

class UserSerializer(serializers.ModelSerializer):
    class Meta():
        model = User
        fields = ['id', 'username']

class CategorySerializer(serializers.ModelSerializer):
    class Meta():
        model = Category
        fields = ['slug', 'title',]

class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.CharField(write_only=True)

    class Meta():
        model = MenuItem
        fields = ['id',
                  'title',
                  'price',
                  'featured',
                  'category',
                  'category_id',
                  ]

class MenuItemForOrderSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta():
        model = MenuItem
        fields = ['id',
                  'title',
                  'category',
                  ]

class CartSerializer(serializers.ModelSerializer):
    menuitem = MenuItemSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    menuitem_id = serializers.IntegerField  (write_only=True)
    unit_price = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    price = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)

    class Meta():
        model = Cart
        fields = ['id',
                  'user',
                  'menuitem',
                  'quantity',
                  'unit_price',
                  'price',
                  'menuitem_id',
                  ]

    def create(self, validated_data):
        user = self.context['request'].user
        menuitem_id = validated_data.pop('menuitem_id')
        menuitem = MenuItem.objects.get(id=menuitem_id)
        unit_price = menuitem.price
        price = unit_price * validated_data['quantity']
        cart = Cart.objects.create(
            **validated_data,
            user = user,
            menuitem = menuitem,
            unit_price = unit_price,
            price = price,
        )
        return cart

class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    date = serializers.DateField(read_only=True)

    class Meta():
        model = Order
        fields = ['id',
                  'user',
                  'delivery_crew',
                  'status',
                  'total',
                  'date',
                  ]

    def create(self, validated_data):
        user = self.context['request'].user
        current_date = datetime.now()
        order = Order.objects.create(
            **validated_data,
            user=user,
            date=current_date,
        )
        return order

class OrderItemSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    menuitem = MenuItemForOrderSerializer(read_only=True)

    class Meta():
        model = OrderItem
        fields = ['order',
                  'menuitem',
                  'quantity',
                  'unit_price',
                  'price',
                  ]