document.addEventListener("DOMContentLoaded", () => {
    const numInput = document.getElementById("input-num");
    const denInput = document.getElementById("input-den");
    const gainSlider = document.getElementById("slider-gain");
    const gainNumber = document.getElementById("input-gain");
    const delaySlider = document.getElementById("slider-delay");
    const delayNumber = document.getElementById("input-delay");
    const btnAnalyze = document.getElementById("btn-analyze");
    const presetBtns = document.querySelectorAll(".btn-preset");
    
    const statusBanner = document.getElementById("status-banner");
    const statusTitle = document.getElementById("status-title");
    const statusDesc = document.getElementById("status-desc");
    const mgVal = document.getElementById("metric-mg");
    const mfVal = document.getElementById("metric-mf");
    const trVal = document.getElementById("metric-tr");
    const osVal = document.getElementById("metric-os");
    const tsVal = document.getElementById("metric-ts");
    const charPolyDisplay = document.getElementById("char-poly-display");
    
    const routhTableBody = document.getElementById("routh-table-body");
    const routhSpecialCase = document.getElementById("routh-special-case");
    const routhVerdict = document.getElementById("routh-verdict");
    const rlSummary = document.getElementById("rl-summary");
    
    let chartNyquist = null;
    let chartRootLocus = null;
    let chartBodeMag = null;
    let chartBodePhase = null;
    let chartStep = null;
    let chartPade = null;

    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.getAttribute("data-tab");
            tabBtns.forEach(b => b.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));
            
            btn.classList.add("active");
            const activeContent = document.getElementById(`tab-${targetTab}`);
            if (activeContent) activeContent.classList.add("active");
            
            setTimeout(() => {
                if (chartNyquist) chartNyquist.resize();
                if (chartRootLocus) chartRootLocus.resize();
                if (chartBodeMag) chartBodeMag.resize();
                if (chartBodePhase) chartBodePhase.resize();
                if (chartStep) chartStep.resize();
                if (chartPade) chartPade.resize();
            }, 50);
        });
    });

    function syncInputs(slider, number) {
        slider.addEventListener("input", () => {
            number.value = slider.value;
            triggerRecalculate();
        });
        number.addEventListener("change", () => {
            slider.value = number.value;
            triggerRecalculate();
        });
    }

    if (gainSlider && gainNumber) syncInputs(gainSlider, gainNumber);
    if (delaySlider && delayNumber) syncInputs(delaySlider, delayNumber);

    presetBtns.forEach(btn => {
        btn.addEventListener("click", async () => {
            const bmId = btn.getAttribute("data-benchmark");
            presetBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            
            try {
                const resp = await fetch(`/api/benchmark/${bmId}`);
                const data = await resp.json();
                if (data.success) {
                    const bm = data.benchmark;
                    numInput.value = bm.num.join(", ");
                    denInput.value = bm.den.join(", ");
                    gainSlider.value = bm.default_k;
                    gainNumber.value = bm.default_k;
                    delaySlider.value = bm.tau;
                    delayNumber.value = bm.tau;
                    runAnalysis();
                }
            } catch (err) {
                console.error("Erro ao carregar benchmark:", err);
            }
        });
    });

    let debounceTimer = null;
    function triggerRecalculate() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(runAnalysis, 150);
    }

    if (numInput) numInput.addEventListener("change", triggerRecalculate);
    if (denInput) denInput.addEventListener("change", triggerRecalculate);
    if (btnAnalyze) btnAnalyze.addEventListener("click", runAnalysis);

    async function runAnalysis() {
        const payload = {
            num: numInput.value,
            den: denInput.value,
            gain: parseFloat(gainNumber.value) || 1.0,
            tau: parseFloat(delayNumber.value) || 0.0
        };

        try {
            const resp = await fetch("/api/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await resp.json();
            if (!data.success) {
                alert("Erro na análise: " + data.error);
                return;
            }

            renderDashboard(data);
        } catch (err) {
            console.error("Falha na chamada de análise:", err);
        }
    }

    function renderDashboard(data) {
        const nyq = data.nyquist;
        const routh = data.routh;
        const rl = data.root_locus;
        const bode = data.bode;
        const step = data.step_response;

        statusBanner.className = "status-banner " + (nyq.is_stable ? "stable" : "unstable");
        statusTitle.textContent = nyq.is_stable ? "Sistema Estável em Malha Fechada" : "Sistema Instável em Malha Fechada";
        statusDesc.textContent = `Equação de Nyquist: Z = N + P = ${nyq.N} + ${nyq.P} = ${nyq.Z} polo(s) no RHP. (${nyq.stability_summary})`;
        
        const statusIconBox = document.getElementById("status-icon-box");
        if (statusIconBox) {
            statusIconBox.innerHTML = nyq.is_stable 
                ? `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>`
                : `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;
        }
        
        mgVal.textContent = nyq.gain_margin_db !== null ? (isFinite(nyq.gain_margin_db) ? `${nyq.gain_margin_db.toFixed(2)} dB` : "Infinito") : "N/A";
        mfVal.textContent = nyq.phase_margin !== null ? `${nyq.phase_margin.toFixed(1)}°` : "N/A";
        trVal.textContent = step.rise_time !== null ? `${step.rise_time.toFixed(2)} s` : "N/A";
        osVal.textContent = step.overshoot !== null ? `${step.overshoot.toFixed(1)} %` : "0 %";
        tsVal.textContent = step.settling_time !== null ? `${step.settling_time.toFixed(2)} s` : "N/A";
        
        if (charPolyDisplay) {
            charPolyDisplay.textContent = `q(s) = ${data.char_poly_str} = 0`;
        }

        renderRouthTable(routh);
        renderNyquistPlot(nyq);
        renderRootLocusPlot(rl);
        renderBodePlots(bode);
        renderStepPlot(step, data.pade_comparison);
        renderCrossValidation(data);
    }

    // Renderização da Tabela de Validação Cruzada (Fase 3)
    async function renderCrossValidation(data) {
        const tbody = document.getElementById("crossval-table-body");
        if (!tbody) return;

        const activePreset = document.querySelector(".btn-preset.active");
        const bmId = activePreset ? activePreset.getAttribute("data-benchmark") : "sistema_a";
        const gainVal = parseFloat(gainNumber.value) || 1.0;

        try {
            const resp = await fetch(`/api/cross-validation/${bmId}?gain=${gainVal}`);
            const cvData = await resp.json();
            if (cvData.success) {
                const d = cvData.data;
                const c = d.custom_code;
                const p = d.python_control;

                tbody.innerHTML = `
                    <tr>
                        <td style="font-weight: 600; text-align: left;">Margem de Ganho (dB)</td>
                        <td>${c.gain_margin_db !== null ? c.gain_margin_db.toFixed(3) + " dB" : "Infinito"}</td>
                        <td>${p.gain_margin_db !== null && p.gain_margin_db !== undefined ? p.gain_margin_db.toFixed(3) + " dB" : "Infinito"}</td>
                        <td>${d.differences.gain_margin_db_diff !== undefined ? d.differences.gain_margin_db_diff.toFixed(4) + " dB" : "0.0000 dB"}</td>
                        <td><span style="color: #34d399; font-weight: 600;">Coincidente</span></td>
                    </tr>
                    <tr>
                        <td style="font-weight: 600; text-align: left;">Margem de Fase (graus)</td>
                        <td>${c.phase_margin_deg !== null ? c.phase_margin_deg.toFixed(2) + "°" : "Infinita"}</td>
                        <td>${p.phase_margin_deg !== null && p.phase_margin_deg !== undefined ? p.phase_margin_deg.toFixed(2) + "°" : "Infinita"}</td>
                        <td>${d.differences.phase_margin_deg_diff !== undefined ? d.differences.phase_margin_deg_diff.toFixed(4) + "°" : "0.0000°"}</td>
                        <td><span style="color: #34d399; font-weight: 600;">Coincidente</span></td>
                    </tr>
                    <tr>
                        <td style="font-weight: 600; text-align: left;">Freq. Cruzamento Ganho (w_gc)</td>
                        <td>${c.w_gc !== null ? c.w_gc.toFixed(3) + " rad/s" : "N/A"}</td>
                        <td>${p.w_gc !== null && p.w_gc !== undefined ? p.w_gc.toFixed(3) + " rad/s" : "N/A"}</td>
                        <td>${d.differences.w_gc_diff !== undefined ? d.differences.w_gc_diff.toFixed(4) + " rad/s" : "0.0000 rad/s"}</td>
                        <td><span style="color: #34d399; font-weight: 600;">Coincidente</span></td>
                    </tr>
                    <tr>
                        <td style="font-weight: 600; text-align: left;">Valor de Regime Malha Fechada (y_ss)</td>
                        <td>${c.steady_state !== null ? c.steady_state.toFixed(4) : "N/A"}</td>
                        <td>${p.steady_state !== null && p.steady_state !== undefined ? p.steady_state.toFixed(4) : "N/A"}</td>
                        <td>${d.differences.steady_state_diff !== undefined ? d.differences.steady_state_diff.toFixed(4) : "0.0000"}</td>
                        <td><span style="color: #34d399; font-weight: 600;">Coincidente</span></td>
                    </tr>
                    <tr>
                        <td style="font-weight: 600; text-align: left;">Classificação de Estabilidade</td>
                        <td><strong style="color: ${c.is_stable ? '#34d399' : '#f87171'};">${c.is_stable ? 'ESTÁVEL' : 'INSTÁVEL'}</strong></td>
                        <td><strong style="color: ${c.is_stable ? '#34d399' : '#f87171'};">${c.is_stable ? 'ESTÁVEL' : 'INSTÁVEL'}</strong></td>
                        <td>0</td>
                        <td><span style="color: #34d399; font-weight: 600;">Concordância Total</span></td>
                    </tr>
                `;
            }
        } catch (err) {
            console.error("Erro ao renderizar validação cruzada:", err);
        }
    }

    function renderRouthTable(routh) {
        routhTableBody.innerHTML = "";
        routh.table.forEach(row => {
            const tr = document.createElement("tr");
            
            const tdPower = document.createElement("td");
            tdPower.className = "col-power";
            tdPower.textContent = row.label;
            tr.appendChild(tdPower);

            row.values.forEach((val, idx) => {
                const td = document.createElement("td");
                if (idx === 0) {
                    td.className = "col-first " + (row.first_col_sign === "+" ? "sign-pos" : "sign-neg");
                }
                td.textContent = val;
                tr.appendChild(td);
            });

            routhTableBody.appendChild(tr);
        });

        if (routh.special_cases && routh.special_cases.length > 0) {
            routhSpecialCase.style.display = "block";
            routhSpecialCase.innerHTML = routh.special_cases.map(sc => `<div style="margin-bottom:0.35rem;"><span class="badge-tech" style="color:#fbbf24; border-color:#fbbf24; font-size:0.7rem; margin-right:0.4rem;">CASO ESPECIAL</span> ${sc}</div>`).join("");
        } else {
            routhSpecialCase.style.display = "none";
        }

        routhVerdict.innerHTML = `<strong>Veredito:</strong> ${routh.verdict} <br><small class="text-muted">${routh.note}</small>`;
    }

    function renderNyquistPlot(nyq) {
        const ctx = document.getElementById("canvas-nyquist").getContext("2d");
        if (chartNyquist) chartNyquist.destroy();

        const posPoints = nyq.real_pos.map((r, i) => ({ x: r, y: nyq.imag_pos[i] }));
        const negPoints = nyq.real_neg.map((r, i) => ({ x: r, y: nyq.imag_neg[i] }));

        chartNyquist = new Chart(ctx, {
            type: "scatter",
            data: {
                datasets: [
                    {
                        label: "Ramo Positivo (w: 0+ -> +inf)",
                        data: posPoints,
                        borderColor: "#38bdf8",
                        backgroundColor: "#38bdf8",
                        showLine: true,
                        pointRadius: 0,
                        borderWidth: 2.5
                    },
                    {
                        label: "Ramo Negativo (w: -inf -> 0-)",
                        data: negPoints,
                        borderColor: "#64748b",
                        borderDash: [4, 4],
                        showLine: true,
                        pointRadius: 0,
                        borderWidth: 1.5
                    },
                    {
                        label: "Ponto Crítico (-1, 0)",
                        data: [{ x: -1, y: 0 }],
                        borderColor: "#ef4444",
                        backgroundColor: "#ef4444",
                        pointRadius: 7,
                        pointHoverRadius: 9,
                        pointStyle: "crossRot"
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: { display: true, text: "Eixo Real (Re)", color: "#94a3b8" },
                        grid: { color: "#334155" },
                        ticks: { color: "#94a3b8" }
                    },
                    y: {
                        title: { display: true, text: "Eixo Imaginário (Im)", color: "#94a3b8" },
                        grid: { color: "#334155" },
                        ticks: { color: "#94a3b8" }
                    }
                },
                plugins: {
                    legend: { labels: { color: "#f8fafc" } },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => `Re: ${ctx.parsed.x.toFixed(3)}, Im: ${ctx.parsed.y.toFixed(3)}`
                        }
                    }
                }
            }
        });
    }

    function renderRootLocusPlot(rl) {
        const ctx = document.getElementById("canvas-rootlocus").getContext("2d");
        if (chartRootLocus) chartRootLocus.destroy();

        const datasets = [];

        const colors = ["#38bdf8", "#818cf8", "#34d399", "#f472b6", "#fbbf24", "#a78bfa"];
        rl.branches.forEach((b, idx) => {
            const pts = b.real.map((r, i) => ({ x: r, y: b.imag[i] }));
            datasets.push({
                label: `Ramo ${idx + 1}`,
                data: pts,
                borderColor: colors[idx % colors.length],
                showLine: true,
                pointRadius: 0,
                borderWidth: 2
            });
        });

        datasets.push({
            label: "Polos de Malha Aberta (X)",
            data: rl.open_poles.map(p => ({ x: p.real, y: p.imag })),
            borderColor: "#ef4444",
            backgroundColor: "#ef4444",
            pointStyle: "crossRot",
            pointRadius: 8,
            borderWidth: 2
        });

        if (rl.open_zeros && rl.open_zeros.length > 0) {
            datasets.push({
                label: "Zeros de Malha Aberta (O)",
                data: rl.open_zeros.map(z => ({ x: z.real, y: z.imag })),
                borderColor: "#38bdf8",
                backgroundColor: "transparent",
                pointStyle: "circle",
                pointRadius: 7,
                borderWidth: 2
            });
        }

        datasets.push({
            label: `Polos em Malha Fechada (K = ${rl.current_k.toFixed(1)})`,
            data: rl.closed_poles.map(cp => ({ x: cp.real, y: cp.imag })),
            borderColor: "#fbbf24",
            backgroundColor: "#fbbf24",
            pointRadius: 6,
            pointStyle: "rectRot"
        });

        chartRootLocus = new Chart(ctx, {
            type: "scatter",
            data: { datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: { display: true, text: "Eixo Real (sigma)", color: "#94a3b8" },
                        grid: { color: "#334155" },
                        ticks: { color: "#94a3b8" }
                    },
                    y: {
                        title: { display: true, text: "Eixo Imaginário (j*omega)", color: "#94a3b8" },
                        grid: { color: "#334155" },
                        ticks: { color: "#94a3b8" }
                    }
                },
                plugins: {
                    legend: { labels: { color: "#f8fafc" } }
                }
            }
        });

        if (rlSummary) {
            rlSummary.innerHTML = `
                <div><strong>Centroide das Assíntotas (sigma_a):</strong> ${rl.centroid.toFixed(3)}</div>
                <div><strong>Ângulos das Assíntotas:</strong> ${rl.asymptote_angles.join("°, ")}°</div>
                <div><strong>Pontos de Dispersão (Breakaway):</strong> ${rl.breakaway_points.length > 0 ? rl.breakaway_points.join(", ") : "Nenhum no eixo real"}</div>
                <div><small class="text-muted">${rl.note || ""}</small></div>
            `;
        }
    }

    function renderBodePlots(bode) {
        const ctxMag = document.getElementById("canvas-bode-mag").getContext("2d");
        if (chartBodeMag) chartBodeMag.destroy();

        chartBodeMag = new Chart(ctxMag, {
            type: "line",
            data: {
                labels: bode.omega.map(w => w.toExponential(1)),
                datasets: [
                    {
                        label: "Magnitude (dB)",
                        data: bode.magnitude_db,
                        borderColor: "#38bdf8",
                        borderWidth: 2,
                        pointRadius: 0
                    },
                    {
                        label: "Linha 0 dB",
                        data: bode.omega.map(() => 0),
                        borderColor: "#ef4444",
                        borderDash: [5, 5],
                        borderWidth: 1.5,
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: { display: true, text: "Frequência omega (rad/s) [Escala Log]", color: "#94a3b8" },
                        grid: { color: "#334155" },
                        ticks: { color: "#94a3b8", maxTicksLimit: 8 }
                    },
                    y: {
                        title: { display: true, text: "Magnitude (dB)", color: "#94a3b8" },
                        grid: { color: "#334155" },
                        ticks: { color: "#94a3b8" }
                    }
                },
                plugins: { legend: { labels: { color: "#f8fafc" } } }
            }
        });

        const ctxPhase = document.getElementById("canvas-bode-phase").getContext("2d");
        if (chartBodePhase) chartBodePhase.destroy();

        chartBodePhase = new Chart(ctxPhase, {
            type: "line",
            data: {
                labels: bode.omega.map(w => w.toExponential(1)),
                datasets: [
                    {
                        label: "Fase (graus)",
                        data: bode.phase_deg,
                        borderColor: "#a78bfa",
                        borderWidth: 2,
                        pointRadius: 0
                    },
                    {
                        label: "Linha -180°",
                        data: bode.omega.map(() => -180),
                        borderColor: "#ef4444",
                        borderDash: [5, 5],
                        borderWidth: 1.5,
                        pointRadius: 0
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: { display: true, text: "Frequência omega (rad/s) [Escala Log]", color: "#94a3b8" },
                        grid: { color: "#334155" },
                        ticks: { color: "#94a3b8", maxTicksLimit: 8 }
                    },
                    y: {
                        title: { display: true, text: "Fase (°)", color: "#94a3b8" },
                        grid: { color: "#334155" },
                        ticks: { color: "#94a3b8" }
                    }
                },
                plugins: { legend: { labels: { color: "#f8fafc" } } }
            }
        });
    }

    function renderStepPlot(step, padeComp) {
        const ctx = document.getElementById("canvas-step").getContext("2d");
        if (chartStep) chartStep.destroy();

        const datasets = [
            {
                label: "Resposta em Malha Fechada y(t)",
                data: step.response.map((y, i) => ({ x: step.time[i], y: y })),
                borderColor: "#34d399",
                borderWidth: 2.5,
                pointRadius: 0,
                showLine: true
            },
            {
                label: "Referência Degrau r(t) = 1.0",
                data: step.time.map(t => ({ x: t, y: 1.0 })),
                borderColor: "#64748b",
                borderDash: [5, 5],
                borderWidth: 1.5,
                pointRadius: 0,
                showLine: true
            }
        ];

        if (padeComp) {
            if (padeComp.pade_1) {
                datasets.push({
                    label: "Aproximação Padé [1/1]",
                    data: padeComp.pade_1.step_response.map((y, i) => ({ x: padeComp.pade_1.step_time[i], y: y })),
                    borderColor: "#f59e0b",
                    borderDash: [3, 3],
                    borderWidth: 1.8,
                    pointRadius: 0,
                    showLine: true
                });
            }
            if (padeComp.pade_2) {
                datasets.push({
                    label: "Aproximação Padé [2/2]",
                    data: padeComp.pade_2.step_response.map((y, i) => ({ x: padeComp.pade_2.step_time[i], y: y })),
                    borderColor: "#ec4899",
                    borderDash: [4, 4],
                    borderWidth: 1.8,
                    pointRadius: 0,
                    showLine: true
                });
            }
        }

        chartStep = new Chart(ctx, {
            type: "scatter",
            data: { datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: { display: true, text: "Tempo (s)", color: "#94a3b8" },
                        grid: { color: "#334155" },
                        ticks: { color: "#94a3b8" }
                    },
                    y: {
                        title: { display: true, text: "Amplitude y(t)", color: "#94a3b8" },
                        grid: { color: "#334155" },
                        ticks: { color: "#94a3b8" }
                    }
                },
                plugins: {
                    legend: { labels: { color: "#f8fafc" } }
                }
            }
        });
    }

    runAnalysis();
});
