from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, View, DetailView
from django.urls import reverse_lazy
from store.models import Category, Product, ProductImage, Order
from .models import AdminActivity
from django.db.models import Q, Max, Min, F
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

class AdminDashboardView(AdminRequiredMixin, ListView):
    model = AdminActivity
    template_name = 'admin_panel/dashboard.html'
    context_object_name = 'activities'
    paginate_by = 10
    ordering = ['-timestamp']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from store.models import Order
        context['total_products'] = Product.objects.count()
        context['total_categories'] = Category.objects.count()
        context['total_orders'] = Order.objects.filter(is_ordered=True).count()
        context['recent_products'] = Product.objects.order_by('-created_at')[:5]
        context['recent_orders'] = Order.objects.filter(is_ordered=True).order_by('-created_at')[:5]
        return context

# Category Views
class CategoryListView(AdminRequiredMixin, ListView):
    model = Category
    template_name = 'admin_panel/category_list.html'
    context_object_name = 'categories'
    paginate_by = 10

class CategoryCreateView(AdminRequiredMixin, CreateView):
    model = Category
    template_name = 'admin_panel/category_form.html'
    fields = ['name', 'description', 'image', 'display_order', 'is_active']
    success_url = reverse_lazy('admin_categories')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Tìm số thứ tự hiển thị nhỏ nhất chưa được sử dụng (lớn hơn 0)
        used_orders = list(Category.objects.filter(display_order__gt=0).values_list('display_order', flat=True))
        
        # Nếu không có danh mục nào có display_order > 0
        if not used_orders:
            next_order = 1
        else:
            # Tìm số nhỏ nhất chưa được sử dụng
            next_order = 1
            while next_order in used_orders:
                next_order += 1
        
        # Đặt giá trị mặc định cho trường display_order
        form.initial['display_order'] = next_order
        return form
    
    def form_valid(self, form):
        # Kiểm tra xem display_order đã tồn tại chưa (nếu > 0)
        display_order = form.cleaned_data.get('display_order')
        
        # Nếu display_order > 0 (hiển thị) và đã tồn tại
        if display_order > 0 and Category.objects.filter(display_order=display_order).exists():
            # Sử dụng transaction để đảm bảo tính nhất quán của dữ liệu
            with transaction.atomic():
                # Dịch chuyển tất cả các danh mục có display_order >= display_order lên 1
                Category.objects.filter(display_order__gte=display_order).update(
                    display_order=F('display_order') + 1
                )
                
                # Lưu danh mục mới với display_order đã chọn
                messages.info(self.request, f'Đã chèn danh mục vào vị trí {display_order} và dịch chuyển các danh mục khác.')
        
        response = super().form_valid(form)
        # Log activity
        AdminActivity.objects.create(
            admin=self.request.user,
            action='create',
            model_name='Category',
            object_id=self.object.id,
            description=f'Created category: {self.object.name}'
        )
        messages.success(self.request, f'Danh mục "{self.object.name}" đã được tạo thành công.')
        return response

class CategoryUpdateView(AdminRequiredMixin, UpdateView):
    model = Category
    template_name = 'admin_panel/category_form.html'
    fields = ['name', 'description', 'image', 'display_order', 'is_active']
    success_url = reverse_lazy('admin_categories')
    
    def form_valid(self, form):
        # Kiểm tra xem display_order đã tồn tại chưa (nếu > 0)
        display_order = form.cleaned_data.get('display_order')
        original_category = self.get_object()
        
        # Chỉ kiểm tra nếu display_order > 0 và khác với giá trị hiện tại
        if display_order > 0 and display_order != original_category.display_order:
            if Category.objects.filter(display_order=display_order).exists():
                # Sử dụng transaction để đảm bảo tính nhất quán của dữ liệu
                with transaction.atomic():
                    # Nếu thứ tự mới nhỏ hơn thứ tự cũ, dịch chuyển các mục ở giữa lên 1
                    if display_order < original_category.display_order:
                        Category.objects.filter(
                            display_order__gte=display_order,
                            display_order__lt=original_category.display_order
                        ).update(display_order=F('display_order') + 1)
                    
                    # Nếu thứ tự mới lớn hơn thứ tự cũ, dịch chuyển các mục ở giữa xuống 1
                    elif display_order > original_category.display_order:
                        Category.objects.filter(
                            display_order__gt=original_category.display_order,
                            display_order__lte=display_order
                        ).update(display_order=F('display_order') - 1)
                    
                    messages.info(self.request, f'Đã chèn danh mục vào vị trí {display_order} và điều chỉnh các danh mục khác.')
        
        response = super().form_valid(form)
        # Log activity
        AdminActivity.objects.create(
            admin=self.request.user,
            action='update',
            model_name='Category',
            object_id=self.object.id,
            description=f'Updated category: {self.object.name}'
        )
        messages.success(self.request, f'Danh mục "{self.object.name}" đã được cập nhật thành công.')
        return response

