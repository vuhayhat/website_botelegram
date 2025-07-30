#!/usr/bin/env python
import os
import sys
import django
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Order

def test_order_status_update():
    """Test cập nhật trạng thái đơn hàng"""
    
    # Lấy đơn hàng đầu tiên
    order = Order.objects.filter(is_ordered=True).first()
    if not order:
        print("Không có đơn hàng nào trong database")
        return
    
    print(f"Testing với đơn hàng: {order.order_number}")
    print(f"Trạng thái hiện tại: {order.status}")
    
    # Test cập nhật trạng thái
    old_status = order.status
    order.status = 'processing'
    order.save()
    
    print(f"Đã cập nhật trạng thái từ '{old_status}' thành '{order.status}'")
    
    # Kiểm tra lại
    order.refresh_from_db()
    print(f"Trạng thái sau khi cập nhật: {order.status}")

if __name__ == "__main__":
    test_order_status_update() 