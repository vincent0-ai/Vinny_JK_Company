document.addEventListener('DOMContentLoaded', () => {
    fetchDashboardStats();
});

async function fetchDashboardStats() {
    try {
        const response = await fetch('/api/admin/dashboard-stats/', {
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            if (response.status === 401 || response.status === 403) logout();
            throw new Error('Failed to fetch dashboard stats');
        }

        const data = await response.json();

        // Update Text Stats
        document.getElementById('total-revenue').innerText = `KES ${data.total_revenue.toLocaleString()}`;
        document.getElementById('total-orders').innerText = data.total_orders;
        document.getElementById('total-bookings').innerText = data.pending_bookings;
        document.getElementById('low-stock').innerText = data.low_stock_count;

        // Init Charts with Real Data
        initRevenueChart(data.revenue_trends);
        initBookingChart(data.booking_status_distribution);

    } catch (error) {
        console.error('Error fetching stats:', error);
        mockStats();
        // Fallback charts with mock data
        initRevenueChart({ labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], data: [0, 0, 0, 0, 0, 0, 0] });
        initBookingChart({ 'Pending': 0, 'Confirmed': 0, 'Completed': 0, 'Cancelled': 0 });
    }
}

function mockStats() {
    document.getElementById('total-revenue').innerText = "KES 0";
    document.getElementById('total-orders').innerText = "0";
    document.getElementById('total-bookings').innerText = "0";
    document.getElementById('low-stock').innerText = "0";
}

function initRevenueChart(revenueData) {
    const ctx = document.getElementById('revenueChart').getContext('2d');
    
    // Destroy existing chart if it exists to avoid overlaps on refresh
    const existingChart = Chart.getChart("revenueChart");
    if (existingChart) existingChart.destroy();

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: revenueData.labels,
            datasets: [{
                label: 'Revenue (KES)',
                data: revenueData.data,
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
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true },
                x: { grid: { display: false } }
            }
        }
    });
}

function initBookingChart(bookingDist) {
    const ctx = document.getElementById('bookingChart').getContext('2d');

    const existingChart = Chart.getChart("bookingChart");
    if (existingChart) existingChart.destroy();

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(bookingDist),
            datasets: [{
                data: Object.values(bookingDist),
                backgroundColor: ['#ffc107', '#17a2b8', '#28a745', '#dc3545'],
                borderWidth: 0,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            cutout: '70%',
            plugins: {
                legend: { position: 'bottom', labels: { boxWidth: 12, padding: 15 } }
            }
        }
    });
}