class CategoryDeleteView(AdminRequiredMixin, DeleteView):
    model = Category
    template_name = 'admin_panel/category_confirm_delete.html'
    success_url = reverse_lazy('admin_categories')
    
    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        AdminActivity.objects.create(
            admin=self.request.user,
            action='DELETE',
            model_name='Category',
            object_id=category.id,
            description=f"Deleted category: {category.name}"
        )
        messages.success(request, 'Category deleted successfully.')
        return super().delete(request, *args, **kwargs)

# Product Views
class ProductListView(AdminRequiredMixin, ListView):
    model = Product
    template_name = 'admin_panel/product_list.html'
    context_object_name = 'products'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )
        
        # Filter by featured products
        featured = self.request.GET.get('featured')
        if featured:
            queryset = queryset.filter(is_featured=True)
        
        # Filter by available products
        available = self.request.GET.get('available')
        if available:
            queryset = queryset.filter(is_available=True)
        
        # Sorting
        sort_by = self.request.GET.get('sort', 'display_order')
        if sort_by:
            if sort_by.startswith('-'):
                # Descending order
                queryset = queryset.order_by(sort_by, 'name')
            else:
                # Ascending order
                queryset = queryset.order_by(sort_by, 'name')
        
        return queryset

class ProductCreateView(AdminRequiredMixin, CreateView):
    model = Product
    template_name = 'admin_panel/product_form.html'
    fields = ['category', 'name', 'description', 'price', 'stock', 'is_available', 'display_order', 'is_featured']
    success_url = reverse_lazy('admin_products')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Tìm số thứ tự hiển thị nhỏ nhất chưa được sử dụng (lớn hơn 0)
        used_orders = list(Product.objects.filter(display_order__gt=0).values_list('display_order', flat=True))
        
        # Nếu không có sản phẩm nào có display_order > 0
        if not used_orders:
            next_order = 1
        else:
            # Tìm số nhỏ nhất chưa được sử dụng
            next_order = 1
            while next_order in used_orders:
                next_order += 1
        
        # Đặt giá trị mặc định cho trường display_order
        form.initial['display_order'] = next_order
        return form
    
    def form_valid(self, form):
        # Kiểm tra xem display_order đã tồn tại chưa (nếu > 0)
        display_order = form.cleaned_data.get('display_order')
        
        # Nếu display_order > 0 (hiển thị) và đã tồn tại
        if display_order > 0 and Product.objects.filter(display_order=display_order).exists():
            # Sử dụng transaction để đảm bảo tính nhất quán của dữ liệu
            with transaction.atomic():
                # Dịch chuyển tất cả các sản phẩm có display_order >= display_order lên 1
                Product.objects.filter(display_order__gte=display_order).update(
                    display_order=F('display_order') + 1
                )
                
                # Lưu sản phẩm mới với display_order đã chọn
                messages.info(self.request, f'Đã chèn sản phẩm vào vị trí {display_order} và dịch chuyển các sản phẩm khác.')
        
        response = super().form_valid(form)
        product = self.object
        
        # Handle main image
        main_image = self.request.FILES.get('main_image')
        if main_image:
            # Create main image
            ProductImage.objects.create(
                product=product,
                image=main_image,
                is_main=True
            )
        
        # Handle additional images
        additional_images = self.request.FILES.getlist('additional_images')
        for image in additional_images:
            ProductImage.objects.create(
                product=product,
                image=image,
                is_main=False
            )
        
        # Log activity
        AdminActivity.objects.create(
            admin=self.request.user,
            action='CREATE',
            model_name='Product',
            object_id=self.object.id,
            description=f"Created product: {self.object.name}"
        )
        messages.success(self.request, 'Product created successfully.')
        return response

