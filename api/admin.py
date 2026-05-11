from django.contrib import admin
from .models import Services, Product, Order, Booking, Category, OrderItem, Gallery, ContactMessage, ProductImage, Offer, ServiceImage

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'total_price', 'created_at', 'is_paid', 'is_delivered')
    inlines = [OrderItemInline]

class GalleryAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'created_at')
    list_filter = ('category',)
    search_fields = ('title', 'category')

admin.site.register(Gallery, GalleryAdmin)
class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 0

class ServicesAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'created_at')
    inlines = [ServiceImageInline]
    search_fields = ('name',)

admin.site.register(Services, ServicesAdmin)
admin.site.register(Category)
admin.site.register(ProductImage)
admin.site.register(Order, OrderAdmin)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'services', 'booking_date', 'booking_time', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'booking_date', 'services')
    search_fields = ('full_name', 'phone_number', 'vehicle_model', 'number_plate')

admin.site.register(Booking, BookingAdmin)

class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'subject', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')

admin.site.register(ContactMessage, ContactMessageAdmin)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock_quantity', 'is_available', 'is_active')
    inlines = [ProductImageInline]
    list_filter = ('is_available', 'is_active', 'category')
    search_fields = ('name', 'description')

admin.site.register(Product, ProductAdmin)

class OfferAdmin(admin.ModelAdmin):
    list_display = ('name', 'discount_percentage', 'start_date', 'end_date', 'is_active')
    filter_horizontal = ('products',)
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('name',)

admin.site.register(Offer, OfferAdmin)
