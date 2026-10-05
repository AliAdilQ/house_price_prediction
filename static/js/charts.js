"use strict";

const chartElement = document.getElementById("locationChart");
const chartDataElement = document.getElementById("chart-data");
if (chartElement && chartDataElement) {
  const data = JSON.parse(chartDataElement.textContent);
  const currency = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0
  });
  const tableBody = document.getElementById("chartTableBody");
  data.labels.forEach((label, index) => {
    const row = document.createElement("tr");
    [label, currency.format(data.values[index])].forEach((value) => {
      const cell = document.createElement("td");
      cell.textContent = value;
      row.appendChild(cell);
    });
    tableBody.appendChild(row);
  });
  if (typeof Chart !== "undefined") {
    new Chart(chartElement, {
      type: "bar",
      data: {
        labels: data.labels,
        datasets: [{
          label: "Average estimated value",
          data: data.values,
          backgroundColor: ["#245c4c", "#56806a", "#93a993", "#b8c2a9", "#c19a78", "#dfc6ab"],
          borderRadius: 5,
          maxBarThickness: 46
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 650
        },
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: "#163e35",
            padding: 12,
            callbacks: {
              label: (context) => currency.format(context.parsed.y)
            }
          }
        },
        scales: {
          x: {
            grid: {
              display: false
            },
            border: {
              display: false
            },
            ticks: {
              color: "#66736c",
              font: {
                size: 11
              }
            }
          },
          y: {
            beginAtZero: true,
            border: {
              display: false
            },
            grid: {
              color: "#eeeee7"
            },
            ticks: {
              color: "#66736c",
              maxTicksLimit: 5,
              callback: (value) => `$${Math.round(value / 1000)}k`
            }
          }
        }
      }
    });
  }
}