class ProductUpdateView(AdminRequiredMixin, UpdateView):
    model = Product
    template_name = 'admin_panel/product_form.html'
    fields = ['category', 'name', 'description', 'price', 'stock', 'is_available', 'display_order', 'is_featured']
    success_url = reverse_lazy('admin_products')
    
    def form_valid(self, form):
        # Kiểm tra xem display_order đã tồn tại chưa (nếu > 0)
        display_order = form.cleaned_data.get('display_order')
        original_product = self.get_object()
        
        # Chỉ kiểm tra nếu display_order > 0 và khác với giá trị hiện tại
        if display_order > 0 and display_order != original_product.display_order:
            if Product.objects.filter(display_order=display_order).exists():
                # Sử dụng transaction để đảm bảo tính nhất quán của dữ liệu
                with transaction.atomic():
                    # Nếu thứ tự mới nhỏ hơn thứ tự cũ, dịch chuyển các mục ở giữa lên 1
                    if display_order < original_product.display_order:
                        Product.objects.filter(
                            display_order__gte=display_order,
                            display_order__lt=original_product.display_order
                        ).update(display_order=F('display_order') + 1)
                    
                    # Nếu thứ tự mới lớn hơn thứ tự cũ, dịch chuyển các mục ở giữa xuống 1
                    elif display_order > original_product.display_order:
                        Product.objects.filter(
                            display_order__gt=original_product.display_order,
                            display_order__lte=display_order
                        ).update(display_order=F('display_order') - 1)
                    
                    messages.info(self.request, f'Đã chèn sản phẩm vào vị trí {display_order} và điều chỉnh các sản phẩm khác.')
        
        response = super().form_valid(form)
        product = self.object
        
        # Handle deleted images
        deleted_images = self.request.POST.get('deleted_images', '')
        if deleted_images:
            image_ids = [int(id) for id in deleted_images.split(',') if id.isdigit()]
            ProductImage.objects.filter(id__in=image_ids).delete()
        
        # Check if main image was deleted
        deleted_main_image = self.request.POST.get('deleted_main_image', 'false') == 'true'
        
        # Handle main image selection from existing images
        main_image_id = self.request.POST.get('main_image_id', '')
        if main_image_id and main_image_id.isdigit():
            # First, set all images as not main
            ProductImage.objects.filter(product=product).update(is_main=False)
            # Then set the selected image as main
            ProductImage.objects.filter(id=int(main_image_id)).update(is_main=True)
        
        # Handle new main image upload
        new_main_image = self.request.FILES.get('main_image')
        if new_main_image:
            # If a new main image is uploaded, set all existing images as not main
            ProductImage.objects.filter(product=product).update(is_main=False)
            # Create new main image
            ProductImage.objects.create(
                product=product,
                image=new_main_image,
                is_main=True
            )
        elif deleted_main_image and not main_image_id:
            # If main image was deleted and no existing image was selected as main,
            # try to set the first available image as main
            first_image = ProductImage.objects.filter(product=product).first()
            if first_image:
                first_image.is_main = True
                first_image.save()
        
        # Handle additional images
        additional_images = self.request.FILES.getlist('additional_images')
        for image in additional_images:
            ProductImage.objects.create(
                product=product,
                image=image,
                is_main=False
            )
        
        # Log activity
        AdminActivity.objects.create(
            admin=self.request.user,
            action='UPDATE',
            model_name='Product',
            object_id=self.object.id,
            description=f"Updated product: {self.object.name}"
        )
        messages.success(self.request, 'Product updated successfully.')
        return response

class ProductDeleteView(AdminRequiredMixin, DeleteView):
    model = Product
    template_name = 'admin_panel/product_confirm_delete.html'
    success_url = reverse_lazy('admin_products')
    
    def delete(self, request, *args, **kwargs):
        product = self.get_object()
        AdminActivity.objects.create(
            admin=self.request.user,
            action='DELETE',
            model_name='Product',
            object_id=product.id,
            description=f"Deleted product: {product.name}"
        )
        messages.success(request, 'Product deleted successfully.')
        return super().delete(request, *args, **kwargs)

