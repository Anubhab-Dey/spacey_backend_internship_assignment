from django.shortcuts import render
from django.db.models import Sum, Count, F
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, filters, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from drf_spectacular.types import OpenApiTypes

from .models import Product, Customer, Bill, BillItem
from .serializers import ProductSerializer, CustomerSerializer, BillSerializer

# List and Create Products
class ProductListCreate(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id', 'name', 'price', 'description']

# Retrieve, Update, and Delete a Product
class ProductDetailUpdateDelete(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

# List and Create Customers
class CustomerListCreate(generics.ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

# Retrieve, Update, and Delete a Customer
class CustomerDetailUpdateDelete(generics.RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

# List and Create Bills
class BillListCreate(generics.ListCreateAPIView):
    queryset = Bill.objects.all()
    serializer_class = BillSerializer

# Retrieve, Update, and Delete a Bill
class BillDetailUpdateDelete(generics.RetrieveUpdateDestroyAPIView):
    queryset = Bill.objects.all()
    serializer_class = BillSerializer

# Analytics View:
@extend_schema(
    parameters=[
        OpenApiParameter("type", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Type of analytics to retrieve ('customer', 'cashier', or 'product')."),
        OpenApiParameter("identifier", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Identifier for the analytics type (e.g., email for 'customer' or 'cashier', product name or ID for 'product').")
    ],
    responses={
        200: inline_serializer(
            name='UnifiedAnalyticsResponse',
            fields={
                'products_bought': serializers.ListField(
                    child=inline_serializer(
                        name='ProductBought',
                        fields={
                            'product__name': serializers.CharField(),
                            'total_quantity': serializers.IntegerField(),
                            'frequency': serializers.IntegerField()
                        }
                    ),
                    required=False
                ),
                'frequented_timings': serializers.ListField(
                    child=inline_serializer(
                        name='FrequentedTiming',
                        fields={
                            'hour': serializers.IntegerField(),
                            'frequency': serializers.IntegerField()
                        }
                    ),
                    required=False
                ),
                'cashiers': serializers.ListField(
                    child=inline_serializer(
                        name='CashierInfo',
                        fields={
                            'created_by__email': serializers.EmailField(),
                            'instances': serializers.IntegerField()
                        }
                    ),
                    required=False
                ),
                'products_sold': serializers.ListField(
                    child=inline_serializer(
                        name='ProductSold',
                        fields={
                            'product__name': serializers.CharField(),
                            'total_quantity': serializers.IntegerField()
                        }
                    ),
                    required=False
                ),
                'customers': serializers.ListField(
                    child=inline_serializer(
                        name='CustomerInfo',
                        fields={
                            'customer__email': serializers.EmailField(),
                            'instances': serializers.IntegerField()
                        }
                    ),
                    required=False
                )
            }
        ),
        400: inline_serializer(
            name='ErrorResponse',
            fields={
                'error': serializers.CharField()
            }
        )
    },
    description="Provides analytics based on the given type and identifier, including products bought, frequented timings, and cashier interactions."
)
class UnifiedAnalyticsView(APIView):
    def get(self, request):
        analytics_type = request.query_params.get('type')
        identifier = request.query_params.get('identifier')

        if analytics_type == 'customer':
            return self.customer_analytics(identifier)
        elif analytics_type == 'cashier':
            return self.cashier_analytics(identifier)
        elif analytics_type == 'product':
            return self.product_analytics(identifier)
        else:
            return Response({'error': 'Invalid analytics type'}, status=400)

    def customer_analytics(self, customer_email):
        if not customer_email:
            return Response({'error': 'Customer email is required for customer analytics'}, status=400)
        
        products_bought = BillItem.objects.filter(bill__customer__email=customer_email)\
            .values('product__name')\
            .annotate(total_quantity=Sum('quantity'), frequency=Count('product_id'))\
            .order_by('-total_quantity', '-frequency')

        frequented_timings = Bill.objects.filter(customer__email=customer_email)\
            .annotate(hour=F('created_at__hour'))\
            .values('hour')\
            .annotate(frequency=Count('id'))\
            .order_by('-frequency')

        cashiers = Bill.objects.filter(customer__email=customer_email)\
            .values('created_by__email')\
            .annotate(instances=Count('id'))\
            .order_by('-instances')

        return Response({
            'products_bought': list(products_bought),
            'frequented_timings': list(frequented_timings),
            'cashiers': list(cashiers)
        })

    def cashier_analytics(self, cashier_email):
        if not cashier_email:
            return Response({'error': 'Cashier email is required for cashier analytics'}, status=400)
        
        products_sold = BillItem.objects.filter(bill__created_by__email=cashier_email)\
            .values('product__name')\
            .annotate(total_quantity=Sum('quantity'))\
            .order_by('-total_quantity')

        customers = Bill.objects.filter(created_by__email=cashier_email)\
            .values('customer__email')\
            .annotate(instances=Count('id'))\
            .order_by('-instances')

        return Response({
            'products_sold': list(products_sold),
            'customers': list(customers)
        })

    def product_analytics(self, product_identifier):
        if not product_identifier:
            return Response({'error': 'Product identifier is required for product analytics'}, status=400)
        
        filter_args = {'product__name': product_identifier} if product_identifier.isalpha() else {'product__id': product_identifier}

        customers = BillItem.objects.filter(**filter_args)\
            .values('bill__customer__email')\
            .annotate(total_quantity=Sum('quantity'))\
            .order_by('-total_quantity')

        cashiers = BillItem.objects.filter(**filter_args)\
            .values('bill__created_by__email')\
            .annotate(total_quantity=Sum('quantity'))\
            .order_by('-total_quantity')

        return Response({
            'customers': list(customers),
            'cashiers': list(cashiers)
        })