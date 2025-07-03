let distanceChart = null;
let speedLevelChart = null;

function createDistanceChart(data) {
    const ctx = document.getElementById("distanceChart").getContext("2d");
    if (distanceChart) distanceChart.destroy();

    distanceChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: data.labels,
            datasets: [{
                label: "확산 거리 (km)",
                data: data.values,
                fill: false,
                borderColor: "rgba(75, 192, 192, 1)",
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: "top" },
                title: { display: true, text: "시간별 확산 거리 변화" }
            }
        }
    });
}

function createSpeedLevelChart(data) {
    const ctx = document.getElementById("speedLevelChart").getContext("2d");
    if (speedLevelChart) speedLevelChart.destroy();

    const labels = Object.keys(data);
    const high = labels.map(r => data[r].high);
    const medium = labels.map(r => data[r].medium);
    const low = labels.map(r => data[r].low);

    speedLevelChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels,
            datasets: [
                { label: "높음", data: high, backgroundColor: "rgba(255, 99, 132, 0.6)" },
                { label: "보통", data: medium, backgroundColor: "rgba(255, 159, 64, 0.6)" },
                { label: "낮음", data: low, backgroundColor: "rgba(255, 205, 86, 0.6)" }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                title: { display: true, text: "지역별 확산 속도 등급 분포" },
                legend: { position: "bottom" }
            },
            scales: {
                y: { beginAtZero: true, title: { display: true, text: "격자 수" } },
                x: { title: { display: true, text: "지역" } }
            }
        }
    });
}

function generateMockLineData(region) {
    return {
        labels: ["T+1h", "T+2h", "T+3h", "T+4h", "T+5h"],
        values: Array.from({ length: 5 }, () => (Math.random() * 4 + 1).toFixed(2))
    };
}

function generateMockBarData(regionList) {
    const data = {};
    regionList.forEach(region => {
        data[region] = {
            high: Math.floor(Math.random() * 5 + 3),
            medium: Math.floor(Math.random() * 5 + 2),
            low: Math.floor(Math.random() * 5 + 1)
        };
    });
    return data;
}