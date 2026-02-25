from rest_framework import generics
from .models import Services, Product, Order, Booking, Cart, CartItem, Payment, OrderItem, Gallery
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
    OrderItemSerializer,
    BookingSerializer,
    CartSerializer,
    CartItemSerializer,
    GallerySerializer
)
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .utils import MpesaClient, create_stripe_payment_intent, send_receipt_email
import json
import logging

logger = logging.getLogger(__name__)

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

class GalleryListCreateView(generics.ListCreateAPIView):
    queryset = Gallery.objects.all()
    serializer_class = GallerySerializer

class GalleryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Gallery.objects.all()
    serializer_class = GallerySerializer

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
        items_data = request.data.get('items', [])
        if not items_data:
            return Response({"error": "No items provided"}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            total_order_price = 0
            order_items_to_create = []
            
            for item in items_data:
                product_id = item.get('product_id')
                quantity = int(item.get('quantity', 1))

                product = Product.objects.select_for_update().get(id=product_id)
                if not product.has_stock(quantity):
                    raise ValueError(f"Not enough stock for {product.name}")

                # Note: Stock deduction moved to mpesa_callback / successful payment handler
                
                price_at_order = product.price
                total_order_price += price_at_order * quantity
                
                order_items_to_create.append({
                    'product': product,
                    'quantity': quantity,
                    'price_at_order': price_at_order
                })

            order = Order.objects.create(
                total_price=total_order_price,
                auto_part=request.data.get('auto_part'),
                vehicle_model=request.data.get('vehicle_model'),
                vehicle_make=request.data.get('vehicle_make'),
                vehicle_year=request.data.get('vehicle_year'),
                full_name=request.data.get('full_name'),
                email=request.data.get('email'),
                phone_number=request.data.get('phone_number'),
                estate=request.data.get('estate'),
                street_address=request.data.get('street_address')
            )

            payment_method = request.data.get('payment_method', 'M-Pesa')
            
            for item_data in order_items_to_create:
                OrderItem.objects.create(
                    order=order,
                    product=item_data['product'],
                    quantity=item_data['quantity'],
                    price_at_order=item_data['price_at_order']
                )
                
                # If it's Payment on Delivery, deduct stock immediately 
                # because there won't be an automated M-Pesa webhook to do it later.
                if payment_method == 'Delivery':
                    item_data['product'].reduce_stock(item_data['quantity'])

        # Send Email Receipt ONLY if Delivery. M-Pesa receipts are sent in the callback webhook.
        try:
            if order.email and payment_method == 'Delivery':
                subject = f"Order #{order.id} Confirmation (Payment on Delivery)"
                email_body = f"Hello {order.full_name},<br><br>We have received your order <b>#{order.id}</b> for a total of <b>KES {total_order_price}</b>. Since you selected Payment on Delivery, payment will be collected upon arrival at your location.<br><br>Thank you for shopping with Vinny KJ!"
                send_receipt_email(order.email, subject, email_body)
        except Exception as e:
            logger.error(f"Failed to send Email Receipt for Delivery order {order.id}: {e}")

        return Response({
            "message": "Order created successfully",
            "order_id": order.id,
            "total_price": float(total_order_price)
        }, status=status.HTTP_201_CREATED)

    except Product.DoesNotExist:
        return Response({"error": "One or more products not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
            email=request.data.get('email'),
            phone_number=request.data.get('phone_number'),
            vehicle_model=request.data.get('vehicle_model'),
            number_plate=request.data.get('number_plate'),
            additional_notes=request.data.get('additional_notes')
        )

        # Send Email Receipt (wrapped to prevent booking failure on Email error)
        try:
            if booking.email:
                subject = f"Booking Confirmation: {services.name}"
                email_body = f"Hello {booking.full_name},<br><br>Your booking for <b>{services.name}</b> on <b>{booking.booking_date}</b> at <b>{booking.booking_time}</b> has been received.<br><br>Thank you for choosing Vinny KJ Auto Services!"
                send_receipt_email(booking.email, subject, email_body)
        except Exception as e:
            logger.error(f"Failed to send Email Receipt for booking {booking.id}: {e}")

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
                return Response({"message": "Order already cancelled"}, status=status.HTTP_400_BAD_REQUEST)

            for item in order.items.all():
                item.product.restore_stock(item.quantity)

            order.is_cancelled = True
            order.is_pending = False
            order.is_completed = False
            order.is_restored = True
            order.save()

        return Response({
            "message": "Order cancelled and stock restored",
            "order_id": order.id
        }, status=status.HTTP_200_OK)

    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

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
# Payment Views
@api_view(['POST'])
def initiate_mpesa_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    phone_number = request.data.get('phone_number')
    
    if not phone_number:
        return Response({"error": "Phone number is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Convert phone number to Safaricom Daraja format: 2547XXXXXXXX or 2541XXXXXXXX
    phone_number = str(phone_number).strip().replace('+', '').replace(' ', '')
    if phone_number.startswith('0'):
        phone_number = '254' + phone_number[1:]
    elif len(phone_number) == 9 and (phone_number.startswith('7') or phone_number.startswith('1')):
        phone_number = '254' + phone_number
    elif not phone_number.startswith('254') or len(phone_number) != 12:
        return Response({"error": "Invalid phone number format. Use 07XXXXXXXX, 01XXXXXXXX, or 2547XXXXXXXX"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            # Check if there's already a pending payment for this order to avoid duplicates
            existing_pending_payment = Payment.objects.filter(order=order, status='Pending', payment_method='M-Pesa').first()
            
            mpesa_client = MpesaClient()
            response = mpesa_client.stk_push(
                phone_number=phone_number,
                amount=order.total_price,
                account_reference=f"ORD{order.id}",
                transaction_desc=f"Payment for Order {order.id}"
            )

            if response and response.get('ResponseCode') == '0':
                checkout_request_id = response.get('CheckoutRequestID')
                
                # If we have an existing pending payment, we update it or keep it as is. 
                # Better to create a new one to track separate attempts, or update if we want to keep it simple.
                # Production usually creates a new record for each attempt.
                Payment.objects.create(
                    order=order,
                    transaction_id=checkout_request_id,
                    payment_method='M-Pesa',
                    amount=order.total_price,
                    phone_number=phone_number,
                    status='Pending'
                )
                
                return Response({
                    "message": "STK Push initiated successfully",
                    "checkout_request_id": checkout_request_id,
                    "customer_message": response.get('CustomerMessage')
                })
            else:
                error_msg = response.get('errorMessage', 'Failed to initiate STK Push') if response else 'No response from Daraja'
                return Response({"error": error_msg, "details": response}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Unexpected error in initiate_mpesa_payment: {e}")
        return Response({"error": f"Internal Server Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
def mpesa_callback(request):
    """
    M-Pesa STK Push Callback Handler
    """
    try:
        data = request.data
        logger.info(f"M-Pesa Callback Received: {json.dumps(data)}")
        
        stk_callback = data.get('Body', {}).get('stkCallback', {})
        result_code = stk_callback.get('ResultCode')
        result_desc = stk_callback.get('ResultDesc')
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        
        payment = Payment.objects.filter(transaction_id=checkout_request_id).first()
        if not payment:
            logger.error(f"Payment with CheckoutRequestID {checkout_request_id} not found")
            return Response({"message": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

        # Save raw data for auditing
        payment.raw_callback_data = data
        
        if result_code == 0:
            logger.info(f"Payment successful: CheckoutID={checkout_request_id}, Ref={payment.order.id}")
            payment.status = 'Completed'
            
            # Extract Metadata
            items = stk_callback.get('CallbackMetadata', {}).get('Item', [])
            for item in items:
                name = item.get('Name')
                value = item.get('Value')
                if name == 'MpesaReceiptNumber':
                    receipt_number = value
                    print(f"M-Pesa Receipt Number: {receipt_number}")
                    payment.mpesa_receipt_number = receipt_number
                elif name == 'Amount':
                    # Optional: verify amount matches
                    pass
            
            payment.save()
            
            # Update order status and deduct stock
            order = payment.order
            
            # Deduct stock ONLY when genuinely paid
            if not order.is_paid:
                for order_item in order.items.all():
                    if order_item.product.has_stock(order_item.quantity):
                        order_item.product.reduce_stock(order_item.quantity)
                    else:
                        logger.warning(f"Stock shortage for product {order_item.product.name} during late M-Pesa payment.")

            order.is_paid = True
            order.is_pending = False
            order.save()
            
            # Send Email Receipt upon successful M-Pesa Payment
            try:
                if order.email:
                    subject = f"Payment Received: Order #{order.id}"
                    email_body = f"Hello {order.full_name},<br><br>We have successfully received your M-Pesa payment of <b>KES {payment.amount}</b> (Receipt: {payment.mpesa_receipt_number}) for Order <b>#{order.id}</b>.<br><br>Your order is now processing. Thank you for shopping with Vinny KJ!"
                    send_receipt_email(order.email, subject, email_body)
            except Exception as e:
                logger.error(f"Failed to send Email Receipt for M-Pesa Order {order.id}: {e}")

            return Response({"ResultCode": 0, "ResultDesc": "Success"})
        else:
            logger.warning(f"Payment failed: CheckoutID={checkout_request_id}, Code={result_code}, Desc={result_desc}")
            payment.status = 'Failed'
            payment.save()
            return Response({"ResultCode": 0, "ResultDesc": "Failure acknowledged"})

    except Exception as e:
        logger.error(f"CRITICAL: M-Pesa Callback Processing Error: {str(e)}")
        return Response({"ResultCode": 1, "ResultDesc": "Internal Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
