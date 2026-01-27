from rest_framework import generics
from .models import Services, Goods, Order, Booking
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import timedelta
from django.utils import timezone
from .serializers import (
    ServicesSerializer,
    GoodsSerializer,
    OrderSerializer,
    BookingSerializer
)

class ServicesListCreateView(generics.ListCreateAPIView):
    queryset = Services.objects.all()
    serializer_class = ServicesSerializer


class ServicesDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Services.objects.all()
    serializer_class = ServicesSerializer

class GoodsListCreateView(generics.ListCreateAPIView):
    queryset = Goods.objects.all()
    serializer_class = GoodsSerializer


class GoodsDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Goods.objects.all()
    serializer_class = GoodsSerializer

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
        goods_id = request.data.get('goods')
        quantity = int(request.data.get('quantity', 1))

        goods = Goods.objects.get(id=goods_id)

        total_price = goods.price * quantity

        order = Order.objects.create(
            goods=goods,
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
            "total_price": total_price
        }, status=status.HTTP_201_CREATED)

    except Goods.DoesNotExist:
        return Response(
            {"error": "Goods not found"},
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

        total_price = services.price

        booking = Booking.objects.create(
            services=services,
            total_price=total_price,
            booking_date=request.data.get('booking_date'),
            booking_time=request.data.get('booking_time'),
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
# stock reduction logic
@api_view(['POST'])
def create_order(request):
    try:
        goods_id = request.data.get('goods')
        quantity = int(request.data.get('quantity', 1))

        with transaction.atomic():  
            goods = Goods.objects.select_for_update().get(id=goods_id)

            
            if goods.stock_quantity < quantity:
                return Response(
                    {"error": "Not enough stock available"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            
            total_price = goods.price * quantity

            
            order = Order.objects.create(
                goods=goods,
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

            
            goods.stock_quantity -= quantity

            
            if goods.stock_quantity == 0:
                goods.is_available = False

            goods.save()

        return Response({
            "message": "Order created successfully",
            "order_id": order.id,
            "remaining_stock": goods.stock_quantity,
            "total_price": total_price
        }, status=status.HTTP_201_CREATED)

    except Goods.DoesNotExist:
        return Response(
            {"error": "Goods not found"},
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

            goods = order.goods

            goods.stock_quantity += order.quantity
            goods.is_available = True
            goods.save()

            order.is_cancelled = True
            order.is_pending = False
            order.is_completed = False
            order.is_restored = True
            order.save()

        return Response({
            "message": "Order cancelled and stock restored",
            "restored_quantity": order.quantity,
            "current_stock": goods.stock_quantity
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