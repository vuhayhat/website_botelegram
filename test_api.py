#!/usr/bin/env python
import requests
import json

def test_order_status_api():
    """Test API endpoint cập nhật trạng thái đơn hàng"""
    
    # URL của API endpoint
    url = "http://127.0.0.1:8000/admin/orders/update-status/"
    
    # Dữ liệu test
    data = {
        'order_number': 'ORD-5191E698',
        'status': 'delivered',
        'note': 'Test cập nhật trạng thái'
    }
    
    print(f"Testing API endpoint: {url}")
    print(f"Data: {data}")
    
    try:
        # Gửi POST request
        response = requests.post(url, data=data)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response text: {response.text}")
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                print(f"JSON response: {json_data}")
            except json.JSONDecodeError:
                print("Response không phải JSON")
        else:
            print(f"Error: HTTP {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")

if __name__ == "__main__":
    test_order_status_api() 