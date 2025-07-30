from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
import requests
import json
import uuid
from .models import Category, Product, Cart, CartItem, Order, OrderItem

# Create your views here.

class HomeView(ListView):
    model = Product
    template_name = 'store/home.html'
    context_object_name = 'products'
    paginate_by = 8
    
    def get_queryset(self):
        return Product.objects.filter(is_available=True).order_by('display_order', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True).exclude(display_order=0).order_by('display_order')
        context['featured_products'] = Product.objects.filter(is_featured=True, is_available=True).order_by('display_order')[:4]
        return context

class CategoryView(ListView):
    model = Product
    template_name = 'store/category.html'
    context_object_name = 'products'
    paginate_by = 8
    
    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return Product.objects.filter(category=self.category, is_available=True).order_by('display_order', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'store/product_detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context['related_products'] = Product.objects.filter(
            category=product.category, 
            is_available=True
        ).exclude(id=product.id).order_by('display_order', 'name')[:4]
        return context

# Hàm tiện ích để lấy hoặc tạo giỏ hàng
def _get_or_create_cart(request):
    cart_id = request.session.get('cart_id')
    if cart_id:
        try:
            cart = Cart.objects.get(cart_id=cart_id)
        except Cart.DoesNotExist:
            cart = _create_new_cart(request)
    else:
        cart = _create_new_cart(request)
    
    # Liên kết giỏ hàng với người dùng nếu đã đăng nhập
    if request.user.is_authenticated and not cart.user:
        cart.user = request.user
        cart.save()
    
    return cart

def _create_new_cart(request):
    cart = Cart.objects.create()
    request.session['cart_id'] = str(cart.cart_id)
    return cart

