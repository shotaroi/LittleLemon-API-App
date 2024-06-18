from django.http import Http404
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User, Group

from rest_framework import generics, status
# from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

from .models import MenuItems, Category, Order, OrderItem, Cart
from .serializers import MenuItemsSerializer, CategorySerializer, SingleOrderSerializer, UserSerializer, OrderSerializer, CartSerializer
from .permissions import IsManager, IsDeliveryCrew
from datetime import date


# Create your views here.
class MenuItemsView(generics.ListCreateAPIView):    # Provides get and post method handlers.
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = MenuItems.objects.all()
    serializer_class = MenuItemsSerializer
    ordering_fields = ['price']
    filterset_fields = ['price']
    search_fields = ['title']

    def get_permissions(self):
        permission_classes = []

        if self.request.method == 'POST':
            permission_classes = [IsManager]

        return [permission() for permission in permission_classes]       

class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):    # Provides get, put, patch and delete method handlers.
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = MenuItems.objects.all()
    serializer_class = MenuItemsSerializer

    def get_permissions(self):
        permission_classes = []

        if self.request.method != 'GET':
            permission_classes = [IsManager]

        return [permission() for permission in permission_classes]

class CategoriesView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ManagersView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = User.objects.filter(groups__name='Manager')
    serializer_class = UserSerializer
    permission_classes = [IsManager]

    # Assign a users to the manager group
    def post(self, request):
        username = request.data['username']

        if username:
            user = get_object_or_404(User, username=username)
            managers = Group.objects.get(name='Manager')
            managers.user_set.add(user)

            return Response({"message": "The user is added to the Manager group"})
        
        return Response({"message": "error"}, status.HTTP_400_BAD_REQUEST)
    
# @api_view()
# @permission_classes([IsAuthenticated])
# def manager_view(request):
#     if request.user.groups.filter(name='Admin').exists():
#         users = User.objects.filter(groups__name='Manager')
#         serializer = UserSerializer(users, many=True)
#         return Response({'data': serializer.data})
#     else:
#         return Response({"message": "You are not authorized"}, 403)

class ManagersDeleteView(generics.DestroyAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes = [IsManager]
    queryset = User.objects.filter(groups__name='Manager')  

    def destroy(self):
        manager = self.get_object()
        self.perform_destroy(manager)

        return Response({"message": "The manager has been successfully deleted"}, status=200)

class DeliveryCrewsView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = User.objects.filter(groups__name='Delivery crew')
    serializer_class = UserSerializer
    permission_classes = [IsManager]

    # Assign a users to the delivery crews group
    def post(self, request):
        username = request.data['username']

        if username:
            user = get_object_or_404(User, username=username)
            deliveryCrew = Group.objects.get(name='Delivery crew')
            deliveryCrew.user_set.add(user)

            return Response({"message": "The user is added to the Delivery crew group"}, status=201)
        
        return Response({"message": "error"}, status.HTTP_400_BAD_REQUEST)

class DeliveryCrewDeleteView(generics.DestroyAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes = [IsManager]
    queryset = User.objects.filter(groups__name='Delivery crew')

    def destroy(self):
        deliveryCrew = self.get_object()
        self.perform_destroy(deliveryCrew)

        return Response({"message": "The Delivery crew has been successfully deleted"}, status=200)

class OrdersView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.groups.filter(name='Manager').exists():
            return Order.objects.all()
        elif self.request.user.groups.filter(name='Delivery crew').exists():
            return Order.objects.filter(delivery_crew=self.request.user)
        else:
            return Order.objects.filter(user=self.request.user)
        
    def post(self, request, *args, **kwargs):
        carts = Cart.objects.filter(user=self.request.user)

        if not carts:
            return Response({"message": "The cart is empty"}, 400)
        
        total = self.get_total()
        user = self.request.user
        dateToday = date.today()
        order = Order.objects.create(user=user, total=total, date=dateToday)

        for cart in carts.values():
            menuitem = get_object_or_404(MenuItems, id=cart['menuitem_id'])
            quantity = cart['quantity']
            unit_price = cart['unit_price']
            price = cart['price']
            OrderItem.objects.create(order=order, menuitem=menuitem, quantity=quantity, unit_price=unit_price, price=price).save()
        
        carts.delete()

        return Response({"message": "The order is successfully received"}, 200)

    def get_total(self):
        total = 0
        user = self.request.user
        menuitems = Cart.objects.filter(user=user)

        for menuitem in menuitems.values():
            total += menuitem['price']
        
        return total 

class SingleOrderView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = SingleOrderSerializer

    def get_permissions(self):
        order = Order.objects.get(pk=self.kwargs['pk'])
        if self.request.method == 'PUT' or self.request.method == 'DELETE':
            permission_classes = [IsManager]
        elif self.request.method == 'PATCH':
            permission_classes = [IsManager | IsDeliveryCrew]
        elif self.request.user == order.user and self.request.method == 'GET':
            permission_classes = [IsAuthenticated]
        elif self.request.user == order.delivery_crew and self.request.method == 'GET':
            permission_classes = [IsDeliveryCrew]
        else:
            permission_classes = [IsManager]

        return [permission() for permission in permission_classes]

    def get_queryset(self, *args, **kwargs):
        return OrderItem.objects.filter(order_id=self.kwargs['pk'])
    
    def patch(self, request, *args, **kwargs):
        order = Order.objects.get(pk=self.kwargs['pk'])
        order.status = not order.status
        order.save()

        return Response({'message': 'Order status has been changed'})
    
    def put(self, request, *args, **kwargs):
        username = self.request.data.get('username')
        user = get_object_or_404(User, username=username)
        order = Order.objects.get(pk=self.kwargs['pk'])
        order.delivery_crew = user
        order.save()

        return Response({'message': 'Delivery crew assigned to this order has been changed'})


    def delete(self, request, *args, **kwargs):
        order = Order.objects.get(pk=self.kwargs['pk'])
        orderID = str(order.id)
        order.delete()

        return Response({'message':'Order with ID {} was successfully deleted'.format(orderID)}, 200)
    
class TestView(generics.ListAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = SingleOrderSerializer
    queryset = OrderItem.objects.filter(order_id=8)


class CartView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        items = Cart.objects.filter(user=self.request.user)

        return items
    
    def post(self, request):
        user = get_object_or_404(User, username=request.data['username'])
        menuitem_id = request.data['menuitem_id']
        menuitem = get_object_or_404(MenuItems, id=menuitem_id)
        quantity = request.data['quantity']
        unit_price = menuitem.price
        price = unit_price * int(quantity)

        try:
            Cart.objects.create(user=user, menuitem_id=menuitem_id, quantity=quantity, unit_price=unit_price, price=price)
        except Exception as e:
            return Response({"error_message": str(e)}, status.HTTP_400_BAD_REQUEST)
        
        return Response({"message": "Menu item is added to the cart."}, status=201)
    
    def delete(self, request):
        if Cart.objects.exists():
            try: 
                cart = Cart.objects.all().filter(user=self.request.user)
                cart.delete()
            except Exception as e:
                return Response({"error_message": str(e)}, status=400)
            
            return Response({"message": "Cart items have been successfully deleted"}, status=200)
        else:
            return Response({"message": "The cart is empty"}, status=400)      
  
