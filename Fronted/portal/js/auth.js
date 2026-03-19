// auth.js - Handles Admin Authentication

const BASE_URL = '/api';

/**
 * Check if user is authenticated before allowing access to a protected page.
 * If not authenticated, redirects to login.html.
 */
function requireAuth() {
    const token = localStorage.getItem('adminToken');
    const path = window.location.pathname;
    const isLoginPage = path.endsWith('login.html');

    if (!token && !isLoginPage) {
        // Redirect to login if on a protected page without a token
        window.location.href = 'login.html';
        return false;
    } 
    
    if (token && isLoginPage) {
        // Redirect to dashboard if on login page but already logged in
        window.location.href = 'index.html';
        return true;
    }

    return !!token || isLoginPage;
}

/**
 * Handle Login Form Submission
 */
async function handleLogin(e) {
    e.preventDefault();

    const usernameInput = document.getElementById('username').value;
    const passwordInput = document.getElementById('password').value;
    const errorDiv = document.getElementById('login-error');
    const loginBtn = document.getElementById('login-btn');
    const btnText = loginBtn.querySelector('span');
    const btnIcon = loginBtn.querySelector('i');

    // Reset error
    errorDiv.style.display = 'none';

    // UI Loading state
    btnText.innerText = 'Authenticating...';
    btnIcon.className = 'fas fa-spinner fa-spin';
    loginBtn.disabled = true;

    try {
        const response = await fetch(`${BASE_URL}/admin/login/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: usernameInput,
                password: passwordInput
            })
        });

        const data = await response.json();

        if (response.ok && data.token) {
            // Success
            localStorage.setItem('adminToken', data.token);
            window.location.href = 'index.html';
        } else {
            // Failure
            errorDiv.innerText = data.non_field_errors || 'Invalid username or password.';
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        console.error('Login Error:', error);
        errorDiv.innerText = 'Connection error. Please try again.';
        errorDiv.style.display = 'block';
    } finally {
        // Reset UI
        btnText.innerText = 'Login';
        btnIcon.className = 'fas fa-arrow-right';
        loginBtn.disabled = false;
    }
}

/**
 * Logout user
 */
function logout(message = null) {
    localStorage.removeItem('adminToken');
    if (message) {
        alert(message);
    }
    window.location.href = 'login.html';
}

/**
 * Get the standardized headers for authenticated API requests
 */
function getAuthHeaders() {
    const token = localStorage.getItem('adminToken');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Token ${token}`
    };
}

// Global Initialization
(function init() {
    // 1. Run immediate auth check
    const authorized = requireAuth();

    // 2. Setup UI handling
    document.addEventListener('DOMContentLoaded', () => {
        // Show body if authorized or on login page
        if (authorized || window.location.pathname.endsWith('login.html')) {
            document.body.style.display = '';
        }

        // Attach login form handler
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', handleLogin);
        }

        // Attach logout handler
        document.querySelectorAll('.logout-btn').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                logout();
            });
        });
    });
})();
