/* ============================================
   VIN-KJ AUTO SERVICES - Frontend JavaScript
   API Integration & UI Logic
   ============================================ */

// ---- Configuration ----
const API_BASE_URL = '/api';

// ---- Mobile Nav Dropdown Toggle ----
function toggleMobileNav() {
  const nav = document.getElementById('navbarNav');
  if (!nav) return;
  nav.classList.toggle('show');
}

document.addEventListener('click', function (e) {
  if (window.innerWidth >= 992) return;
  const nav = document.getElementById('navbarNav');
  if (!nav || !nav.classList.contains('show')) return;
  const navbar = document.getElementById('mainNavbar');
  if (navbar && navbar.contains(e.target)) return;
  nav.classList.remove('show');
});

// ---- Utility Functions ----
function formatPrice(amount) {
  const num = parseFloat(amount);
  if (isNaN(num)) return 'KSh 0';
  return 'KSh ' + num.toLocaleString('en-KE', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function truncateText(text, maxLen) {
  if (!text) return '';
  return text.length > maxLen ? text.substring(0, maxLen) + '...' : text;
}

function getImageUrl(imagePath) {
  if (!imagePath) return 'https://via.placeholder.com/400x250?text=No+Image';
  if (imagePath.startsWith('http')) return imagePath;
  return imagePath;
}

function showAlert(elementId, message, duration) {
  const el = document.getElementById(elementId);
  if (!el) return;
  if (message) {
    const msgSpan = el.querySelector('span:not(.material-icons)') || el;
    if (msgSpan) msgSpan.textContent = message;
  }
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
    console.warn('API error:', error.message);
    return null;
  }
}

async function fetchProducts() {
  try {
    const response = await fetch(`${API_BASE_URL}/products/`);
    if (!response.ok) throw new Error('Failed to fetch products');
    return await response.json();
  } catch (error) {
    console.warn('API error:', error.message);
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

// ---- Cart Manager ----
const CartManager = {
  items: JSON.parse(localStorage.getItem('vinkj_cart')) || [],

  save() {
    localStorage.setItem('vinkj_cart', JSON.stringify(this.items));
    this.updateUI();
  },

  add(product) {
    const existing = this.items.find(item => item.id === product.id);
    if (existing) {
      if (existing.quantity < product.stock) {
        existing.quantity++;
      } else {
        alert('Cannot add more. Max stock reached.');
        return;
      }
    } else {
      this.items.push({
        id: product.id,
        name: product.name,
        price: product.price,
        image: product.image,
        stock: product.stock,
        quantity: 1
      });
    }
    this.save();
    this.showFloatingBadgeAnimation();
  },

  remove(id) {
    this.items = this.items.filter(item => item.id !== id);
    this.save();
  },

  updateQuantity(id, delta) {
    const item = this.items.find(item => item.id === id);
    if (item) {
      const newQty = item.quantity + delta;
      if (newQty > 0 && newQty <= item.stock) {
        item.quantity = newQty;
        this.save();
      }
    }
  },

  getTotal() {
    return this.items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  },

  getCount() {
    return this.items.reduce((sum, item) => sum + item.quantity, 0);
  },

  clear() {
    this.items = [];
    this.save();
  },

  updateUI() {
    const badge = document.getElementById('cartBadge');
    const totalDisplay = document.getElementById('cartTotalDisplay');
    const container = document.getElementById('cartItemsContainer');
    const checkoutBtn = document.getElementById('checkoutBtn');
    const count = this.getCount();

    if (badge) {
      badge.textContent = count;
      badge.classList.toggle('d-none', count === 0);
    }

    if (totalDisplay) totalDisplay.textContent = formatPrice(this.getTotal());
    if (checkoutBtn) checkoutBtn.disabled = count === 0;

    if (container) {
      if (this.items.length === 0) {
        container.innerHTML = `
          <div class="text-center py-5 opacity-50">
            <span class="material-icons" style="font-size: 3rem;">shopping_basket</span>
            <p class="mt-2">Your cart is empty</p>
          </div>
        `;
      } else {
        container.innerHTML = this.items.map(item => `
          <div class="cart-item-row">
            <img src="${getImageUrl(item.image)}" class="cart-item-img" alt="${item.name}">
            <div class="cart-item-info">
              <div class="cart-item-title">${item.name}</div>
              <div class="cart-item-price">${formatPrice(item.price)}</div>
              <div class="qty-control">
                <button class="btn-qty" onclick="CartManager.updateQuantity(${item.id}, -1)">-</button>
                <span class="small mx-1">${item.quantity}</span>
                <button class="btn-qty" onclick="CartManager.updateQuantity(${item.id}, 1)">+</button>
                <button class="btn btn-link btn-sm text-danger ms-auto p-0" onclick="CartManager.remove(${item.id})">
                  <span class="material-icons" style="font-size: 1.2rem;">delete_outline</span>
                </button>
              </div>
            </div>
          </div>
        `).join('');
      }
    }
  },

  showFloatingBadgeAnimation() {
    const cartBtn = document.getElementById('cartBtn');
    if (cartBtn) {
      cartBtn.classList.add('animate__animated', 'animate__pulse');
      setTimeout(() => cartBtn.classList.remove('animate__animated', 'animate__pulse'), 500);
    }
  }
};

// ---- Render Functions ----
function renderServiceCard(service, isPreview) {
  const imgUrl = getImageUrl(service.image);
  const desc = isPreview ? truncateText(service.description, 100) : service.description;
  return `
    <div class="col-md-6 col-lg-4">
      <div class="card-custom">
        <img src="${imgUrl}" class="card-img-top" alt="${service.name}" onerror="this.src='https://via.placeholder.com/400x250?text=Service'">
        <div class="card-body">
          <h5 class="card-title">${service.name}</h5>
          <p class="card-text">${desc}</p>
          <div class="card-price">${formatPrice(service.price)}</div>
        </div>
        <div class="card-footer-custom">
          <a href="services.html#booking" class="btn btn-primary-custom w-100"
             onclick="sessionStorage.setItem('selectedServiceId', '${service.id}'); sessionStorage.setItem('selectedServicePrice', '${service.price}');">
            Book Now
          </a>
        </div>
      </div>
    </div>
  `;
}

function renderProductCard(product, isPreview) {
  const imgUrl = getImageUrl(product.image);
  const desc = isPreview ? truncateText(product.description, 80) : truncateText(product.description, 120);
  const inStock = product.is_available && product.stock_quantity > 0;
  const stockText = inStock ? `In Stock (${product.stock_quantity})` : 'Out of Stock';
  const stockClass = inStock ? 'in-stock' : 'out-of-stock';

  const buttonHtml = inStock
    ? `<button class="btn btn-primary-custom w-100 d-flex align-items-center justify-content-center gap-2" 
               onclick="CartManager.add({id: ${product.id}, name: '${product.name.replace(/'/g, "\\'")}', price: ${product.price}, image: '${product.image}', stock: ${product.stock_quantity}})">
          <span class="material-icons" style="font-size: 1.2rem;">add_shopping_cart</span> Add to Cart
       </button>`
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

// ---- Initialization ----
document.addEventListener('DOMContentLoaded', async () => {
  CartManager.updateUI();

  const checkoutBtn = document.getElementById('checkoutBtn');
  if (checkoutBtn) {
    checkoutBtn.addEventListener('click', () => {
      const offcanvasEl = document.getElementById('cartOffcanvas');
      const offcanvas = bootstrap.Offcanvas.getInstance(offcanvasEl) || new bootstrap.Offcanvas(offcanvasEl);
      offcanvas.hide();
      openCheckoutModal();
    });
  }

  // Load Products
  const productsContainer = document.getElementById('productsContainer');
  const productsPreview = document.getElementById('productsPreviewContainer');
  if (productsContainer || productsPreview) {
    const products = await fetchProducts();
    if (products) {
      if (productsContainer) productsContainer.innerHTML = products.map(p => renderProductCard(p, false)).join('');
      if (productsPreview) productsPreview.innerHTML = products.filter(p => p.is_available).slice(0, 3).map(p => renderProductCard(p, true)).join('');
    }
  }

  // Load Services
  const servicesContainer = document.getElementById('servicesContainer');
  const servicesPreview = document.getElementById('servicesPreviewContainer');
  if (servicesContainer || servicesPreview) {
    const services = await fetchServices();
    if (services) {
      if (servicesContainer) servicesContainer.innerHTML = services.map(s => renderServiceCard(s, false)).join('');
      if (servicesPreview) servicesPreview.innerHTML = services.slice(0, 3).map(s => renderServiceCard(s, true)).join('');
    }
  }

  // Booking logic
  const bookingForm = document.getElementById('bookingForm');
  if (bookingForm) {
    const bookingServiceSelect = document.getElementById('bookingService');
    const services = await fetchServices();
    if (services && bookingServiceSelect) {
      bookingServiceSelect.innerHTML = '<option value="" disabled selected>-- Select a Service --</option>' +
        services.map(s => `<option value="${s.id}" data-price="${s.price}">${s.name} - ${formatPrice(s.price)}</option>`).join('');

      const savedId = sessionStorage.getItem('selectedServiceId');
      if (savedId) {
        bookingServiceSelect.value = savedId;
        const savedPrice = sessionStorage.getItem('selectedServicePrice');
        if (savedPrice) document.getElementById('bookingPrice').textContent = formatPrice(savedPrice);
        sessionStorage.removeItem('selectedServiceId');
        sessionStorage.removeItem('selectedServicePrice');
      }

      bookingServiceSelect.addEventListener('change', function () {
        const selected = this.options[this.selectedIndex];
        document.getElementById('bookingPrice').textContent = formatPrice(selected.dataset.price);
      });
    }

    bookingForm.addEventListener('submit', async function (e) {
      e.preventDefault();
      const submitBtn = document.getElementById('bookingSubmitBtn');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Submitting...';
      try {
        const price = bookingServiceSelect.options[bookingServiceSelect.selectedIndex].dataset.price;
        await createBooking({
          services: bookingServiceSelect.value,
          total_price: parseFloat(price),
          full_name: document.getElementById('bookingName').value,
          phone_number: document.getElementById('bookingPhone').value,
          vehicle_model: document.getElementById('bookingVehicle').value,
          number_plate: document.getElementById('bookingPlate').value,
          booking_date: document.getElementById('bookingDate').value,
          booking_time: document.getElementById('bookingTime').value,
          additional_notes: document.getElementById('bookingNotes').value
        });
        showAlert('bookingSuccess', 'Booking submitted!', 8000);
        bookingForm.reset();
      } catch (err) {
        showAlert('bookingError', err.message, 6000);
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Booking';
      }
    });
  }
});

// ---- Checkout Modal logic ----
let selectedPaymentMethod = null;

function openCheckoutModal() {
  const modalEl = document.getElementById('orderModal');
  if (!modalEl) return;
  const itemsList = document.getElementById('checkoutItemsList');
  if (itemsList) {
    itemsList.innerHTML = CartManager.items.map(item => `
      <div class="d-flex justify-content-between align-items-center mb-2 small">
        <span>${item.name} x ${item.quantity}</span>
        <span>${formatPrice(item.price * item.quantity)}</span>
      </div>
    `).join('');
  }
  document.getElementById('checkoutTotalDisplay').textContent = formatPrice(CartManager.getTotal());
  selectedPaymentMethod = null;
  document.querySelectorAll('.payment-option').forEach(el => el.classList.remove('selected'));
  if (document.getElementById('stkPrompt')) document.getElementById('stkPrompt').classList.add('d-none');
  new bootstrap.Modal(modalEl).show();
}

/**
 * Global function for payment selection (called by onclick in HTML)
 */
window.selectPayment = function (method) {
  selectedPaymentMethod = method;
  document.querySelectorAll('.payment-option').forEach(el => {
    el.classList.toggle('selected', el.id === (method === 'online' ? 'payOnlineOption' : 'payDeliveryOption'));
  });
  const onlineRadio = document.getElementById('payOnline');
  const deliveryRadio = document.getElementById('payDelivery');
  if (onlineRadio) onlineRadio.checked = (method === 'online');
  if (deliveryRadio) deliveryRadio.checked = (method === 'delivery');
};

document.addEventListener('click', async function (e) {
  if (e.target.id === 'orderSubmitBtn') {
    const form = document.getElementById('orderForm');
    if (!form.checkValidity()) { form.reportValidity(); return; }
    if (!selectedPaymentMethod) { alert('Please select a payment method.'); return; }

    const submitBtn = e.target;
    submitBtn.disabled = true;
    submitBtn.textContent = 'Processing...';

    const cartSummary = CartManager.items.map(i => `${i.name} (${i.quantity})`).join(', ');
    const orderData = {
      product: CartManager.items[0].id,
      quantity: CartManager.items[0].quantity,
      total_price: CartManager.getTotal(),
      full_name: document.getElementById('orderName').value,
      phone_number: document.getElementById('orderPhone').value,
      estate: document.getElementById('orderEstate').value,
      street_address: document.getElementById('orderStreet').value,
      auto_part: `Cart Order: ${cartSummary}`,
      payment_method: selectedPaymentMethod === 'online' ? 'M-Pesa' : 'Delivery'
    };

    try {
      const order = await createOrder(orderData);
      if (selectedPaymentMethod === 'online') {
        const stkPrompt = document.getElementById('stkPrompt');
        if (stkPrompt) stkPrompt.classList.remove('d-none');
        await fetch(`${API_BASE_URL}/payments/initiate-mpesa/${order.id}/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ phone_number: orderData.phone_number })
        });
        showAlert('orderSuccess', 'STK Push sent! Check your phone.', 10000);
      } else {
        showAlert('orderSuccess', 'Order placed!', 8000);
      }
      CartManager.clear();
      setTimeout(() => {
        const modal = bootstrap.Modal.getInstance(document.getElementById('orderModal'));
        if (modal) modal.hide();
      }, 3000);
    } catch (err) {
      showAlert('orderError', err.message, 6000);
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Confirm Order';
    }
  }
});

// Navbar scroll effect
window.addEventListener('scroll', function () {
  const navbar = document.getElementById('mainNavbar');
  if (navbar) {
    navbar.classList.toggle('scrolled', window.scrollY > 50);
  }
  const backToTop = document.getElementById('backToTop');
  if (backToTop) {
    backToTop.classList.toggle('show', window.scrollY > 400);
  }
});