# Display Settings View
class DisplaySettingsView(AdminRequiredMixin, TemplateView):
    template_name = 'admin_panel/display_settings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Lấy danh sách sản phẩm nổi bật
        context['featured_products'] = Product.objects.filter(is_featured=True).order_by('display_order')
        
        # Lấy danh sách tất cả sản phẩm để hiển thị trong form
        context['all_products'] = Product.objects.all().order_by('display_order')
        
        return context
    
    def post(self, request, *args, **kwargs):
        # Xử lý cập nhật sản phẩm nổi bật
        if 'update_featured' in request.POST:
            featured_ids = request.POST.getlist('featured_products')
            
            # Đặt tất cả sản phẩm về không nổi bật
            Product.objects.all().update(is_featured=False)
            
            # Đặt các sản phẩm được chọn là nổi bật
            if featured_ids:
                Product.objects.filter(id__in=featured_ids).update(is_featured=True)
            
            messages.success(request, 'Cập nhật sản phẩm nổi bật thành công.')
        
        # Xử lý cập nhật thứ tự hiển thị
        if 'update_order' in request.POST:
            product_ids = request.POST.getlist('product_id')
            display_orders = request.POST.getlist('display_order')
            
            # Cập nhật thứ tự hiển thị cho từng sản phẩm
            for i, product_id in enumerate(product_ids):
                if product_id and display_orders[i]:
                    try:
                        product = Product.objects.get(id=int(product_id))
                        product.display_order = int(display_orders[i])
                        product.save()
                    except (Product.DoesNotExist, ValueError):
                        pass
            
            messages.success(request, 'Cập nhật thứ tự hiển thị thành công.')
        
        # Xử lý cập nhật SEO
        if 'update_seo' in request.POST:
            product_id = request.POST.get('seo_product_id')
            if product_id:
                try:
                    product = Product.objects.get(id=int(product_id))
                    # Lưu các thông tin SEO (giả định đã có trường meta_title, meta_description)
                    product.meta_title = request.POST.get('meta_title', '')
                    product.meta_description = request.POST.get('meta_description', '')
                    product.save()
                    messages.success(request, 'Cập nhật thông tin SEO thành công.')
                except Product.DoesNotExist:
                    messages.error(request, 'Không tìm thấy sản phẩm.')
        
        return redirect('admin_display_settings')

# Orders View
class OrderListView(AdminRequiredMixin, ListView):
    template_name = 'admin_panel/orders.html'
    context_object_name = 'orders'
    paginate_by = 20
    
    def get_queryset(self):
        from store.models import Order
        queryset = Order.objects.filter(is_ordered=True).order_by('-created_at')
        
        # Search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(order_number__icontains=search_query) | 
                Q(full_name__icontains=search_query) |
                Q(phone__icontains=search_query)
            )
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Quản lý đơn hàng'
        return context

