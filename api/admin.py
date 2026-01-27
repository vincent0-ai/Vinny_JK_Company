from django.contrib import admin
from .models import Services
from .models import Goods
from .models import Order
from .models import Booking

admin.site.register(Services)
admin.site.register(Goods)
admin.site.register(Order)
admin.site.register(Booking)

