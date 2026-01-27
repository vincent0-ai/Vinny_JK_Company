
from django.db import models
from django.utils import timezone

class Services(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='services/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Goods(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='goods/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_available = models.BooleanField(default=True)
    stock_quantity = models.IntegerField(default=0)


class Order(models.Model):
    goods = models.ForeignKey('Goods', on_delete=models.CASCADE)
    quantity = models.IntegerField(blank=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    auto_part = models.CharField(max_length=255, blank=True, null=True)
    vehicle_model = models.CharField(max_length=240, blank=True, null=True)
    vehicle_make = models.CharField(max_length=20, blank=True, null=True)
    vehicle_year = models.CharField(max_length=20, blank=True, null=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    estate = models.CharField(max_length=20, blank=True, null=True)
    street_address = models.CharField(max_length=255, blank=True, null=True)
    is_delivered = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    is_pending = models.BooleanField(default=True)
    is_out_for_delivery = models.BooleanField(default=False)
    is_restored = models.BooleanField(default=False)
    
    

class Booking(models.Model):
    services = models.ForeignKey('Services', on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    booking_date = models.DateField(blank=True, null=True)
    booking_time = models.TimeField(blank=True, null=True)   
    full_name = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    vehicle_model = models.CharField(max_length=240, blank=True, null=True)
    number_plate = models.CharField(max_length=20, blank=True, null=True)
    additional_notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_confirmed = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    is_pending = models.BooleanField(default=True)
    is_out_for_service = models.BooleanField(default=False)



    def __str__(self):
        return self.name


