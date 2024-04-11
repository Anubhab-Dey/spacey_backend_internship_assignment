from django.db import transaction
from rest_framework import serializers

from .models import Product, Customer, Bill, BillItem

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class BillItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillItem
        fields = ['id', 'bill', 'product', 'quantity', 'price']

class BillSerializer(serializers.ModelSerializer):
    items = BillItemSerializer(many=True)
    temp_customer_name = serializers.CharField(write_only=True, required=False)
    temp_customer_email = serializers.EmailField(write_only=True, required=False)
    temp_customer_address = serializers.CharField(write_only=True, required=False)
    temp_customer_phone = serializers.CharField(write_only=True, required=False)
    update_customer_consent = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = Bill
        fields = ['id', 'customer', 'customer_name', 'customer_email', 'customer_address', 'customer_phone', 'created_by', 'created_at', 'total_amount', 'items', 'temp_customer_name', 'temp_customer_email', 'temp_customer_address', 'temp_customer_phone', 'update_customer_consent']
        read_only_fields = ('created_by', 'total_amount',)

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        temp_customer_details = {k: validated_data.pop(k, None) for k in ['temp_customer_name', 'temp_customer_email', 'temp_customer_address', 'temp_customer_phone']}
        update_customer_consent = validated_data.pop('update_customer_consent', False)

        with transaction.atomic():
            validated_data['created_by'] = self.context['request'].user
            email = temp_customer_details.get('temp_customer_email')

            # Handle customer creation or update
            if email:
                customer, created = Customer.objects.get_or_create(email=email, defaults=temp_customer_details)
                if not created and update_customer_consent:
                    # If consent is given, update the existing customer's details
                    for key, value in temp_customer_details.items():
                        if value:  # Avoid overwriting with None
                            setattr(customer, key, value)
                    customer.save()
                validated_data['customer'] = customer
                # Update bill with customer snapshot data
                validated_data['customer_name'] = customer.name
                validated_data['customer_email'] = customer.email
                validated_data['customer_address'] = customer.address
                validated_data['customer_phone'] = customer.phone

            bill = Bill.objects.create(**validated_data)
            for item_data in items_data:
                BillItem.objects.create(bill=bill, **item_data)

        return bill