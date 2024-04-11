from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.ProductListCreate.as_view(), name='product-list-create'),
    path('products/<int:pk>/', views.ProductDetailUpdateDelete.as_view(), name='product-detail-update-delete'),
    path('customers/', views.CustomerListCreate.as_view(), name='customer-list-create'),
    path('customers/<int:pk>/', views.CustomerDetailUpdateDelete.as_view(), name='customer-detail-update-delete'),
    path('bills/', views.BillListCreate.as_view(), name='bill-list-create'),
    path('analytics/', views.UnifiedAnalyticsView.as_view(), name='unified-analytics'),
]
