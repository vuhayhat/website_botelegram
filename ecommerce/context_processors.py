from store.models import Cart

def cart_count(request):
    """
    Context processor để hiển thị số lượng sản phẩm trong giỏ hàng trên tất cả các trang
    """
    cart_count = 0
    if request.user.is_authenticated:
        # Nếu người dùng đã đăng nhập, lấy giỏ hàng của họ
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.item_count
        except Cart.DoesNotExist:
            pass
    elif 'cart_id' in request.session:
        # Nếu người dùng chưa đăng nhập nhưng có giỏ hàng trong session
        try:
            cart = Cart.objects.get(cart_id=request.session['cart_id'])
            cart_count = cart.item_count
        except Cart.DoesNotExist:
            pass
    
    return {'cart_count': cart_count} 