# Thêm sản phẩm vào giỏ hàng
class AddToCartView(View):
    def post(self, request, *args, **kwargs):
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        
        try:
            product = Product.objects.get(id=product_id, is_available=True)
        except Product.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Sản phẩm không tồn tại hoặc không khả dụng'}, status=404)
        
        # Kiểm tra số lượng tồn kho
        if product.stock < quantity:
            return JsonResponse({'status': 'error', 'message': 'Số lượng sản phẩm không đủ'}, status=400)
        
        cart = _get_or_create_cart(request)
        
        # Kiểm tra xem sản phẩm đã có trong giỏ hàng chưa
        try:
            cart_item = CartItem.objects.get(cart=cart, product=product)
            cart_item.quantity += quantity
            cart_item.save()
        except CartItem.DoesNotExist:
            cart_item = CartItem.objects.create(cart=cart, product=product, quantity=quantity)
        
        # Gửi thông báo Telegram khi thêm vào giỏ hàng
        self.send_telegram_cart_notification(request, product, quantity)
        
        return JsonResponse({
            'status': 'success',
            'message': f'Đã thêm {quantity} sản phẩm vào giỏ hàng',
            'cart_count': cart.item_count,
        })

    def send_telegram_cart_notification(self, request, product, quantity):
        from django.conf import settings
        import requests
        import datetime
        
        telegram_bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        telegram_chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', None)
        
        print(f"DEBUG: Telegram config - Token: {telegram_bot_token}, Chat ID: {telegram_chat_id}")
        
        if not telegram_bot_token or not telegram_chat_id:
            print("DEBUG: Missing Telegram configuration")
            return
        try:
            user = request.user if request.user.is_authenticated else None
            if user:
                user_info = user.get_full_name() if user.get_full_name() != user.phone_number else f"User {user.phone_number}"
            else:
                user_info = 'Khách vãng lai'
            now = datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            message = (
                f"🛒 *THÊM VÀO GIỎ HÀNG* 🛒\n\n"
                f"*Người dùng:* {user_info}\n"
                f"*Sản phẩm:* {product.name}\n"
                f"*Số lượng:* {quantity}\n"
                f"*Thời gian:* {now}"
            )
            url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
            payload = {
                'chat_id': telegram_chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            print(f"DEBUG: Sending Telegram message: {message}")
            response = requests.post(url, json=payload)
            print(f"DEBUG: Telegram response: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Telegram cart notification error: {e}")

# Xem giỏ hàng
class CartView(View):
    def get(self, request, *args, **kwargs):
        try:
            cart = _get_or_create_cart(request)
            cart_items = cart.items.all()
        except Exception:
            cart_items = []
            cart = None
        
        context = {
            'cart': cart,
            'cart_items': cart_items,
        }
        return render(request, 'store/cart.html', context)

# Cập nhật giỏ hàng
class UpdateCartView(View):
    def post(self, request, *args, **kwargs):
        cart_item_id = request.POST.get('cart_item_id')
        action = request.POST.get('action')
        
        try:
            cart = _get_or_create_cart(request)
            cart_item = CartItem.objects.get(id=cart_item_id, cart=cart)
        except CartItem.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Sản phẩm không tồn tại trong giỏ hàng'}, status=404)
        
        if action == 'increase':
            # Kiểm tra tồn kho
            if cart_item.quantity + 1 > cart_item.product.stock:
                return JsonResponse({'status': 'error', 'message': 'Số lượng sản phẩm không đủ'}, status=400)
            cart_item.quantity += 1
            cart_item.save()
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
        elif action == 'remove':
            cart_item.delete()
        
        # Tính lại tổng giỏ hàng
        cart_total = cart.total
        cart_count = cart.item_count
        
        return JsonResponse({
            'status': 'success',
            'cart_total': cart_total,
            'cart_count': cart_count,
            'item_subtotal': cart_item.subtotal if action != 'remove' else 0,
            'item_id': cart_item_id,
        })

# Trang thanh toán
class CheckoutView(View):
    def get(self, request, *args, **kwargs):
        try:
            cart = _get_or_create_cart(request)
            cart_items = cart.items.all()
            if not cart_items:
                messages.warning(request, 'Giỏ hàng của bạn đang trống')
                return redirect('cart')
        except Exception:
            messages.error(request, 'Đã xảy ra lỗi với giỏ hàng của bạn')
            return redirect('home')
        
        context = {
            'cart': cart,
            'cart_items': cart_items,
        }
        return render(request, 'store/checkout.html', context)
    
    def post(self, request, *args, **kwargs):
        try:
            cart = _get_or_create_cart(request)
            cart_items = cart.items.all()
            if not cart_items:
                messages.warning(request, 'Giỏ hàng của bạn đang trống')
                return redirect('cart')
        except Exception:
            messages.error(request, 'Đã xảy ra lỗi với giỏ hàng của bạn')
            return redirect('home')
        
        # Lấy thông tin từ form
        full_name = request.POST.get('full_name')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        country = request.POST.get('country')
        postal_code = request.POST.get('postal_code', '')
        order_note = request.POST.get('order_note', '')
        
        # Kiểm tra thông tin bắt buộc
        if not all([full_name, phone, address, city, country]):
            messages.error(request, 'Vui lòng điền đầy đủ thông tin bắt buộc')
            return redirect('checkout')
        
        # Tạo đơn hàng
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            full_name=full_name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            country=country,
            postal_code=postal_code,
            order_note=order_note,
            order_total=cart.total,
            ip=request.META.get('REMOTE_ADDR'),
            is_ordered=True,
        )
        
        # Tạo các mục đơn hàng
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
            )
            
            # Cập nhật số lượng tồn kho
            product = item.product
            product.stock -= item.quantity
            product.save()
        
        # Gửi thông báo qua Telegram
        print(f"DEBUG: About to send order notification for order {order.order_number}")
        self.send_telegram_notification(order)
        print(f"DEBUG: Order notification sent successfully")
        
        # Xóa giỏ hàng
        cart_items.delete()
        
        # Lưu thông tin đơn hàng vào session để hiển thị trang hoàn tất
        request.session['order_number'] = order.order_number
        
        return redirect('order_complete')
    
    def send_telegram_notification(self, order):
        # Kiểm tra cấu hình Telegram
        telegram_bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        telegram_chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', None)
        
        print(f"DEBUG: Order notification - Token: {telegram_bot_token}, Chat ID: {telegram_chat_id}")
        
        if not telegram_bot_token or not telegram_chat_id:
            print("DEBUG: Missing Telegram configuration for order notification")
            return
        
        try:
            # Tạo nội dung thông báo
            message = f"🛒 *ĐƠN HÀNG MỚI* 🛒\n\n"
            message += f"*Mã đơn hàng:* {order.order_number}\n"
            message += f"*Khách hàng:* {order.full_name}\n"
            message += f"*Điện thoại:* {order.phone}\n"
            message += f"*Địa chỉ:* {order.address}, {order.city}, {order.country}\n\n"
            
            # Thêm thông tin các sản phẩm
            message += "*Chi tiết đơn hàng:*\n"
            for item in order.items.all():
                message += f"- {item.quantity} x {item.product.name}: {item.subtotal:,.0f} VND\n"
            
            message += f"\n*Tổng tiền:* {order.order_total:,.0f} VND"
            
            # Gửi thông báo qua Telegram API
            url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
            payload = {
                'chat_id': telegram_chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            print(f"DEBUG: Sending order notification: {message}")
            response = requests.post(url, json=payload)
            print(f"DEBUG: Order notification response: {response.status_code} - {response.text}")
        except Exception as e:
            # Xử lý lỗi (có thể log lại)
            print(f"Telegram notification error: {e}")

# Trang hoàn tất đơn hàng
class OrderCompleteView(View):
    def get(self, request, *args, **kwargs):
        order_number = request.session.get('order_number')
        
        if order_number:
            try:
                order = Order.objects.get(order_number=order_number, is_ordered=True)
                order_items = order.items.all()
                
                context = {
                    'order': order,
                    'order_items': order_items,
                }
                
                # Xóa session sau khi hiển thị
                if 'order_number' in request.session:
                    del request.session['order_number']
                
                return render(request, 'store/order_complete.html', context)
            
            except Order.DoesNotExist:
                return redirect('home')
        else:
            return redirect('home')

# Trang lịch sử đơn hàng
class OrderHistoryView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Vui lòng đăng nhập để xem lịch sử đơn hàng')
            return redirect('login')
        
        orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
        
        context = {
            'orders': orders,
        }
        return render(request, 'store/order_history.html', context)

# Trang chi tiết đơn hàng
class OrderDetailView(View):
    def get(self, request, order_number, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Vui lòng đăng nhập để xem chi tiết đơn hàng')
            return redirect('login')
        
        try:
            order = Order.objects.get(order_number=order_number, user=request.user, is_ordered=True)
            order_items = order.items.all()
            
            context = {
                'order': order,
                'order_items': order_items,
            }
            
            return render(request, 'store/order_detail.html', context)
        
        except Order.DoesNotExist:
            messages.error(request, 'Không tìm thấy đơn hàng')
            return redirect('order_history')
