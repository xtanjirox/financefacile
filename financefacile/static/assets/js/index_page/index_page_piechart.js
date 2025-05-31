document.addEventListener('DOMContentLoaded', function () {
    // Get the currency symbol from the server
    const currencySymbol = '{{ currency_symbol }}';

    // Common colors for all charts
    const chartColors = [
        '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b',
        '#6f42c1', '#20c9a6', '#27a9e3', '#fd7e14', '#6c757d'
    ];

    // Common options for all pie charts
    const commonOptions = {
        chart: {
            type: 'donut',
            fontFamily: 'Nunito, sans-serif',
            toolbar: {
                show: false
            },
            animations: {
                enabled: true,
                easing: 'easeinout',
                speed: 800
            }
        },
        legend: {
            position: 'bottom',
            horizontalAlign: 'center',
            fontSize: '12px',
            markers: {
                width: 10,
                height: 10,
                radius: 2
            },
            itemMargin: {
                horizontal: 5,
                vertical: 5
            }
        },
        tooltip: {
            enabled: true,
            style: {
                fontSize: '12px'
            },
            y: {
                formatter: function (value) {
                    return value;
                }
            }
        },
        stroke: {
            width: 2,
            colors: ['#fff']
        },
        dataLabels: {
            enabled: false
        },
        colors: chartColors,
        plotOptions: {
            pie: {
                donut: {
                    size: '60%',
                    labels: {
                        show: true,
                        name: {
                            show: true,
                            fontSize: '16px',
                            fontWeight: 600
                        },
                        value: {
                            show: true,
                            fontSize: '14px',
                            fontWeight: 400,
                            formatter: function (val) {
                                return val;
                            }
                        },
                        total: {
                            show: true,
                            fontSize: '14px',
                            fontWeight: 600,
                            label: 'Total',
                            formatter: function (w) {
                                return w.globals.seriesTotals.reduce((a, b) => a + b, 0);
                            }
                        }
                    }
                }
            }
        },
        responsive: [{
            breakpoint: 480,
            options: {
                chart: {
                    height: 250
                },
                legend: {
                    position: 'bottom'
                }
            }
        }]
    };

    // Initialize charts if elements exist
    const initCharts = () => {
        // Revenue Forecast Chart
        const revenueForecastEl = document.getElementById('revenue-forecast');
        if (revenueForecastEl) {
            const revenueForecastOptions = {
                series: [
                    {
                        name: "{{ current_year }}",
                        data: {{ monthly_revenue_current_year|default: '[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]' | safe
            }
        }
    },
        {
            name: "{{ previous_year }}",
            data: {{ monthly_revenue_previous_year|default: '[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]' | safe
}}
                        }
                    ],
    chart: {
    type: "bar",
    height: 270,
    stacked: true,
    toolbar: {
        show: false
    },
    fontFamily: "inherit",
    foreColor: "#adb0bb"
},
    colors: ["#4DB6AC", "#F06292"],
    plotOptions: {
    bar: {
        horizontal: false,
        columnWidth: "25%",
        borderRadius: 6,
        borderRadiusApplication: "end",
        borderRadiusWhenStacked: "all"
    }
},
    dataLabels: {
    enabled: false
},
    legend: {
    show: true,
    position: 'top',
    horizontalAlign: 'right'
},
    grid: {
    show: true,
    borderColor: "rgba(0,0,0,0.05)"
},
    xaxis: {
    categories: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    labels: {
        style: { fontSize: "13px", colors: "#adb0bb" }
    }
},
    yaxis: {
    labels: {
        formatter: function (value) {
            return currencySymbol + ' ' + value.toLocaleString();
        }
    }
},
    tooltip: {
    theme: "light",
    y: {
        formatter: function (value) {
            return currencySymbol + ' ' + value.toLocaleString();
        }
    }
}
                };

const revenueForecastChart = new ApexCharts(revenueForecastEl, revenueForecastOptions);
revenueForecastChart.render();

// Handle period change
const periodSelector = document.getElementById('revenue-forecast-period');
if (periodSelector) {
    periodSelector.addEventListener('change', function () {
        // In a real implementation, you would fetch new data based on the selected period
        // For now, we'll just show a message
        console.log('Period changed to: ' + this.value);
    });
}
            }

// Pie Chart: Products by Parent Category
const productsEl = document.getElementById('chart-products-category');
if (productsEl) {
    const pieProductsData = JSON.parse('{{ pie_products_by_category|escapejs }}');
    const productSeries = pieProductsData.datasets[0].data;
    const productLabels = pieProductsData.labels;

    const productsOptions = {
        ...commonOptions,
        series: productSeries,
        labels: productLabels,
        title: {
            text: 'Articles par catégorie',
            align: 'center',
            style: {
                fontSize: '14px',
                fontWeight: 500,
                color: '#666'
            }
        }
    };

    const productsChart = new ApexCharts(productsEl, productsOptions);
    productsChart.render();
}

// Pie Chart: Inventory Value by Parent Category
const valueEl = document.getElementById('chart-value-category');
if (valueEl) {
    const pieValueData = JSON.parse('{{ pie_value_by_category|escapejs }}');
    const valueSeries = pieValueData.datasets[0].data;
    const valueLabels = pieValueData.labels;

    const valueOptions = {
        ...commonOptions,
        series: valueSeries,
        labels: valueLabels,
        title: {
            text: 'Valeur du stock',
            align: 'center',
            style: {
                fontSize: '14px',
                fontWeight: 500,
                color: '#666'
            }
        },
        tooltip: {
            y: {
                formatter: function (value) {
                    return currencySymbol + ' ' + value.toLocaleString();
                }
            }
        },
        plotOptions: {
            pie: {
                donut: {
                    labels: {
                        value: {
                            formatter: function (val) {
                                return currencySymbol + ' ' + parseFloat(val).toLocaleString();
                            }
                        },
                        total: {
                            formatter: function (w) {
                                const total = w.globals.seriesTotals.reduce((a, b) => a + b, 0);
                                return currencySymbol + ' ' + total.toLocaleString();
                            }
                        }
                    }
                }
            }
        }
    };

    const valueChart = new ApexCharts(valueEl, valueOptions);
    valueChart.render();
}

// Pie Chart: Invoices by Parent Category (sold products)
const invoiceEl = document.getElementById('chart-invoice-category');
if (invoiceEl) {
    const pieInvoiceData = JSON.parse('{{ pie_invoice_by_category|escapejs }}');
    const invoiceSeries = pieInvoiceData.datasets[0].data;
    const invoiceLabels = pieInvoiceData.labels;

    const invoiceOptions = {
        ...commonOptions,
        series: invoiceSeries,
        labels: invoiceLabels,
        title: {
            text: 'Factures par catégorie',
            align: 'center',
            style: {
                fontSize: '14px',
                fontWeight: 500,
                color: '#666'
            }
        },
        tooltip: {
            y: {
                formatter: function (value) {
                    return currencySymbol + ' ' + value.toLocaleString();
                }
            }
        },
        plotOptions: {
            pie: {
                donut: {
                    labels: {
                        value: {
                            formatter: function (val) {
                                return currencySymbol + ' ' + parseFloat(val).toLocaleString();
                            }
                        },
                        total: {
                            formatter: function (w) {
                                const total = w.globals.seriesTotals.reduce((a, b) => a + b, 0);
                                return currencySymbol + ' ' + total.toLocaleString();
                            }
                        }
                    }
                }
            }
        }
    };

    const invoiceChart = new ApexCharts(invoiceEl, invoiceOptions);
    invoiceChart.render();
}
        };

// Initialize charts
initCharts();
    });
