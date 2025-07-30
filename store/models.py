from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.conf import settings
import uuid

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    display_order = models.IntegerField(default=0, help_text="Thứ tự hiển thị (0=off, 1=đầu tiên, 2=thứ hai, ...)")
    is_active = models.BooleanField(default=True, help_text="Hiển thị danh mục này?")
    
    class Meta:
        verbose_name_plural = 'categories'
        ordering = ('display_order', 'name',)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('category', args=[self.slug])
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0, help_text="Thứ tự hiển thị sản phẩm (số nhỏ hơn hiển thị trước)")
    is_featured = models.BooleanField(default=False, help_text="Đánh dấu sản phẩm nổi bật")
    
    # SEO Fields
    meta_title = models.CharField(max_length=200, blank=True, help_text="Tiêu đề SEO (để trống sẽ dùng tên sản phẩm)")
    meta_description = models.TextField(blank=True, help_text="Mô tả SEO (để trống sẽ dùng mô tả sản phẩm)")
    meta_keywords = models.CharField(max_length=255, blank=True, help_text="Từ khóa SEO (phân cách bằng dấu phẩy)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ('display_order', 'name',)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('product_detail', args=[self.slug])
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        
        # Nếu không có meta_title, sử dụng tên sản phẩm
        if not self.meta_title:
            self.meta_title = self.name
            
        # Nếu không có meta_description, sử dụng mô tả sản phẩm (rút gọn)
        if not self.meta_description and self.description:
            self.meta_description = self.description[:160] + '...' if len(self.description) > 160 else self.description
            
        super().save(*args, **kwargs)

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    is_main = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Image for {self.product.name} ({'Main' if self.is_main else 'Additional'})"

class Cart(models.Model):
    cart_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return str(self.cart_id)
    
    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())
    
    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    @property
    def subtotal(self):
        return self.product.price * self.quantity

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Đang xử lý'),
        ('processing', 'Đang chuẩn bị'),
        ('shipped', 'Đã gửi hàng'),
        ('delivered', 'Đã giao hàng'),
        ('cancelled', 'Đã hủy'),
    )
    
    order_number = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, blank=True)
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)
    order_note = models.TextField(blank=True)
    order_total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    ip = models.CharField(max_length=20, blank=True)
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.order_number
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        return f"ORD-{uuid.uuid4().hex[:8].upper()}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Lưu giá tại thời điểm đặt hàng
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    @property
    def subtotal(self):
        return self.price * self.quantity
