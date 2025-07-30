// Admin Panel JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Toggle sidebar on mobile
    const sidebarToggler = document.querySelector('.sidebar-toggler');
    if (sidebarToggler) {
        sidebarToggler.addEventListener('click', function() {
            document.querySelector('.admin-sidebar').classList.toggle('expanded');
        });
    }
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Product image upload handling
    initProductImageUpload();
});

// Product image upload functionality
function initProductImageUpload() {
    // Main image upload
    const mainImageDropArea = document.getElementById('mainImageDropArea');
    const mainImageInput = document.getElementById('id_main_image');
    const mainImagePreview = document.getElementById('mainImagePreview');
    
    if (mainImageDropArea && mainImageInput) {
        // Click to select file
        mainImageDropArea.addEventListener('click', function() {
            mainImageInput.click();
        });
        
        // File selection handler
        mainImageInput.addEventListener('change', function() {
            handleImageSelection(this, mainImagePreview, mainImageDropArea);
        });
        
        // Drag and drop for main image
        setupDragAndDrop(mainImageDropArea, mainImageInput);
    }
    
    // Additional images upload
    const additionalImagesDropArea = document.getElementById('additionalImagesDropArea');
    const additionalImagesInput = document.getElementById('id_additional_images');
    const additionalImagesPreview = document.getElementById('additionalImagesPreview');
    
    if (additionalImagesDropArea && additionalImagesInput) {
        // Click to select files
        additionalImagesDropArea.addEventListener('click', function() {
            additionalImagesInput.click();
        });
        
        // File selection handler
        additionalImagesInput.addEventListener('change', function() {
            handleMultipleImageSelection(this, additionalImagesPreview, additionalImagesDropArea);
        });
        
        // Drag and drop for additional images
        setupDragAndDrop(additionalImagesDropArea, additionalImagesInput);
    }
    
    // Set up delete buttons for existing images
    setupImageDeleteButtons();
    
    // Set up "Set as main" functionality
    setupSetAsMainButtons();
}

// Handle single image selection
function handleImageSelection(input, previewElement, dropArea) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            // Create or update preview
            if (previewElement) {
                // If preview exists, update it
                const img = previewElement.querySelector('img') || document.createElement('img');
                img.src = e.target.result;
                img.className = 'img-fluid';
                
                if (!previewElement.contains(img)) {
                    previewElement.appendChild(img);
                }
                
                previewElement.style.display = 'block';
                if (dropArea) dropArea.style.display = 'none';
            }
        };
        
        reader.readAsDataURL(input.files[0]);
    }
}

// Handle multiple image selection
function handleMultipleImageSelection(input, previewContainer, dropArea) {
    if (input.files && input.files.length > 0) {
        // Clear previous preview if needed
        // previewContainer.innerHTML = '';
        
        for (let i = 0; i < input.files.length; i++) {
            const file = input.files[i];
            const reader = new FileReader();
            
            reader.onload = function(e) {
                const previewItem = document.createElement('div');
                previewItem.className = 'image-preview';
                
                const img = document.createElement('img');
                img.src = e.target.result;
                img.className = 'img-fluid';
                img.alt = 'Product image';
                
                const deleteBtn = document.createElement('div');
                deleteBtn.className = 'delete-btn';
                deleteBtn.innerHTML = '<i class="fas fa-times"></i>';
                deleteBtn.setAttribute('data-bs-toggle', 'tooltip');
                deleteBtn.setAttribute('title', 'Remove');
                deleteBtn.onclick = function() {
                    previewItem.remove();
                };
                
                previewItem.appendChild(img);
                previewItem.appendChild(deleteBtn);
                previewContainer.appendChild(previewItem);
            };
            
            reader.readAsDataURL(file);
        }
        
        previewContainer.style.display = 'flex';
        if (dropArea) dropArea.style.display = 'none';
    }
}

// Setup drag and drop functionality
function setupDragAndDrop(dropArea, fileInput) {
    if (!dropArea) return;
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        dropArea.classList.add('highlight');
    }
    
    function unhighlight() {
        dropArea.classList.remove('highlight');
    }
    
    dropArea.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (fileInput.multiple) {
            // For multiple file input
            handleMultipleImageSelection({files: files}, 
                document.getElementById('additionalImagesPreview'), 
                document.getElementById('additionalImagesDropArea'));
        } else {
            // For single file input
            if (files && files.length > 0) {
                fileInput.files = files;
                const event = new Event('change', { bubbles: true });
                fileInput.dispatchEvent(event);
            }
        }
    }
}

// Setup delete buttons for existing images
function setupImageDeleteButtons() {
    // Delete main image
    const deleteMainImageBtn = document.getElementById('deleteMainImage');
    if (deleteMainImageBtn) {
        deleteMainImageBtn.addEventListener('click', function() {
            const mainImagePreview = document.getElementById('mainImagePreview');
            const mainImageDropArea = document.getElementById('mainImageDropArea');
            const deletedMainImageInput = document.getElementById('deleted_main_image');
            
            if (mainImagePreview) mainImagePreview.style.display = 'none';
            if (mainImageDropArea) mainImageDropArea.style.display = 'block';
            if (deletedMainImageInput) deletedMainImageInput.value = 'true';
        });
    }
    
    // Delete additional images
    const deleteImageBtns = document.querySelectorAll('.delete-additional-image');
    deleteImageBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const imageId = this.getAttribute('data-image-id');
            const imagePreview = this.closest('.image-preview');
            const deletedImagesInput = document.getElementById('deleted_images');
            
            if (imagePreview) imagePreview.style.display = 'none';
            
            // Add to deleted images list
            if (deletedImagesInput && imageId) {
                const currentIds = deletedImagesInput.value ? deletedImagesInput.value.split(',') : [];
                if (!currentIds.includes(imageId)) {
                    currentIds.push(imageId);
                    deletedImagesInput.value = currentIds.join(',');
                }
            }
        });
    });
}

// Setup "Set as main" functionality
function setupSetAsMainButtons() {
    const setMainBtns = document.querySelectorAll('.set-as-main');
    if (!setMainBtns.length) return;
    
    setMainBtns.forEach(btn => {
        btn.addEventListener('change', function() {
            if (this.checked) {
                // Uncheck all other radio buttons
                setMainBtns.forEach(radio => {
                    if (radio !== this) radio.checked = false;
                });
                
                // Set the main_image_id field
                const mainImageIdInput = document.getElementById('main_image_id');
                if (mainImageIdInput) {
                    mainImageIdInput.value = this.value;
                }
            }
        });
    });
} 