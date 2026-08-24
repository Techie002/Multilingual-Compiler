/* Chart.js Initialization for Faculty Dashboard Analytics */

document.addEventListener('DOMContentLoaded', async () => {
    const analyticsCanvas = document.getElementById('language-pie-chart');
    if (!analyticsCanvas) return;

    try {
        const response = await fetch('/api/analytics');
        const result = await response.json();

        if (result.success) {
            const data = result.data;

            // 1. Language Usage Pie Chart
            const langCtx = document.getElementById('language-pie-chart').getContext('2d');
            new Chart(langCtx, {
                type: 'pie',
                data: {
                    labels: Object.keys(data.language_usage),
                    datasets: [{
                        data: Object.values(data.language_usage),
                        backgroundColor: ['#6366f1', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4']
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'bottom', labels: { color: '#f8fafc' } }
                    }
                }
            });

            // 2. Score Distribution Bar Chart
            const scoreCtx = document.getElementById('score-bar-chart').getContext('2d');
            new Chart(scoreCtx, {
                type: 'bar',
                data: {
                    labels: Object.keys(data.score_distribution),
                    datasets: [{
                        label: 'Number of Students',
                        data: Object.values(data.score_distribution),
                        backgroundColor: ['#10b981', '#f59e0b', '#f43f5e']
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        x: { ticks: { color: '#94a3b8' } },
                        y: { ticks: { color: '#94a3b8' }, beginAtZero: true }
                    },
                    plugins: {
                        legend: { labels: { color: '#f8fafc' } }
                    }
                }
            });
        }
    } catch (err) {
        console.error("Error loading analytics charts:", err);
    }
});
