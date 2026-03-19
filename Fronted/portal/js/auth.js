// auth.js - Handles Admin Authentication

const BASE_URL = '/api';

/**
 * Check if user is authenticated before allowing access to a protected page.
 * If not authenticated, redirects to login.html.
 */
function requireAuth() {
    const token = localStorage.getItem('adminToken');
    const isLoginPage = window.location.pathname.endsWith('login.html');

    if (!token && !isLoginPage) {
        // Redirect to login if on a protected page without a token
        window.location.href = 'login.html';
    } else if (token && isLoginPage) {
        // Redirect to dashboard if on login page but already explicitly logged in
        window.location.href = 'index.html';
    }
}

// 1. Immediately check authentication status
requireAuth();

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
            headers: {
                'Content-Type': 'application/json',
            },
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
            errorDiv.innerText = 'Invalid username or password.';
            errorDiv.style.display = 'block';
            throw new Error('Authentication failed');
        }
    } catch (error) {
        console.error('Login Error:', error);
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
function logout(e) {
    if (e) e.preventDefault();
    localStorage.removeItem('adminToken');
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

// Get the standardized headers for authenticated API requests
document.addEventListener('DOMContentLoaded', () => {
    // 2. Attach login form handler if on login page
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    // 3. Attach logout handler to any element with class="logout-btn"
    document.querySelectorAll('.logout-btn').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    });
});
