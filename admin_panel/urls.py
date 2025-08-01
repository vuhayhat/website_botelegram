from django.urls import path
from . import views

urlpatterns = [
    path('', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    
    # Category URLs
    path('categories/', views.CategoryListView.as_view(), name='admin_categories'),
    path('categories/add/', views.CategoryCreateView.as_view(), name='admin_category_add'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='admin_category_edit'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='admin_category_delete'),
    
    # Product URLs
    path('products/', views.ProductListView.as_view(), name='admin_products'),
    path('products/add/', views.ProductCreateView.as_view(), name='admin_product_add'),
    path('products/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='admin_product_edit'),
    path('products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='admin_product_delete'),
    
    # Display Settings URL
    path('display-settings/', views.DisplaySettingsView.as_view(), name='admin_display_settings'),
    
    # Orders URLs
    path('orders/', views.OrderListView.as_view(), name='admin_orders'),
    path('orders/update-status/', views.update_order_status, name='admin_update_order_status'),
    path('orders/<str:order_number>/', views.OrderDetailView.as_view(), name='admin_order_detail'),
    path('orders/<str:order_number>/detail/', views.order_detail_ajax, name='admin_order_detail_ajax'),
] 