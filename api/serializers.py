
from rest_framework import serializers
from .models import Services, Product, Order, Booking, Category, Cart, CartItem, OrderItem, Gallery, ContactMessage, ProductImage, ServiceImage


class GallerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Gallery
        fields = '__all__'


class ServicesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Services
        fields = '__all__'

class ProductImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'price', 'description', 'car_models', 'uploaded_at']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'





class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    discounted_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'image', 'discounted_price', 'discount_percentage', 'category', 'images', 'created_at', 'updated_at', 'is_available', 'stock_quantity', 'is_active']

    def get_discount_percentage(self, obj):
        offer = obj.current_offer
        if offer:
            return offer.discount_percentage
        return None

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_id', 'quantity', 'price_at_order']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    class Meta:
        model = Order
        fields = [
            'id', 'items', 'total_price', 'created_at', 'updated_at', 'auto_part',
            'vehicle_model', 'vehicle_make', 'vehicle_year', 'full_name',
            'phone_number', 'estate', 'street_address', 'is_delivered',
            'is_paid', 'is_cancelled', 'is_completed', 'is_pending',
            'is_out_for_delivery', 'is_restored', 'is_failed', 'payment_method',
            'is_confirmed', 'description'
        ]
        read_only_fields = ['total_price']


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source='product', write_only=True
    )
    sub_total = serializers.DecimalField(
        max_digits=10, decimal_places=2, source='total_price', read_only=True
    )

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'sub_total']

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    grand_total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'grand_total', 'created_at']

    def get_grand_total(self, obj):
        return sum(item.total_price for item in obj.items.all())

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = '__all__'


class ServiceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceImage
        fields = ['id', 'image', 'image_type', 'service_type', 'price', 'description', 'uploaded_at']

class ServicesSerializer(serializers.ModelSerializer):
    images = ServiceImageSerializer(many=True, read_only=True)

    class Meta:
        model = Services
        fields = ['id', 'name', 'description', 'price', 'images', 'created_at', 'updated_at']


