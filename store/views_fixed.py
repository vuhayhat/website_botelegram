# Fixed UpdateCartView
class UpdateCartView(View):
    def post(self, request, *args, **kwargs):
        cart_item_id = request.POST.get('cart_item_id')
        action = request.POST.get('action')
        
        try:
            cart = _get_or_create_cart(request)
            cart_item = CartItem.objects.get(id=cart_item_id, cart=cart)
        except CartItem.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Sản phẩm không tồn tại trong giỏ hàng'}, status=404)
        
        # Store values before potential deletion
        item_subtotal = 0
        item_quantity = 0
        
        if action == 'increase':
            # Kiểm tra tồn kho
            if cart_item.quantity + 1 > cart_item.product.stock:
                return JsonResponse({'status': 'error', 'message': 'Số lượng sản phẩm không đủ'}, status=400)
            cart_item.quantity += 1
            cart_item.save()
            item_subtotal = cart_item.subtotal
            item_quantity = cart_item.quantity
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
                item_subtotal = cart_item.subtotal
                item_quantity = cart_item.quantity
            else:
                cart_item.delete()
                item_subtotal = 0
                item_quantity = 0
        elif action == 'remove':
            cart_item.delete()
            item_subtotal = 0
            item_quantity = 0
        
        # Tính lại tổng giỏ hàng
        cart_total = cart.total
        cart_count = cart.item_count
        
        return JsonResponse({
            'status': 'success',
            'cart_total': cart_total,
            'cart_count': cart_count,
            'item_subtotal': item_subtotal,
            'item_quantity': item_quantity,
            'item_id': cart_item_id,
        })