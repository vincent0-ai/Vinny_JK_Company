from rest_framework import generics
from .models import Services, Product, Order, Booking, Cart, CartItem, Payment
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models.functions import TruncDay, TruncMonth,TruncWeek
from rest_framework import status
from django.db.models import Sum, Count
from datetime import timedelta, datetime
from django.utils import timezone
from .serializers import (
    ServicesSerializer,
    ProductSerializer,
    OrderSerializer,
    OrderSerializer,
    BookingSerializer,
    CartSerializer,
    CartItemSerializer
)
from django.db import transaction
from django.shortcuts import get_object_or_404
from .utils import MpesaClient, create_stripe_payment_intent
import json

class ServicesListCreateView(generics.ListCreateAPIView):
    queryset = Services.objects.all()
    serializer_class = ServicesSerializer


class ServicesDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Services.objects.all()
    serializer_class = ServicesSerializer

class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class OrderCreateView(generics.CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


class OrderListView(generics.ListAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


class OrderDetailView(generics.RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

class BookingCreateView(generics.CreateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer


class BookingListView(generics.ListAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer


class BookingDetailView(generics.RetrieveAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

#calculating total price for order

@api_view(['POST'])
def create_order(request):
    try:
        product_id = request.data.get('product')
        quantity = int(request.data.get('quantity', 1))

        with transaction.atomic():
            product = Product.objects.select_for_update().get(id=product_id)

            try:
                product.reduce_stock(quantity)
            except ValueError as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            total_price = product.price * quantity

            order = Order.objects.create(
                product=product,
                quantity=quantity,
                total_price=total_price,
                auto_part=request.data.get('auto_part'),
                vehicle_model=request.data.get('vehicle_model'),
                vehicle_make=request.data.get('vehicle_make'),
                vehicle_year=request.data.get('vehicle_year'),
                full_name=request.data.get('full_name'),
                phone_number=request.data.get('phone_number'),
                estate=request.data.get('estate'),
                street_address=request.data.get('street_address')
            )

        return Response({
            "message": "Order created successfully",
            "order_id": order.id,
            "remaining_stock": product.stock_quantity,
            "total_price": total_price
        }, status=status.HTTP_201_CREATED)

    except Product.DoesNotExist:
        return Response(
            {"error": "Product not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )

    #calculating total price for booking

@api_view(['POST'])
def create_booking(request):
    try:
        services_id = request.data.get('services')
        services = Services.objects.get(id=services_id)
        
        booking_date_str = request.data.get('booking_date')
        booking_time_str = request.data.get('booking_time')
        
        # Validate date and time
        if not booking_date_str or not booking_time_str:
             return Response(
                {"error": "Date and Time are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking_date = datetime.strptime(booking_date_str, "%Y-%m-%d").date()
        booking_time = datetime.strptime(booking_time_str, "%H:%M").time()

        # Logic for avoid booking in the past
        if booking_date < timezone.now().date():
            return Response(
                {"error": "Booking date cannot be in the past"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Logic for avoid booking twice
        existing_booking = Booking.objects.filter(
            services=services,
            booking_date=booking_date,
            booking_time=booking_time,
            status__in=['pending', 'confirmed']
        ).exists()

        if existing_booking:
            return Response(
                {"error": "This time slot is already booked."},
                status=status.HTTP_400_BAD_REQUEST
            )

        total_price = services.price

        booking = Booking.objects.create(
            services=services,
            total_price=total_price,
            booking_date=booking_date,
            booking_time=booking_time,
            full_name=request.data.get('full_name'),
            phone_number=request.data.get('phone_number'),
            vehicle_model=request.data.get('vehicle_model'),
            number_plate=request.data.get('number_plate'),
            additional_notes=request.data.get('additional_notes')
        )

        return Response({
            "message": "Booking created successfully",
            "booking_id": booking.id,
            "total_price": total_price
        }, status=status.HTTP_201_CREATED)

    except Services.DoesNotExist:
        return Response(
            {"error": "Services not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
                
   

#cancel order and restore stock
CANCELLATION_LIMIT_HOURS = 2
@api_view(['POST'])
def cancel_order(request, order_id):
    try:
        with transaction.atomic():
            order = Order.objects.select_for_update().get(id=order_id)

            if order.is_cancelled:
                return Response(
                    {"message": "Order already cancelled"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            product = order.product
            product.restore_stock(order.quantity)

            order.is_cancelled = True
            order.is_pending = False
            order.is_completed = False
            order.is_restored = True
            order.save()

        return Response({
            "message": "Order cancelled and stock restored",
            "restored_quantity": order.quantity,
            "current_stock": product.stock_quantity
        }, status=status.HTTP_200_OK)

    except Order.DoesNotExist:
        return Response(
            {"error": "Order not found"},
            status=status.HTTP_404_NOT_FOUND
        )

 # logic for booking cancellation
@api_view(['POST'])

def cancel_booking(request, booking_id):
    try:
        with transaction.atomic():
            booking = Booking.objects.select_for_update().get(id=booking_id)

            if booking.is_cancelled:
                return Response(
                    {"message": "Booking already cancelled"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if booking.is_completed:
                return Response(
                    {"message": "Completed bookings cannot be cancelled"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            booking_datetime = datetime.combine(
                booking.booking_date,
                booking.booking_time
            )

            booking_datetime = timezone.make_aware(booking_datetime)

            now = timezone.now()
            time_difference = booking_datetime - now

            if time_difference < timedelta(hours=CANCELLATION_LIMIT_HOURS):
                return Response(
                    {
                        "error": "Cancellation not allowed. Less than 2 hours to booking time."
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            if booking.status not in ['pending', 'confirmed']:
                return Response(
                    {"error": "Only pending or confirmed bookings can be cancelled"},
                    status=status.HTTP_400_BAD_REQUEST
                )    

            booking.is_cancelled = True
            booking.is_pending = False
            booking.is_confirmed = False
            booking.save()

        return Response({
            "message": "Booking cancelled successfully",
            "booking_id": booking.id
        }, status=status.HTTP_200_OK)

    except Booking.DoesNotExist:
        return Response(
            {"error": "Booking not found"},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
def confirm_booking(request, booking_id):
    booking = Booking.objects.get(id=booking_id)

    if booking.status != 'pending':
        return Response(
            {"error": "Only pending bookings can be confirmed"},
            status=status.HTTP_400_BAD_REQUEST
        )

    booking.status = 'confirmed'
    booking.save()

    return Response({"message": "Booking confirmed"})


@api_view(['POST'])
def complete_booking(request, booking_id):
    booking = Booking.objects.get(id=booking_id)

    if booking.status != 'confirmed':
        return Response(
            {"error": "Only confirmed bookings can be completed"},
            status=status.HTTP_400_BAD_REQUEST
        )

    booking.status = 'completed'
    booking.save()

    return Response({"message": "Booking completed"})


@api_view(['GET'])
def bookings_summary(request):
    total = Booking.objects.count()
    pending = Booking.objects.filter(status='pending').count()
    confirmed = Booking.objects.filter(status='confirmed').count()
    completed = Booking.objects.filter(status='completed').count()
    cancelled = Booking.objects.filter(status='cancelled').count()

    return Response({
        "total_bookings": total,
        "pending": pending,
        "confirmed": confirmed,
        "completed": completed,
        "cancelled": cancelled
    })

@api_view(['GET'])
def booking_revenue(request):
    revenue = Booking.objects.filter(
        status='completed'
    ).aggregate(
        total_revenue=Sum('total_price')
    )

    return Response({
        "completed_booking_revenue": revenue['total_revenue'] or 0
    })

@api_view(['GET'])
def daily_bookings(request):
    daily = Booking.objects.annotate(
        day=TruncDay('created_at')
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')

    return Response(daily)

@api_view(['GET'])
def monthly_bookings(request):
    monthly = Booking.objects.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')

    return Response(monthly)

@api_view(['GET'])
def weekly_bookings(request):
    weekly = Booking.objects.annotate(
        week=TruncWeek('created_at')
    ).values('week').annotate(
        count=Count('id')
    ).order_by('week')

    return Response(weekly)

AVAILABLE_TIME_SLOTS = [
    "09:00",
    "10:00",
    "11:00",
    "12:00",
    "14:00",
    "15:00",
    "16:00",
    "17:00",
    "18:00",
    "19:00",
    "20:00",
    "21:00",
    "22:00",
    "23:00",
]
#get available slots

@api_view(['GET'])
def get_available_slots(request):
    service_id = request.GET.get('service_id')
    booking_date = request.GET.get('booking_date')

    service = Services.objects.get(id=service_id)

    booked_slots = Booking.objects.filter(
        services=service,
        booking_date=booking_date,
        status__in=['pending', 'confirmed']
    ).values_list('booking_time', flat=True)

    booked_slots = [time.strftime("%H:%M") for time in booked_slots]

    available_slots = [
        slot for slot in AVAILABLE_TIME_SLOTS
        if slot not in booked_slots
    ]

    return Response({
        "date": booking_date,
        "available_slots": available_slots
    })

    return Response({
        "date": booking_date,
        "available_slots": available_slots
    })

# Cart Views

class CartCreateView(generics.CreateAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

class CartDetailView(generics.RetrieveAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    lookup_field = 'id'

@api_view(['POST'])
def add_to_cart(request, cart_id):
    cart = get_object_or_404(Cart, id=cart_id)
    product_id = request.data.get('product_id')
    quantity = int(request.data.get('quantity', 1))

    product = get_object_or_404(Product, id=product_id)

    # Check stock
    if not product.has_stock(quantity):
         return Response({"error": "Not enough stock"}, status=status.HTTP_400_BAD_REQUEST)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )

    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    serializer = CartItemSerializer(cart_item)
    return Response(serializer.data, status=status.HTTP_201_CREATED) 

class UpdateCartItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    lookup_field = 'pk' 

    def perform_update(self, serializer):
        # Optional: check stock on update if quantity increases
        instance = serializer.instance
        quantity = serializer.validated_data.get('quantity')
        
        if quantity is not None and quantity > instance.quantity:
            added_quantity = quantity - instance.quantity
            if not instance.product.has_stock(added_quantity):
                raise serializers.ValidationError("Not enough stock")
        
        serializer.save()

# Payment Views
@api_view(['POST'])
def initiate_mpesa_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    phone_number = request.data.get('phone_number')
    if not phone_number:
        return Response({"error": "Phone number is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Convert phone number to format 254...
    if phone_number.startswith('0'):
        phone_number = '254' + phone_number[1:]
    
    mpesa_client = MpesaClient()
    response = mpesa_client.stk_push(
        phone_number=phone_number,
        amount=order.total_price,
        account_reference=str(order.id),
        transaction_desc=f"Payment for Order {order.id}"
    )

    if response and response.get('ResponseCode') == '0':
        checkout_request_id = response.get('CheckoutRequestID')
        Payment.objects.create(
            order=order,
            transaction_id=checkout_request_id, # Store checkout ID initially
            payment_method='M-Pesa',
            amount=order.total_price,
            status='Pending'
        )
        return Response({
            "message": "STK Push initiated",
            "checkout_request_id": checkout_request_id
        })
    else:
        return Response({"error": "Failed to initiate STK Push", "details": response}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def mpesa_callback(request):
    try:
        data = request.data
        body = data.get('Body', {}).get('stkCallback', {})
        result_code = body.get('ResultCode')
        checkout_request_id = body.get('CheckoutRequestID')
        
        # Log the callback data for debugging
        print(f"M-Pesa Callback Data: {json.dumps(data)}")

        payment = Payment.objects.filter(transaction_id=checkout_request_id).first()
        if not payment:
            return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

        if result_code == 0:
            payment.status = 'Completed'
            payment.save()
            
            order = payment.order
            order.is_paid = True
            order.save()

            # Find actual receipt number if needed
            # metadata = body.get('CallbackMetadata', {}).get('Item', [])
            # for item in metadata:
            #     if item.get('Name') == 'MpesaReceiptNumber':
            #         payment.transaction_id = item.get('Value') # Update to real receipt?
            #         payment.save()
            
            return Response({"message": "Payment successful"})
        else:
            payment.status = 'Failed'
            payment.save()
            return Response({"message": "Payment failed"})

    except Exception as e:
        print(f"M-Pesa Callback Error: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def initiate_stripe_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    intent = create_stripe_payment_intent(
        amount=order.total_price,
        currency='kes' 
    )

    if intent:
         Payment.objects.create(
            order=order,
            transaction_id=intent['id'],
            payment_method='Stripe',
            amount=order.total_price,
            status='Pending'
        )
         return Response({
             'client_secret': intent['client_secret'],
             'payment_intent_id': intent['id']
         })
    
    return Response({"error": "Failed to create payment intent"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
