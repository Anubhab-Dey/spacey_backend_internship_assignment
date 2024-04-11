from django.db import models
from django.conf import settings

class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField()
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Customer(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField(default="")
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, default="")

    def __str__(self):
        return self.name

class Bill(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name='bills')
    customer_name = models.CharField(max_length=255, blank=True)
    customer_email = models.EmailField(blank=True)
    _old_email = None
    customer_address = models.TextField(blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __init__(self, *args, **kwargs):
        super(Customer, self).__init__(*args, **kwargs)
        self._old_email = self.email

    def save(self, *args, **kwargs):
        if self.pk is not None and self.email != self._old_email:
            self.update_related_bills(self._old_email, self.email)
        super(Customer, self).save(*args, **kwargs)
        self._old_email = self.email
        
    def __str__(self):
        return f'Bill {self.id} - {self.total_amount}'

class BillItem(models.Model):
    bill = models.ForeignKey(Bill, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.quantity} x {self.product.name}'

    def save(self, *args, **kwargs):
        if not self.pk:
            self.price = self.product.price * self.quantity
            super().save(*args, **kwargs)
            # Update product stock
            self.product.stock_quantity -= self.quantity
            self.product.save(update_fields=['stock_quantity'])
            super().save(*args, **kwargs)

        # Update bill total_amount
        if not self.pk:
            self.bill.total_amount += self.price
            self.bill.save()
