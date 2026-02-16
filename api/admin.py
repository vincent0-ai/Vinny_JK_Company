from django.contrib import admin
from .models import Services, Product, Order, Booking, Category

admin.site.register(Services)
admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(Booking)