# Update Order Status View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@csrf_exempt
def update_order_status(request):
    """Function-based view để cập nhật trạng thái đơn hàng"""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'Không có quyền truy cập'
        })
    
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Chỉ hỗ trợ POST request'
        })
    
    print(f"DEBUG: update_order_status called")
    print(f"DEBUG: POST data: {request.POST}")
    
    try:
        order_number = request.POST.get('order_number')
        new_status = request.POST.get('status')
        
        print(f"DEBUG: order_number = {order_number}")
        print(f"DEBUG: new_status = {new_status}")
        
        if not order_number or not new_status:
            print(f"DEBUG: Missing order_number or status")
            return JsonResponse({
                'success': False,
                'message': 'Thiếu thông tin đơn hàng hoặc trạng thái'
            })
        
        order = get_object_or_404(Order, order_number=order_number, is_ordered=True)
        old_status = order.status
        print(f"DEBUG: Found order {order_number}, old_status = {old_status}")
        
        order.status = new_status
        order.save()
        print(f"DEBUG: Order status updated successfully")
        
        # Log activity
        AdminActivity.objects.create(
            admin=request.user,
            action='UPDATE',
            model_name='Order',
            object_id=order.id,
            description=f"Updated order {order_number} status from {old_status} to {new_status}"
        )
        print(f"DEBUG: Activity logged")
        
        # Get status display name
        status_display = dict(Order.STATUS_CHOICES).get(new_status, new_status)
        
        response_data = {
            'success': True,
            'message': f'Cập nhật trạng thái đơn hàng {order_number} thành công',
            'status': new_status,
            'status_display': status_display
        }
        print(f"DEBUG: Returning response: {response_data}")
        
        return JsonResponse(response_data)
        
    except Exception as e:
        print(f"DEBUG: Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        })

# Class-based view cho backward compatibility
class UpdateOrderStatusView(AdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        return update_order_status(request)

# Order Detail View
class OrderDetailView(AdminRequiredMixin, DetailView):
    model = Order
    template_name = 'admin_panel/order_detail.html'
    context_object_name = 'order'
    
    def get_queryset(self):
        return Order.objects.filter(is_ordered=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_items'] = self.object.items.all()
        context['title'] = f'Chi tiết đơn hàng {self.object.order_number}'
        return context


# Order Detail AJAX View
def order_detail_ajax(request, order_number):
    """AJAX view để lấy chi tiết đơn hàng"""
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'Không có quyền truy cập'
        })
    
    try:
        order = get_object_or_404(Order, order_number=order_number, is_ordered=True)
        order_items = order.items.all()
        
        # Tạo HTML cho chi tiết đơn hàng
        html_content = f"""
        <div class="row">
            <div class="col-md-6">
                <div class="order-detail-header">
                    <h6><i class="fas fa-user me-2"></i>Thông tin khách hàng</h6>
                    <p class="mb-1"><strong>Tên:</strong> {order.full_name}</p>
                    <p class="mb-1"><strong>Số điện thoại:</strong> {order.phone}</p>
                    <p class="mb-1"><strong>Email:</strong> {order.email or 'Không có'}</p>
                </div>
            </div>
            <div class="col-md-6">
                <div class="order-detail-header">
                    <h6><i class="fas fa-shipping-fast me-2"></i>Thông tin giao hàng</h6>
                    <p class="mb-1"><strong>Địa chỉ:</strong> {order.address}</p>
                    <p class="mb-1"><strong>Thành phố:</strong> {order.city}</p>
                    <p class="mb-1"><strong>Quốc gia:</strong> {order.country}</p>
                    {f'<p class="mb-1"><strong>Mã bưu điện:</strong> {order.postal_code}</p>' if order.postal_code else ''}
                    {f'<p class="mb-1"><strong>Ghi chú:</strong> {order.order_note}</p>' if order.order_note else ''}
                </div>
            </div>
        </div>
        
        <div class="card admin-card mb-3">
            <div class="card-header">
                <h6 class="mb-0"><i class="fas fa-box me-2"></i>Sản phẩm</h6>
            </div>
            <div class="card-body p-0">
                <div class="order-products">
        """
        
        for item in order_items:
            # Lấy hình ảnh chính của sản phẩm
            main_image = item.product.images.filter(is_main=True).first()
            image_html = ''
            if main_image:
                image_html = f'<img src="{main_image.image.url}" alt="{item.product.name}" class="order-product-image">'
            else:
                image_html = '<div class="bg-light rounded d-flex align-items-center justify-content-center order-product-image"><i class="fas fa-box text-secondary"></i></div>'
            
            html_content += f"""
                    <div class="order-product">
                        {image_html}
                        <div class="order-product-details">
                            <div class="fw-bold">{item.product.name}</div>
                            <div class="small text-muted">Số lượng: {item.quantity}</div>
                            <div class="small text-muted">Giá: {item.price:,.0f} VND</div>
                        </div>
                        <div class="order-product-price">
                            {item.subtotal:,.0f} VND
                        </div>
                    </div>
            """
        
        html_content += f"""
                </div>
                <div class="p-3 bg-light border-top">
                    <div class="d-flex justify-content-between">
                        <div class="fw-bold">Tổng cộng:</div>
                        <div class="fw-bold">{order.order_total:,.0f} VND</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card admin-card">
            <div class="card-header">
                <h6 class="mb-0"><i class="fas fa-info-circle me-2"></i>Thông tin đơn hàng</h6>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <p class="mb-1"><strong>Mã đơn hàng:</strong> {order.order_number}</p>
                        <p class="mb-1"><strong>Ngày đặt:</strong> {order.created_at.strftime('%d/%m/%Y %H:%M')}</p>
                        <p class="mb-1"><strong>Trạng thái:</strong> {dict(order.STATUS_CHOICES).get(order.status, order.status)}</p>
                    </div>
                    <div class="col-md-6">
                        <p class="mb-1"><strong>IP đặt hàng:</strong> {order.ip or 'Không có'}</p>
                        <p class="mb-1"><strong>Cập nhật lần cuối:</strong> {order.updated_at.strftime('%d/%m/%Y %H:%M')}</p>
                    </div>
                </div>
            </div>
        </div>
        """
        
        return JsonResponse({
            'success': True,
            'html': html_content
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Lỗi: {str(e)}'
        })

