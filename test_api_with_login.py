#!/usr/bin/env python
import requests
import json

def test_order_status_api_with_login():
    """Test API endpoint cập nhật trạng thái đơn hàng với đăng nhập"""
    
    # Tạo session
    session = requests.Session()
    
    # URL đăng nhập
    login_url = "http://127.0.0.1:8000/accounts/login/"
    
    # Dữ liệu đăng nhập (thay bằng thông tin admin thực tế)
    login_data = {
        'phone_number': '0825280204',  # Thay bằng số điện thoại admin
        'password': '123456',  # Thay bằng mật khẩu admin
    }
    
    print("Đăng nhập admin...")
    
    try:
        # Lấy trang đăng nhập để có CSRF token
        login_page = session.get(login_url)
        print(f"Login page status: {login_page.status_code}")
        
        # Tìm CSRF token trong HTML
        import re
        csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', login_page.text)
        if csrf_match:
            csrf_token = csrf_match.group(1)
            print(f"Found CSRF token: {csrf_token[:20]}...")
            
            # Thêm CSRF token vào data đăng nhập
            login_data['csrfmiddlewaretoken'] = csrf_token
            
            # Đăng nhập
            login_response = session.post(login_url, data=login_data)
            print(f"Login response status: {login_response.status_code}")
            
            if login_response.status_code == 200:
                print("Đăng nhập thành công!")
                
                # Test API cập nhật trạng thái
                api_url = "http://127.0.0.1:8000/admin/orders/update-status/"
                api_data = {
                    'order_number': 'ORD-5191E698',
                    'status': 'delivered',
                    'note': 'Test cập nhật trạng thái'
                }
                
                print(f"Testing API endpoint: {api_url}")
                print(f"Data: {api_data}")
                
                # Gửi POST request với session đã đăng nhập
                api_response = session.post(api_url, data=api_data)
                
                print(f"API Response status: {api_response.status_code}")
                print(f"API Response text: {api_response.text}")
                
                if api_response.status_code == 200:
                    try:
                        json_data = api_response.json()
                        print(f"JSON response: {json_data}")
                    except json.JSONDecodeError:
                        print("Response không phải JSON")
                else:
                    print(f"API Error: HTTP {api_response.status_code}")
            else:
                print("Đăng nhập thất bại!")
                print(f"Response: {login_response.text}")
        else:
            print("Không tìm thấy CSRF token!")
            
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")

if __name__ == "__main__":
    test_order_status_api_with_login() 