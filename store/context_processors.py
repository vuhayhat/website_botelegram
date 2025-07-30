from store.models import Category, Cart

def categories(request):
    """
    Context processor để cung cấp danh mục cho tất cả các trang
    """
    return {
        'categories': Category.objects.filter(is_active=True).exclude(display_order=0).order_by('display_order')
    }

def cart_count(request):
    """
    Context processor để cung cấp số lượng sản phẩm trong giỏ hàng
    """
    cart_count = 0
    if request.session.get('cart_id'):
        try:
            cart = Cart.objects.get(cart_id=request.session['cart_id'])
            cart_count = cart.item_count
        except Cart.DoesNotExist:
            pass
    return {
        'cart_count': cart_count
    } 