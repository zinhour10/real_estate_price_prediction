let radarChart;  // keep reference for later update

// Function to update chart with new data
function updateRadarChart(yourData, averageData) {
    // Map your keys to radarData labels, make sure keys match your labels
    const labels = radarData.labels;

    // Extract data for your house and area average from yourData and averageData
    const yourHouseValues = labels.map(label => yourData[label] ?? 0);
    const areaAverageValues = labels.map(label => averageData[label] ?? 0);

    radarChart.data.datasets[0].data = yourHouseValues;
    radarChart.data.datasets[1].data = areaAverageValues;
    radarChart.update();
}

const radarData = {
    labels: ["n_mart_in_1km", "n_hospital_in_1km", "n_resturant_in_1km"],
    datasets: [
        {
            label: "Target House",
            data: [0, 0, 0],  // placeholder
            fill: true,
            backgroundColor: "rgba(54, 162, 235, 0.2)",
            borderColor: "rgb(54, 162, 235)",
            pointBackgroundColor: "rgb(54, 162, 235)"
        },
        {
            label: "Average",
            data: [0, 0, 0],  // placeholder
            fill: true,
            backgroundColor: "rgba(255, 99, 132, 0.2)",
            borderColor: "rgb(255, 99, 132)",
            pointBackgroundColor: "rgb(255, 99, 132)"
        }
    ]
};

const config = {
    type: 'radar',
    data: radarData,
    options: {
        responsive: true,
        plugins: {
            title: {
                display: true,
                text: 'Target vs. Average (1km radius)'
            }
        }
    }
};

window.onload = () => {
    // Initialize chart once DOM is ready
    const ctx = document.getElementById("radarChart").getContext('2d');
    radarChart = new Chart(ctx, config);

    // Fetch nearby properties averages
    fetch("/nearby-properties")
        .then(response => response.json())
        .then(data => {
            const nearbyProperties = data.results.nearby_properties;
            const allKeys = new Set();
            nearbyProperties.forEach(property => {
                Object.keys(property).forEach(key => allKeys.add(key));
            });
            const nearbyKeys = Array.from(allKeys);
            const averages = {};
            nearbyKeys.forEach(key => {
                let sum = 0;
                let count = 0;
                nearbyProperties.forEach(property => {
                    const value = property[key];
                    if (typeof value === 'number') {
                        sum += value;
                        count++;
                    }
                });
                averages[key] = count > 0 ? sum / count : 0;
            });

            // Now fetch your house data
            fetch("/last-prediction")
                .then(response => response.json())
                .then(myHouseData => {
                    // Update chart with your data and area averages
                    updateRadarChart(myHouseData, averages);
                });
        });
};
