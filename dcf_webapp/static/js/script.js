// DOM Elements
const dcfForm = document.getElementById('dcfForm');
const calculateBtn = document.getElementById('calculateBtn');
const resultsSection = document.getElementById('resultsSection');
const errorMessage = document.getElementById('errorMessage');
const logsModal = document.getElementById('logsModal');
const viewLogsBtn = document.getElementById('viewLogsBtn');
const closeModal = document.getElementById('closeModal');

let calculationLogs = '';

// Format currency
function formatCurrency(value) {
    if (value >= 1e12) {
        return `$${(value / 1e12).toFixed(2)}T`;
    } else if (value >= 1e9) {
        return `$${(value / 1e9).toFixed(2)}B`;
    } else if (value >= 1e6) {
        return `$${(value / 1e6).toFixed(2)}M`;
    } else if (value >= 1e3) {
        return `$${(value / 1e3).toFixed(2)}K`;
    }
    return `$${value.toFixed(2)}`;
}

// Format number
function formatNumber(value) {
    if (value >= 1e9) {
        return `${(value / 1e9).toFixed(2)}B`;
    } else if (value >= 1e6) {
        return `${(value / 1e6).toFixed(2)}M`;
    } else if (value >= 1e3) {
        return `${(value / 1e3).toFixed(2)}K`;
    }
    return value.toFixed(2);
}

// Show error
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    setTimeout(() => {
        errorMessage.style.display = 'none';
    }, 5000);
}

// Display results
function displayResults(data) {
    // Calculate upside/downside
    const upside = ((data.target_price - data.current_price) / data.current_price) * 100;
    const upsideColor = upside >= 0 ? '#06d6a0' : '#e63946';
    
    // Update main metrics
    document.getElementById('targetPrice').textContent = `$${data.target_price.toFixed(2)}`;
    document.getElementById('currentPrice').textContent = `$${data.current_price.toFixed(2)}`;
    document.getElementById('upside').textContent = `${upside >= 0 ? '+' : ''}${upside.toFixed(2)}%`;
    document.getElementById('upside').style.color = upsideColor;
    
    // Update company metrics
    document.getElementById('wacc').textContent = `${data.wacc}%`;
    document.getElementById('marketCap').textContent = formatCurrency(data.company_data.market_cap);
    document.getElementById('beta').textContent = data.company_data.beta.toFixed(2);
    document.getElementById('shares').textContent = formatNumber(data.company_data.shares_outstanding);
    
    // Build projections table
    buildProjectionsTable(data.projections);
    
    // Store logs
    calculationLogs = data.calculation_logs;
    
    // Show results section with animation
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Build projections table
function buildProjectionsTable(projections) {
    const table = document.createElement('table');
    
    // Header
    const thead = document.createElement('thead');
    thead.innerHTML = `
        <tr>
            <th>Year</th>
            <th>Revenue</th>
            <th>EBIT</th>
            <th>UFCF</th>
        </tr>
    `;
    table.appendChild(thead);
    
    // Body
    const tbody = document.createElement('tbody');
    projections.forEach(proj => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>Year ${proj.Year}</td>
            <td>${formatCurrency(proj.Revenue)}</td>
            <td>${formatCurrency(proj.EBIT)}</td>
            <td>${formatCurrency(proj.UFCF)}</td>
        `;
        tbody.appendChild(row);
    });
    table.appendChild(tbody);
    
    // Replace existing table
    const projectionsTable = document.getElementById('projectionsTable');
    projectionsTable.innerHTML = '';
    projectionsTable.appendChild(table);
}

// Handle form submission
dcfForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Get form data
    const formData = new FormData(dcfForm);
    const ticker = formData.get('ticker').toUpperCase();
    
    // Collect growth rates
    const growthRates = [];
    for (let i = 1; i <= 5; i++) {
        const rate = parseFloat(formData.get(`growth_${i}`));
        if (isNaN(rate)) {
            showError(`Invalid growth rate for Year ${i}`);
            return;
        }
        growthRates.push(rate);
    }
    
    const terminalGrowth = parseFloat(formData.get('terminal_growth'));
    if (isNaN(terminalGrowth)) {
        showError('Invalid terminal growth rate');
        return;
    }
    
    // Prepare request
    const requestData = {
        ticker: ticker,
        growth_rates: growthRates,
        terminal_growth: terminalGrowth
    };
    
    // Show loading state
    const btnText = calculateBtn.querySelector('.btn-text');
    const btnLoader = calculateBtn.querySelector('.btn-loader');
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline-block';
    calculateBtn.disabled = true;
    
    // Hide previous results and errors
    resultsSection.style.display = 'none';
    errorMessage.style.display = 'none';
    
    try {
        const response = await fetch('/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            displayResults(data);
        } else {
            showError(data.error || 'Calculation failed. Please try again.');
        }
    } catch (error) {
        showError('Network error. Please check your connection and try again.');
        console.error('Error:', error);
    } finally {
        // Reset button state
        btnText.style.display = 'inline-block';
        btnLoader.style.display = 'none';
        calculateBtn.disabled = false;
    }
});

// Modal controls
viewLogsBtn.addEventListener('click', () => {
    document.getElementById('calculationLogs').textContent = calculationLogs;
    logsModal.style.display = 'flex';
});

closeModal.addEventListener('click', () => {
    logsModal.style.display = 'none';
});

// Close modal on outside click
logsModal.addEventListener('click', (e) => {
    if (e.target === logsModal) {
        logsModal.style.display = 'none';
    }
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && logsModal.style.display === 'flex') {
        logsModal.style.display = 'none';
    }
});
