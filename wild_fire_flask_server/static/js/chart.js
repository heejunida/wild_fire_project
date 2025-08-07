let distanceChartInstance = null;

/**
 * Creates or updates the distance chart.
 * @param {object} chartData - Data for the chart.
 */
function createDistanceChart(chartData) {
    const ctx = document.getElementById('distanceChart').getContext('2d');
    if (distanceChartInstance) {
        distanceChartInstance.destroy();
    }
    distanceChartInstance = new Chart(ctx, {
        type: 'line',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: '거리 (km)'
                    }
                }
            }
        }
    });
}