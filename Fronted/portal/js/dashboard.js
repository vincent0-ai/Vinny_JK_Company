document.addEventListener('DOMContentLoaded', () => {
    fetchDashboardStats();
    initRevenueChart();
    initBookingChart();
});

async function fetchDashboardStats() {
    try {
        // Placeholder URLs - will implement backend view next
        const response = await fetch('/api/admin/dashboard-stats/');
        const data = await response.json();
        
        document.getElementById('total-revenue').innerText = `KES ${data.total_revenue.toLocaleString()}`;
        document.getElementById('total-orders').innerText = data.total_orders;
        document.getElementById('total-bookings').innerText = data.pending_bookings;
        document.getElementById('low-stock').innerText = data.low_stock_count;
        
    } catch (error) {
        console.error('Error fetching stats:', error);
        // Fallback for demo if API not yet ready
        mockStats();
    }
}

function mockStats() {
    document.getElementById('total-revenue').innerText = "KES 124,500";
    document.getElementById('total-orders').innerText = "18";
    document.getElementById('total-bookings').innerText = "7";
    document.getElementById('low-stock').innerText = "3";
}

function initRevenueChart() {
    const ctx = document.getElementById('revenueChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Revenue (KES)',
                data: [12000, 19000, 15000, 25000, 22000, 30000, 28000],
                borderColor: '#007bff',
                backgroundColor: 'rgba(0, 123, 255, 0.1)',
                tension: 0.4,
                fill: true,
                borderWidth: 3,
                pointRadius: 4,
                pointBackgroundColor: '#007bff'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true },
                x: { grid: { display: false } }
            }
        }
    });
}

function initBookingChart() {
    const ctx = document.getElementById('bookingChart').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Pending', 'Confirmed', 'Completed', 'Cancelled'],
            datasets: [{
                data: [5, 8, 12, 2],
                backgroundColor: ['#ffc107', '#17a2b8', '#28a745', '#dc3545'],
                borderWidth: 0,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            cutout: '70%',
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}
