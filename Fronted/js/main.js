/* ============================================
   VIN-KJ AUTO SERVICES - Frontend JavaScript
   API Integration & UI Logic
   ============================================ */

// ---- Configuration ----
const API_BASE_URL = '/api'; // Change to full URL if frontend is served separately, e.g. 'http://127.0.0.1:8000/api'

// ---- Mobile Nav Dropdown Toggle ----
function toggleMobileNav() {
  const nav = document.getElementById('navbarNav');
  if (!nav) return;
  nav.classList.toggle('show');
}

// Close mobile nav when tapping outside the navbar
document.addEventListener('click', function (e) {
  if (window.innerWidth >= 992) return;
  const nav = document.getElementById('navbarNav');
  if (!nav || !nav.classList.contains('show')) return;

  const navbar = document.getElementById('mainNavbar');
  if (navbar && navbar.contains(e.target)) return; // inside navbar — ignore

  nav.classList.remove('show');
});

// ---- Utility Functions ----

/**
 * Format a number as KSh currency
 */
function formatPrice(amount) {
  const num = parseFloat(amount);
  if (isNaN(num)) return 'KSh 0';
  return 'KSh ' + num.toLocaleString('en-KE', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

/**
 * Truncate text to a given length
 */
function truncateText(text, maxLen) {
  if (!text) return '';
  return text.length > maxLen ? text.substring(0, maxLen) + '...' : text;
}

/**
 * Get a placeholder image if the real one fails to load
 */
function getImageUrl(imagePath) {
  if (!imagePath) return 'https://via.placeholder.com/400x250?text=No+Image';
  // If it's a full URL already, return as is
  if (imagePath.startsWith('http')) return imagePath;
  // Otherwise prefix with base
  return imagePath;
}

/**
 * Show an alert element briefly
 */
function showAlert(elementId, message, duration) {
  const el = document.getElementById(elementId);
  if (!el) return;
  if (message) el.textContent = message;
  el.classList.remove('d-none');
  if (duration) {
    setTimeout(() => el.classList.add('d-none'), duration);
  }
}

function hideAlert(elementId) {
  const el = document.getElementById(elementId);
  if (el) el.classList.add('d-none');
}


// ---- API Fetch Functions ----

async function fetchServices() {
  try {
    const response = await fetch(`${API_BASE_URL}/services/`);
    if (!response.ok) throw new Error('Failed to fetch services');
    return await response.json();
  } catch (error) {
    console.warn('API not available, using fallback:', error.message);
    return null;
  }
}

async function fetchProducts() {
  try {
    const response = await fetch(`${API_BASE_URL}/products/`);
    if (!response.ok) throw new Error('Failed to fetch products');
    return await response.json();
  } catch (error) {
    console.warn('API not available, using fallback:', error.message);
    return null;
  }
}

async function createBooking(bookingData) {
  const response = await fetch(`${API_BASE_URL}/bookings/create/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(bookingData)
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to create booking');
  }
  return await response.json();
}

async function createOrder(orderData) {
  const response = await fetch(`${API_BASE_URL}/orders/create/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(orderData)
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to create order');
  }
  return await response.json();
}


// ---- Render Functions ----

/**
 * Render a service card
 */
function renderServiceCard(service, isPreview) {
  const imgUrl = getImageUrl(service.image);
  const desc = isPreview ? truncateText(service.description, 100) : service.description;
  return `
    <div class="${isPreview ? 'col-md-6 col-lg-4' : 'col-md-6 col-lg-4'}">
      <div class="card-custom">
        <img src="${imgUrl}" class="card-img-top" alt="${service.name}" onerror="this.src='https://via.placeholder.com/400x250?text=Service'">
        <div class="card-body">
          <h5 class="card-title">${service.name}</h5>
          <p class="card-text">${desc}</p>
          <div class="card-price">${formatPrice(service.price)}</div>
        </div>
        <div class="card-footer-custom">
          <a href="services.html#booking" class="btn btn-primary-custom w-100"
             onclick="sessionStorage.setItem('selectedServiceId', '${service.id}'); sessionStorage.setItem('selectedServiceName', '${service.name}'); sessionStorage.setItem('selectedServicePrice', '${service.price}');">
            Book This Service
          </a>
        </div>
      </div>
    </div>
  `;
}

/**
 * Render a product card
 */
function renderProductCard(product, isPreview) {
  const imgUrl = getImageUrl(product.image);
  const desc = isPreview ? truncateText(product.description, 80) : truncateText(product.description, 120);
  const inStock = product.is_available && product.stock_quantity > 0;
  const stockText = inStock ? `In Stock (${product.stock_quantity} units)` : 'Out of Stock';
  const stockClass = inStock ? 'in-stock' : 'out-of-stock';

  const buttonHtml = inStock
    ? `<button class="btn btn-primary-custom w-100" onclick="openOrderModal(${product.id}, '${product.name.replace(/'/g, "\\'")}', ${product.price}, ${product.stock_quantity})">Order Now</button>`
    : `<button class="btn btn-dark-custom w-100" disabled>Out of Stock</button>`;

  return `
    <div class="${isPreview ? 'col-sm-6 col-lg-4' : 'col-sm-6 col-lg-4 col-xl-3'}">
      <div class="card-custom">
        <img src="${imgUrl}" class="card-img-top" alt="${product.name}" onerror="this.src='https://via.placeholder.com/400x250?text=Product'">
        <div class="card-body">
          <h5 class="card-title">${product.name}</h5>
          <p class="card-text">${desc}</p>
          <div class="card-price">${formatPrice(product.price)}</div>
          <span class="card-stock ${stockClass}">${stockText}</span>
        </div>
        <div class="card-footer-custom">
          ${buttonHtml}
        </div>
      </div>
    </div>
  `;
}


// ---- Page Initialization ----

// Store fetched data for search/filter
let allProducts = [];
let allServices = [];

document.addEventListener('DOMContentLoaded', async () => {

  // ---- Home Page: Services Preview ----
  const servicesPreviewContainer = document.getElementById('servicesPreviewContainer');
  if (servicesPreviewContainer) {
    const services = await fetchServices();
    if (services && services.length > 0) {
      allServices = services;
      const previewServices = services.slice(0, 3);
      servicesPreviewContainer.innerHTML = previewServices.map(s => renderServiceCard(s, true)).join('');
    } else {
      servicesPreviewContainer.innerHTML = `
        <div class="no-results">
          <span class="material-icons">build_circle</span>
          <h5>Services coming soon</h5>
          <p>We're updating our service listings. Check back shortly.</p>
        </div>
      `;
    }
  }

  // ---- Home Page: Products Preview ----
  const productsPreviewContainer = document.getElementById('productsPreviewContainer');
  if (productsPreviewContainer) {
    const products = await fetchProducts();
    if (products && products.length > 0) {
      allProducts = products;
      const previewProducts = products.filter(p => p.is_available).slice(0, 3);
      if (previewProducts.length > 0) {
        productsPreviewContainer.innerHTML = previewProducts.map(p => renderProductCard(p, true)).join('');
      } else {
        productsPreviewContainer.innerHTML = products.slice(0, 3).map(p => renderProductCard(p, true)).join('');
      }
    } else {
      productsPreviewContainer.innerHTML = `
        <div class="no-results">
          <span class="material-icons">inventory_2</span>
          <h5>Products coming soon</h5>
          <p>Our product catalog is being updated. Check back shortly.</p>
        </div>
      `;
    }
  }

  // ---- Services Page: Full Listing ----
  const servicesContainer = document.getElementById('servicesContainer');
  if (servicesContainer && !servicesPreviewContainer) {
    const services = await fetchServices();
    if (services && services.length > 0) {
      allServices = services;
      servicesContainer.innerHTML = services.map(s => renderServiceCard(s, false)).join('');
    } else {
      servicesContainer.innerHTML = '';
      const noServices = document.getElementById('noServicesFound');
      if (noServices) noServices.classList.remove('d-none');
    }
  }

  // ---- Services Page: Populate Booking Dropdown ----
  const bookingServiceSelect = document.getElementById('bookingService');
  if (bookingServiceSelect) {
    let services = allServices;
    if (!services || services.length === 0) {
      services = await fetchServices();
      if (services) allServices = services;
    }
    if (services && services.length > 0) {
      bookingServiceSelect.innerHTML = '<option value="" disabled selected>-- Select a Service --</option>';
      services.forEach(s => {
        const option = document.createElement('option');
        option.value = s.id;
        option.textContent = `${s.name} - ${formatPrice(s.price)}`;
        option.dataset.price = s.price;
        bookingServiceSelect.appendChild(option);
      });

      // Pre-select if coming from a card click
      const savedId = sessionStorage.getItem('selectedServiceId');
      if (savedId) {
        bookingServiceSelect.value = savedId;
        const priceDisplay = document.getElementById('bookingPrice');
        const savedPrice = sessionStorage.getItem('selectedServicePrice');
        if (priceDisplay && savedPrice) priceDisplay.textContent = formatPrice(savedPrice);
        sessionStorage.removeItem('selectedServiceId');
        sessionStorage.removeItem('selectedServiceName');
        sessionStorage.removeItem('selectedServicePrice');
      }
    } else {
      bookingServiceSelect.innerHTML = '<option value="" disabled selected>-- No services available yet --</option>';
    }

    // Update price on change
    bookingServiceSelect.addEventListener('change', function () {
      const selected = this.options[this.selectedIndex];
      const priceDisplay = document.getElementById('bookingPrice');
      if (priceDisplay && selected.dataset.price) {
        priceDisplay.textContent = formatPrice(selected.dataset.price);
      }
    });
  }

  // ---- Products Page: Full Listing ----
  const productsContainer = document.getElementById('productsContainer');
  if (productsContainer && !productsPreviewContainer) {
    const products = await fetchProducts();
    if (products && products.length > 0) {
      allProducts = products;
      productsContainer.innerHTML = products.map(p => renderProductCard(p, false)).join('');
    } else {
      productsContainer.innerHTML = `
        <div class="no-results">
          <span class="material-icons">inventory_2</span>
          <h5>No products available yet</h5>
          <p>Our product catalog is being updated. Check back soon.</p>
        </div>
      `;
    }
  }

  // ---- Products Page: Search & Filter ----
  const productSearch = document.getElementById('productSearch');
  const productFilter = document.getElementById('productFilter');

  function filterProducts() {
    if (!productsContainer || allProducts.length === 0) return;
    const searchTerm = (productSearch ? productSearch.value : '').toLowerCase();
    const filterVal = productFilter ? productFilter.value : 'all';

    let filtered = allProducts.filter(p => {
      const matchesSearch = p.name.toLowerCase().includes(searchTerm) || (p.description && p.description.toLowerCase().includes(searchTerm));
      const matchesFilter = filterVal === 'all' || (filterVal === 'in-stock' && p.is_available && p.stock_quantity > 0);
      return matchesSearch && matchesFilter;
    });

    const noResults = document.getElementById('noProductsFound');
    if (filtered.length > 0) {
      productsContainer.innerHTML = filtered.map(p => renderProductCard(p, false)).join('');
      productsContainer.classList.remove('d-none');
      if (noResults) noResults.classList.add('d-none');
    } else {
      productsContainer.innerHTML = '';
      if (noResults) noResults.classList.remove('d-none');
    }
  }

  if (productSearch) productSearch.addEventListener('input', filterProducts);
  if (productFilter) productFilter.addEventListener('change', filterProducts);

  // ---- About Page: Dynamic Gallery ----
  const galleryContainer = document.getElementById('galleryContainer');
  if (galleryContainer) {
    try {
      const [services, products] = await Promise.all([fetchServices(), fetchProducts()]);
      const images = [];

      if (services) {
        services.forEach(s => {
          if (s.image) images.push({ url: s.image, alt: s.name, type: 'Service' });
        });
      }
      if (products) {
        products.forEach(p => {
          if (p.image) images.push({ url: p.image, alt: p.name, type: 'Product' });
        });
      }

      const spinner = galleryContainer.querySelector('.text-center');
      if (spinner) spinner.remove();

      const noGallery = document.getElementById('noGalleryItems');

      if (images.length > 0) {
        galleryContainer.innerHTML = images.map(img => `
          <div class="col-6 col-md-4 col-lg-3">
            <div class="card-custom gallery-card" style="overflow:hidden; border-radius:12px;">
              <img src="${img.url}" alt="${img.alt}" class="card-img-top" style="height:200px; object-fit:cover;" loading="lazy">
              <div class="card-body p-2 text-center">
                <small class="text-muted">${img.type}</small>
                <h6 class="mb-0 mt-1" style="font-size:0.85rem;">${img.alt}</h6>
              </div>
            </div>
          </div>
        `).join('');
        if (noGallery) noGallery.classList.add('d-none');
      } else {
        galleryContainer.innerHTML = '';
        if (noGallery) noGallery.classList.remove('d-none');
      }
    } catch (err) {
      console.error('Gallery load error:', err);
      const spinner = galleryContainer.querySelector('.text-center');
      if (spinner) spinner.remove();
      const noGallery = document.getElementById('noGalleryItems');
      if (noGallery) noGallery.classList.remove('d-none');
    }
  }

  // ---- Set min date for booking ----
  const bookingDate = document.getElementById('bookingDate');
  if (bookingDate) {
    const today = new Date().toISOString().split('T')[0];
    bookingDate.setAttribute('min', today);
  }
});


// ---- Booking Form Submission ----
document.addEventListener('submit', async function (e) {
  if (e.target.id === 'bookingForm') {
    e.preventDefault();
    const submitBtn = document.getElementById('bookingSubmitBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting...';
    hideAlert('bookingSuccess');
    hideAlert('bookingError');

    const serviceId = document.getElementById('bookingService').value;
    const selectedOption = document.getElementById('bookingService').options[document.getElementById('bookingService').selectedIndex];
    const price = selectedOption.dataset.price || 0;

    const bookingData = {
      services: serviceId,
      total_price: parseFloat(price),
      full_name: document.getElementById('bookingName').value,
      phone_number: document.getElementById('bookingPhone').value,
      vehicle_model: document.getElementById('bookingVehicle').value,
      number_plate: document.getElementById('bookingPlate').value,
      booking_date: document.getElementById('bookingDate').value,
      booking_time: document.getElementById('bookingTime').value,
      additional_notes: document.getElementById('bookingNotes').value
    };

    try {
      await createBooking(bookingData);
      showAlert('bookingSuccess', 'Your booking has been submitted successfully! We\'ll confirm your appointment shortly.', 8000);
      e.target.reset();
      const priceDisplay = document.getElementById('bookingPrice');
      if (priceDisplay) priceDisplay.textContent = '--';
    } catch (error) {
      showAlert('bookingError', error.message || 'Something went wrong. Please try again.', 6000);
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Submit Booking';
    }
  }
});


// ---- Payment Method Selection ----
let selectedPaymentMethod = null;

function selectPayment(method) {
  selectedPaymentMethod = method;

  // Update radio buttons
  const onlineRadio = document.getElementById('payOnline');
  const deliveryRadio = document.getElementById('payDelivery');
  if (onlineRadio) onlineRadio.checked = method === 'online';
  if (deliveryRadio) deliveryRadio.checked = method === 'delivery';

  // Update visual selection
  const onlineOption = document.getElementById('payOnlineOption');
  const deliveryOption = document.getElementById('payDeliveryOption');
  if (onlineOption) onlineOption.classList.toggle('selected', method === 'online');
  if (deliveryOption) deliveryOption.classList.toggle('selected', method === 'delivery');

  // Show/hide payment detail panels
  const onlineDetails = document.getElementById('onlinePaymentDetails');
  const deliveryNote = document.getElementById('deliveryPaymentNote');
  if (onlineDetails) onlineDetails.classList.toggle('d-none', method !== 'online');
  if (deliveryNote) deliveryNote.classList.toggle('d-none', method !== 'delivery');

  // Make M-Pesa code required only for online
  const mpesaInput = document.getElementById('orderMpesaCode');
  if (mpesaInput) mpesaInput.required = method === 'online';
}

// ---- Order Modal Logic ----
let currentOrderProduct = null;

function openOrderModal(productId, productName, unitPrice, stockQty) {
  currentOrderProduct = { id: productId, name: productName, price: unitPrice, stock: stockQty };

  document.getElementById('orderGoodsId').value = productId;
  document.getElementById('orderProductName').textContent = productName;
  document.getElementById('orderUnitPrice').textContent = 'Unit Price: ' + formatPrice(unitPrice);
  document.getElementById('orderTotalDisplay').textContent = formatPrice(unitPrice);
  document.getElementById('orderQuantity').value = 1;
  document.getElementById('orderQuantity').max = stockQty;

  // Reset form fields
  document.getElementById('orderForm').reset();
  document.getElementById('orderGoodsId').value = productId;
  document.getElementById('orderQuantity').value = 1;

  // Reset payment selection
  selectedPaymentMethod = null;
  const onlineOption = document.getElementById('payOnlineOption');
  const deliveryOption = document.getElementById('payDeliveryOption');
  if (onlineOption) onlineOption.classList.remove('selected');
  if (deliveryOption) deliveryOption.classList.remove('selected');
  const onlineDetails = document.getElementById('onlinePaymentDetails');
  const deliveryNote = document.getElementById('deliveryPaymentNote');
  if (onlineDetails) onlineDetails.classList.add('d-none');
  if (deliveryNote) deliveryNote.classList.add('d-none');

  hideAlert('orderSuccess');
  hideAlert('orderError');

  const modal = new bootstrap.Modal(document.getElementById('orderModal'));
  modal.show();
}

// Update total on quantity change
document.addEventListener('input', function (e) {
  if (e.target.id === 'orderQuantity' && currentOrderProduct) {
    const qty = parseInt(e.target.value) || 1;
    const total = qty * currentOrderProduct.price;
    document.getElementById('orderTotalDisplay').textContent = formatPrice(total);
  }
});

// Order Submit
document.addEventListener('click', async function (e) {
  if (e.target.id === 'orderSubmitBtn') {
    const form = document.getElementById('orderForm');
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    const submitBtn = e.target;
    submitBtn.disabled = true;
    submitBtn.textContent = 'Placing Order...';
    hideAlert('orderSuccess');
    hideAlert('orderError');

    const qty = parseInt(document.getElementById('orderQuantity').value) || 1;

    // Validate payment method selection
    if (!selectedPaymentMethod) {
      showAlert('orderError', 'Please select a payment method.', 4000);
      submitBtn.disabled = false;
      submitBtn.textContent = 'Place Order';
      return;
    }

    // Validate M-Pesa code for online payment
    const mpesaCode = document.getElementById('orderMpesaCode');
    if (selectedPaymentMethod === 'online' && mpesaCode && !mpesaCode.value.trim()) {
      showAlert('orderError', 'Please enter your M-Pesa transaction code.', 4000);
      submitBtn.disabled = false;
      submitBtn.textContent = 'Place Order';
      return;
    }

    const orderData = {
      product: parseInt(document.getElementById('orderGoodsId').value),
      quantity: qty,
      total_price: qty * currentOrderProduct.price,
      full_name: document.getElementById('orderName').value,
      phone_number: document.getElementById('orderPhone').value,
      vehicle_make: document.getElementById('orderVehicleMake').value,
      vehicle_model: document.getElementById('orderVehicleModel').value,
      vehicle_year: document.getElementById('orderVehicleYear').value,
      auto_part: document.getElementById('orderAutoPart').value,
      estate: document.getElementById('orderEstate').value,
      street_address: document.getElementById('orderStreet').value,
      payment_method: selectedPaymentMethod,
      mpesa_code: selectedPaymentMethod === 'online' && mpesaCode ? mpesaCode.value.trim() : null
    };

    try {
      await createOrder(orderData);
      showAlert('orderSuccess', 'Your order has been placed successfully! We\'ll contact you shortly to confirm.', 8000);
      form.reset();
    } catch (error) {
      showAlert('orderError', error.message || 'Something went wrong. Please try again.', 6000);
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Place Order';
    }
  }
});


// ---- Contact Form (basic - no backend endpoint yet) ----
document.addEventListener('submit', function (e) {
  if (e.target.id === 'contactForm') {
    e.preventDefault();
    alert('Thank you for your message! We will get back to you shortly.');
    e.target.reset();
  }
});


// ---- Navbar Scroll Effect ----
window.addEventListener('scroll', function () {
  const navbar = document.getElementById('mainNavbar');
  if (navbar) {
    if (window.scrollY > 50) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  }

  // Back to top button
  const backToTop = document.getElementById('backToTop');
  if (backToTop) {
    if (window.scrollY > 400) {
      backToTop.classList.add('show');
    } else {
      backToTop.classList.remove('show');
    }
  }
});

// Back to top click
document.addEventListener('click', function (e) {
  if (e.target.closest('#backToTop')) {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
});
