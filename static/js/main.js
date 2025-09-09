// DecluxDZ - Main JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Cart functionality
    initializeCart();
    
    // Product quantity controls
    initializeQuantityControls();
    
    // Image gallery
    initializeImageGallery();
    
    // Form validation
    initializeFormValidation();
    
    // Admin functionality
    if (window.location.pathname.startsWith('/admin')) {
        initializeAdminFunctionality();
    }
});

// Cart functionality
function initializeCart() {
    // Add to cart buttons
    
            
            // Show loading state
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> جارِ الإضافة...';
            this.disabled = true;
            
            // Add to cart via form submission
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/add_to_cart';
            
            const productIdInput = document.createElement('input');
            productIdInput.type = 'hidden';
            productIdInput.name = 'product_id';
            productIdInput.value = productId;
            
            const quantityInput = document.createElement('input');
            quantityInput.type = 'hidden';
            quantityInput.name = 'quantity';
            quantityInput.value = quantity;
            
            form.appendChild(productIdInput);
            form.appendChild(quantityInput);
            document.body.appendChild(form);
            form.submit();
        };
    

    // Update cart quantities
    document.querySelectorAll('.cart-quantity-input').forEach(input => {
        input.addEventListener('change', function() {
            const form = this.closest('form');
            if (form) {
                form.submit();
            }
        });
    });

    // Remove from cart buttons
    document.querySelectorAll('.remove-from-cart').forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('هل أنت متأكد من حذف هذا المنتج من السلة؟')) {
                e.preventDefault();
            }
        });
    });


// Quantity controls for product detail page
function initializeQuantityControls() {
    const quantityInput = document.querySelector('.quantity-input');
    const decreaseBtn = document.querySelector('.quantity-decrease');
    const increaseBtn = document.querySelector('.quantity-increase');
    
    if (quantityInput && decreaseBtn && increaseBtn) {
        decreaseBtn.addEventListener('click', function() {
            let currentValue = parseInt(quantityInput.value);
            if (currentValue > 1) {
                quantityInput.value = currentValue - 1;
                updateAddToCartButton();
            }
        });
        
        increaseBtn.addEventListener('click', function() {
            let currentValue = parseInt(quantityInput.value);
            quantityInput.value = currentValue + 1;
            updateAddToCartButton();
        });
        
        quantityInput.addEventListener('change', function() {
            if (this.value < 1) {
                this.value = 1;
            }
            updateAddToCartButton();
        });
    }
}

function updateAddToCartButton() {
    const quantityInput = document.querySelector('.quantity-input');
    const addToCartBtn = document.querySelector('.add-to-cart-btn');
    
    if (quantityInput && addToCartBtn) {
        addToCartBtn.dataset.quantity = quantityInput.value;
    }
}

// Image gallery for product detail
function initializeImageGallery() {
    const thumbnails = document.querySelectorAll('.product-thumbnail');
    const mainImage = document.querySelector('.main-product-image');
    
    if (thumbnails.length > 0 && mainImage) {
        thumbnails.forEach(thumbnail => {
            thumbnail.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Remove active class from all thumbnails
                thumbnails.forEach(thumb => thumb.classList.remove('active'));
                
                // Add active class to clicked thumbnail
                this.classList.add('active');
                
                // Update main image
                mainImage.src = this.dataset.fullImage || this.src;
                
                // Add fade effect
                mainImage.style.opacity = '0';
                setTimeout(() => {
                    mainImage.style.opacity = '1';
                }, 150);
            });
        });
    }
}

// Form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            form.classList.add('was-validated');
        });
    });

    // Phone number validation for Arabic format
    const phoneInputs = document.querySelectorAll('input[type="tel"], input[name="phone"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function() {
            // Remove non-digit characters except +
            this.value = this.value.replace(/[^\d+]/g, '');
            
            // Validate Algerian phone format
            const algerianPhonePattern = /^(\+213|0)(5|6|7)[0-9]{8}$/;
            if (this.value && !algerianPhonePattern.test(this.value)) {
                this.setCustomValidity('يرجى إدخال رقم هاتف جزائري صحيح');
            } else {
                this.setCustomValidity('');
            }
        });
    });
}

// Admin functionality
function initializeAdminFunctionality() {
    // Confirm delete actions
    document.querySelectorAll('.delete-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            const itemName = this.dataset.itemName || 'هذا العنصر';
            if (!confirm(`هل أنت متأكد من حذف ${itemName}؟`)) {
                e.preventDefault();
            }
        });
    });

    // Auto-refresh for dashboard stats
    if (window.location.pathname === '/admin') {
        setInterval(refreshDashboardStats, 30000); // Refresh every 30 seconds
    }

    // Product form image preview
    const imageInput = document.querySelector('input[type="file"][name="image"]');
    if (imageInput) {
        imageInput.addEventListener('change', function() {
            previewImage(this);
        });
    }

    // Order status update
    document.querySelectorAll('.status-select').forEach(select => {
        select.addEventListener('change', function() {
            const form = this.closest('form');
            if (form && confirm('هل تريد تحديث حالة الطلب؟')) {
                form.submit();
            }
        });
    });
}

// Image preview for admin forms
function previewImage(input) {
    const preview = document.querySelector('.image-preview');
    const file = input.files[0];
    
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            if (preview) {
                preview.src = e.target.result;
                preview.style.display = 'block';
            } else {
                // Create preview element
                const img = document.createElement('img');
                img.src = e.target.result;
                img.className = 'image-preview img-thumbnail mt-2';
                img.style.maxWidth = '200px';
                input.parentNode.appendChild(img);
            }
        };
        reader.readAsDataURL(file);
    }
}

// Refresh dashboard stats
function refreshDashboardStats() {
    // This would typically fetch updated stats from the server
    // For now, we'll just add a visual indicator that stats are being refreshed
    const statsCards = document.querySelectorAll('.stats-card');
    statsCards.forEach(card => {
        card.style.opacity = '0.8';
        setTimeout(() => {
            card.style.opacity = '1';
        }, 500);
    });
}

// Search functionality
function initializeSearch() {
    const searchInput = document.querySelector('.search-input');
    const searchForm = document.querySelector('.search-form');
    
    if (searchInput && searchForm) {
        let searchTimeout;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length >= 2) {
                searchTimeout = setTimeout(() => {
                    performSearch(query);
                }, 300);
            }
        });
    }
}

function performSearch(query) {
    // Update URL with search query
    const currentUrl = new URL(window.location);
    currentUrl.searchParams.set('search', query);
    window.history.pushState({}, '', currentUrl);
    
    // Submit form
    const searchForm = document.querySelector('.search-form');
    if (searchForm) {
        searchForm.submit();
    }
}

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Lazy loading for images
function initializeLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// Initialize lazy loading if supported
if ('IntersectionObserver' in window) {
    initializeLazyLoading();
}

// Back to top button
function initializeBackToTop() {
    const backToTopBtn = document.createElement('button');
    backToTopBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
    backToTopBtn.className = 'btn btn-primary back-to-top';
    backToTopBtn.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        display: none;
        z-index: 1000;
        border: none;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    
    document.body.appendChild(backToTopBtn);
    
    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 300) {
            backToTopBtn.style.display = 'block';
        } else {
            backToTopBtn.style.display = 'none';
        }
    });
    
    backToTopBtn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}

// Initialize back to top button
initializeBackToTop();
