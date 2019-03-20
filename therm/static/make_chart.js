function makeChart (element, labels, temp_values, set_points_heaton, set_points_heatoff, y_min, y_max, responsive) {
chart = new Chart(element, {
    type: 'line',

    data: {
      labels: labels,
      datasets: [{
            data: temp_values,
            label: "Temperature",
            borderColor: window.chartColors.green,
            borderWidth: 5,
            fill: false,
            spanGaps: true,
        },
        {label: 'Set point',
        data: set_points_heatoff,
                fill: false,
                backgroundColor: 'rgba(54, 162, 235, .5)',
                borderColor: 'rgba(54, 162, 235, .5)',
                borderWidth: 5,
                spanGaps: false,
        },
        {label: 'Set point',
        data: set_points_heaton,
                fill: true,
                backgroundColor: 'rgba(255, 99, 132, .2)',
                borderColor: 'rgb(255, 99, 132, .5)',
                borderWidth: 5,
                spanGaps: false,
        }
        ]
    },
    options: {
        title: {
          display: false,
        },
        legend: {
            display: false,
        },
        animation: {
            duration: 0
        },
        elements: {
            point:{
                radius: 0
            }
        },
        responsive: responsive,
        maintainAspectRatio: false,
        tooltips: {enabled: false},
        hover: {mode: null},
        scales: {
            yAxes: [{
                display: true,
                ticks: {
                    suggestedMin: y_min,
                    suggestedMax: y_max,
                }
            }],
            xAxes: [{
                display: true,
            }]
        }
    }
});

return chart;
}