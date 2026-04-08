document.addEventListener("DOMContentLoaded", () => {
    // UI Elements
    const btnLoadSample = document.getElementById("btn-load-sample");
    const form = document.getElementById("analysis-form");
    const btnAnalyze = document.getElementById("btn-analyze");
    const btnText = btnAnalyze.querySelector(".btn-text");
    const loader = btnAnalyze.querySelector(".loader");
    
    const emptyState = document.getElementById("empty-state");
    const resultsContent = document.getElementById("results-content");
    
    // Output Elements
    const outCompany = document.getElementById("report-company");
    const outTicker = document.getElementById("report-ticker");
    const outVerdictBanner = document.getElementById("verdict-banner");
    const patternDiagnosis = document.getElementById("pattern-diagnosis");
    const analystVerdict = document.getElementById("analyst-verdict");
    const tableHeadRow = document.getElementById("table-head-row");
    const tableBody = document.getElementById("table-body");
    const flagsContainer = document.getElementById("flags-container");

    // Sample Data
    const SAMPLE_COMPANY = {
        "company_name": "Apex Fintech",
        "sector": "Financial Services",
        "ticker": "APEX"
    };

    const HISTORICAL_DATA = [
        {"year": "2018", "revenue": 70.0, "ebitda": 15.0, "net_income": 8.0, "cash": 30.0, "debt": 40.0},
        {"year": "2019", "revenue": 85.0, "ebitda": 20.0, "net_income": 12.0, "cash": 40.0, "debt": 60.0},
        {"year": "2020", "revenue": 100.0, "ebitda": 25.0, "net_income": 15.0, "cash": 50.0, "debt": 100.0},
        {"year": "2021", "revenue": 125.0, "ebitda": 30.0, "net_income": 18.0, "cash": 55.0, "debt": 125.0},
        {"year": "2022", "revenue": 160.0, "ebitda": 35.0, "net_income": 19.0, "cash": 45.0, "debt": 250.0},
        {"year": "2023", "revenue": 210.0, "ebitda": 42.0, "net_income": 20.0, "cash": 40.0, "debt": 400.0},
        {"year": "2024", "revenue": 280.0, "ebitda": 50.0, "net_income": 22.0, "cash": 35.0, "debt": 650.0}
    ];

    // Handlers
    btnLoadSample.addEventListener("click", () => {
        document.getElementById("company-name").value = SAMPLE_COMPANY.company_name;
        document.getElementById("company-sector").value = SAMPLE_COMPANY.sector;
        document.getElementById("company-ticker").value = SAMPLE_COMPANY.ticker;
        document.getElementById("historical-data").value = JSON.stringify(HISTORICAL_DATA, null, 2);
    });

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const companyName = document.getElementById("company-name").value;
        const companySector = document.getElementById("company-sector").value;
        const companyTicker = document.getElementById("company-ticker").value;
        let historicalDataStr = document.getElementById("historical-data").value;
        
        let historicalData;
        try {
            historicalData = JSON.parse(historicalDataStr);
        } catch (err) {
            alert("Invalid JSON format in Historical Data field.");
            return;
        }

        const payload = {
            company: {
                company_name: companyName,
                sector: companySector,
                ticker: companyTicker
            },
            historical_data: historicalData
        };

        // Loading State
        btnAnalyze.disabled = true;
        btnText.classList.add("hidden");
        loader.classList.remove("hidden");
        
        try {
            const response = await fetch("/api/analyze", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-API-Key": "dev_default_key" // Standardizing dev key
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || "Failed to analyze data");
            }

            renderResults(data, payload);
            
        } catch (error) {
            alert(`Error: ${error.message}`);
        } finally {
            // Revert Loading State
            btnAnalyze.disabled = false;
            btnText.classList.remove("hidden");
            loader.classList.add("hidden");
        }
    });

    function renderResults(data, requestPayload) {
        // Toggle view
        emptyState.classList.add("hidden");
        resultsContent.classList.remove("hidden");

        // Header
        outCompany.textContent = requestPayload.company.company_name.toUpperCase();
        outTicker.textContent = requestPayload.company.ticker;
        
        const archetype = data.analyst_verdict.archetype || "UNKNOWN";
        outVerdictBanner.textContent = archetype;
        
        outVerdictBanner.className = "report-verdict-banner"; // reset
        if (["COMPOUNDER", "EARLY STAGE"].includes(archetype)) {
            outVerdictBanner.classList.add("verdict-good");
        } else if (["VALUE TRAP", "MELTING ICE CUBE", "DEBT SPIRAL"].some(a => archetype.includes(a))) {
            outVerdictBanner.classList.add("verdict-bad");
        } else {
            outVerdictBanner.classList.add("verdict-neutral");
        }

        // Table
        renderTable(data.calculated_metrics);

        // Text Analysis
        patternDiagnosis.textContent = data.pattern_diagnosis || "No diagnosis available.";
        analystVerdict.textContent = data.analyst_verdict.summary || "No verdict available.";

        // Flags
        flagsContainer.innerHTML = "";
        const flags = data.flags || [];
        if (flags.length === 0) {
            flagsContainer.innerHTML = "<p>No critical flags triggered.</p>";
        } else {
            flags.forEach(flag => {
                const card = document.createElement("div");
                card.className = "flag-card";
                card.innerHTML = `
                    <div class="flag-card-header">
                        <span>${flag.emoji || "⚠️"}</span>
                        <span>${flag.name}</span>
                    </div>
                    <p>${flag.explanation}</p>
                `;
                flagsContainer.appendChild(card);
            });
        }
    }

    function renderTable(metrics) {
        if (!metrics || !metrics.yearly) return;
        
        const years = metrics.yearly;
        
        // Build Header
        let thHTML = "<th>Metric</th>";
        years.forEach(y => { thHTML += `<th>${y.year}</th>`; });
        thHTML += "<th>Trend</th><th>Signal</th>";
        tableHeadRow.innerHTML = thHTML;

        // Build Rows
        let tbodyHTML = "";

        // Revenue Row
        tbodyHTML += `<tr><td>Revenue ($M)</td>`;
        years.forEach(y => { tbodyHTML += `<td>${y.revenue}</td>`; });
        tbodyHTML += `<td>${metrics.revenue_cagr_pct}% CAGR</td><td><b>${metrics.revenue_trajectory}</b></td></tr>`;

        // EBITDA Margin Row
        tbodyHTML += `<tr><td>EBITDA Margin %</td>`;
        years.forEach(y => { tbodyHTML += `<td>${y.ebitda_margin}%</td>`; });
        tbodyHTML += `<td>STABLE</td><td><b>${metrics.margin_signal}</b></td></tr>`;

        // Leverage Row
        tbodyHTML += `<tr><td>Debt / EBITDA</td>`;
        years.forEach(y => { tbodyHTML += `<td>${y.leverage}x</td>`; });
        tbodyHTML += `<td>RISING</td><td><b>${metrics.debt_signal}</b></td></tr>`;

        tableBody.innerHTML = tbodyHTML;
    }
});
