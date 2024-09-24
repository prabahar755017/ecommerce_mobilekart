from django.urls import path
from . import views
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView

urlpatterns=[
             path('', views.home, name='home'),
             path('register/',views.register,name="register"),
             path('login/',views.login_page,name="login"),
             path('logout',views.logout_page,name="logout"),
             path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
             path('catagory/create/', views.create_catagory, name='create_catagory'),
             path('catagory/', views.list_catagory, name='list_catagory'),
             path('catagory/update/<int:id>/', views.update_catagory, name='update_catagory'),
             path('catagory/delete/<int:id>/', views.delete_catagory, name='delete_catagory'),
             path('product/create/', views.create_product, name='create_product'),
             path('product/', views.list_products, name='list_products'),
             path('product/update/<int:id>/', views.update_product, name='update_product'),
             path('product/delete/<int:id>/', views.delete_product, name='delete_product'),
             path('collections',views.collections,name="collections"),
             path('collections/<str:name>',views.collections_view,name="collections_view"),
             path('collections/<str:category>/<str:product>/', views.product_details, name='product_details'),
             path('products/', views.product_list, name='product_list'),
             path('users/', views.users_list, name='users_list'),
             path('cart/',views.cart_page,name="cart"),
             path('remove_cart/<str:cid>',views.remove_cart,name="remove_cart"),
             path('addtocart/<int:product_id>/', views.add_to_cart, name='add_to_cart'), 
             path('cart/update/<int:item_id>/',views.update_cart, name='update_cart'),
             path('orders/<int:pk>/', views.order_detail, name='order_detail'),
             path('orders/create/<int:category_id>/<int:product_id>/', views.create_order, name='create_order'),
             path('order/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
             path('order/user/', views.order_list_user, name='order_list_user'),
             path('admin/cart/', views.admin_cart_list, name='admin_cart_list'),
             path('admin/orders/', views.admin_order_list, name='admin_order'),
             path('admin/orders/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
             path('payment/<int:order_id>/', views.payment, name='payment'),
             path('payment-success/', views.payment_success, name='payment_success'),
             path('admin/payments/', views.admin_payment_list, name='payment_list'),
             path('payments/<int:pk>/', views.payment_detail, name='payment_detail'),
             path('profile/',  views.profile_view, name='profile'),
             path('add-address/',  views.add_address, name='add_address'),
             path('edit-address/<int:address_id>/',views.edit_address, name='edit_address'),  
             path('delete-address/<int:address_id>/', views.delete_address, name='delete_address'),
]
