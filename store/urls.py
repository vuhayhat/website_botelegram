from django.urls import path
from . import views
from .views import AddToCartView, CartView, UpdateCartView, CheckoutView, OrderCompleteView, OrderHistoryView, OrderDetailView

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('category/<slug:slug>/', views.CategoryView.as_view(), name='category'),
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    
    # Cart URLs
    path('cart/add/', AddToCartView.as_view(), name='add_to_cart'),
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/update/', UpdateCartView.as_view(), name='update_cart'),
    
    # Checkout URLs
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('order-complete/', OrderCompleteView.as_view(), name='order_complete'),
    
    # Order History URLs
    path('order/', OrderHistoryView.as_view(), name='order_history'),
    path('order/<str:order_number>/', OrderDetailView.as_view(), name='order_detail'),
] 