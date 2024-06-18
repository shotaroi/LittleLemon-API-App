from django.urls import path
from . import views
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('menu-items/', views.MenuItemsView.as_view(), name='menuitems-view-create'),
    path('menu-items/<int:pk>', views.SingleMenuItemView.as_view()),
    path('categories', views.CategoriesView.as_view()),
    path('groups/manager/users/', views.ManagersView.as_view()),
    path('groups/manager/users/<int:pk>', views.ManagersDeleteView.as_view()),
    path('groups/delivery-crew/users/', views.DeliveryCrewsView.as_view()),
    path('groups/delivery-crew/users/<int:pk>', views.DeliveryCrewDeleteView.as_view()),
    path('api-token-auth/', obtain_auth_token),
    path('cart/menu-items/', views.CartView.as_view()),
    path('orders/<int:pk>', views.SingleOrderView.as_view()),
    path('orders/', views.OrdersView.as_view()),
    path('orders/test/', views.TestView.as_view()),
]