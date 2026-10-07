// main.js - Animations, Control Logic & API Handlers
document.addEventListener('DOMContentLoaded', () => {

    const scenarioSelect = document.getElementById('scenarioSelect');
    const runBtn = document.getElementById('runBtn');
    const resetBtn = document.getElementById('resetBtn');
    const downloadReportBtn = document.getElementById('downloadReportBtn');
    const clearLogBtn = document.getElementById('clearLogBtn');

    const stateA = document.getElementById('stateA');
    const stateB = document.getElementById('stateB');
    const overallStatus = document.getElementById('overallStatus');

    const animatedPacket = document.getElementById('animatedPacket');
    const packetLabel = document.getElementById('packetLabel');
    const dropIndicator = document.getElementById('dropIndicator');
    const timelineLog = document.getElementById('timelineLog');

    const statSent = document.getElementById('statSent');
    const statRecv = document.getElementById('statRecv');
    const statDrop = document.getElementById('statDrop');
    const statRetrans = document.getElementById('statRetrans');
    const statLoss = document.getElementById('statLoss');
    const statDuration = document.getElementById('statDuration');

    const diagPoint = document.getElementById('diagPoint');
    const diagEvidence = document.getElementById('diagEvidence');
    const diagCauses = document.getElementById('diagCauses');
    const diagSteps = document.getElementById('diagSteps');
    const comparisonContent = document.getElementById('comparisonContent');

    let currentSimulationData = null;

    runBtn.addEventListener('click', runSimulation);
    resetBtn.addEventListener('click', resetDashboard);
    clearLogBtn.addEventListener('click', clearTimeline);
    downloadReportBtn.addEventListener('click', downloadReport);

    async function runSimulation() {
        const scenario = scenarioSelect.value;
        setButtonStates(true);
        resetVisualState();

        try {
            const response = await fetch('/api/simulate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ scenario: scenario })
            });

            if (!response.ok) throw new Error('Simulation network request failed');

            currentSimulationData = await response.json();

            await animateEvents(currentSimulationData.events);

            renderStatistics(currentSimulationData.statistics);
            renderDiagnosis(currentSimulationData.diagnosis);
            renderComparison(currentSimulationData.comparison);
            updateOverallStatus(currentSimulationData.status);

            downloadReportBtn.disabled = false;

        } catch (error) {
            console.error('Simulation Error:', error);
            addLogItem('0.00s', 'ERROR', 'Simulation failed to execute: ' + error.message, 'dropped');
        } finally {
            setButtonStates(false);
        }
    }

    async function animateEvents(events) {
        clearTimeline();

        for (const ev of events) {
            if (ev.state_a) stateA.textContent = ev.state_a;
            if (ev.state_b) stateB.textContent = ev.state_b;

            addLogItem(ev.timestamp, ev.packet_type, ev.description, ev.status.toLowerCase());

            if (ev.from_host !== ev.to_host && ev.status !== 'IGNORED') {
                await animatePacketFlight(ev.from_host, ev.to_host, ev.packet_type, ev.status);
            } else {
                await sleep(500);
            }
        }
    }

    function animatePacketFlight(fromHost, toHost, packetType, status) {
        return new Promise((resolve) => {
            animatedPacket.className = 'packet';
            dropIndicator.classList.add('hidden');

            if (packetType.includes('SYN-ACK')) animatedPacket.classList.add('syn-ack');
            else if (packetType.includes('ACK')) animatedPacket.classList.add('ack');
            else if (packetType.includes('RST')) animatedPacket.classList.add('rst');

            packetLabel.textContent = packetType.split(' ');

            const isLeftToRight = (fromHost === 'Computer A');
            const startPos = isLeftToRight ? '10%' : '80%';
            const endPos = isLeftToRight ? '80%' : '10%';
            const dropPos = '45%';

            animatedPacket.style.left = startPos;
            animatedPacket.classList.remove('hidden');

            setTimeout(() => {
                if (status === 'DROPPED') {
                    animatedPacket.style.left = dropPos;
                    setTimeout(() => {
                        dropIndicator.style.left = '43%';
                        dropIndicator.classList.remove('hidden');
                        animatedPacket.classList.add('hidden');
                        setTimeout(resolve, 600);
                    }, 800);
                } else {
                    animatedPacket.style.left = endPos;
                    setTimeout(() => {
                        animatedPacket.classList.add('hidden');
                        resolve();
                    }, 800);
                }
            }, 50);
        });
    }

    function renderStatistics(stats) {
        statSent.textContent = stats.total_sent;
        statRecv.textContent = stats.total_received;
        statDrop.textContent = stats.total_dropped;
        statRetrans.textContent = stats.retransmissions;
        statLoss.textContent = `${stats.packet_loss_rate.toFixed(1)}%`;
        statDuration.textContent = `${stats.duration_ms} ms`;
    }

    function renderDiagnosis(diag) {
        diagPoint.textContent = diag.failure_point;
        populateList(diagEvidence, diag.observed_evidence);
        populateList(diagCauses, diag.possible_causes);
        populateList(diagSteps, diag.troubleshooting_steps);
    }

    function renderComparison(comp) {
        const diffText = comp.duration_diff_ms >= 0 
            ? `+${comp.duration_diff_ms} ms slower` 
            : `${comp.duration_diff_ms} ms faster`;

        comparisonContent.innerHTML = `
            <div class="comparison-row">
                <span>Status Baseline:</span>
                <strong>${comp.status_comparison}</strong>
            </div>
            <div class="comparison-row">
                <span>Baseline Duration:</span>
                <span>${comp.baseline_duration_ms} ms</span>
            </div>
            <div class="comparison-row">
                <span>Current Duration:</span>
                <span>${comp.current_duration_ms} ms (${diffText})</span>
            </div>
            <div class="comparison-row">
                <span>Packet Loss Delta:</span>
                <span class="${comp.current_loss > 0 ? 'danger-text' : ''}">${comp.current_loss}%</span>
            </div>
        `;
    }

    function updateOverallStatus(status) {
        overallStatus.textContent = `STATUS: ${status}`;
        if (status === 'ESTABLISHED') {
            overallStatus.className = 'status-pill state-established';
        } else {
            overallStatus.className = 'status-pill state-failed';
        }
    }

    function populateList(element, items) {
        element.innerHTML = '';
        (items || []).forEach(item => {
            const li = document.createElement('li');
            li.textContent = item;
            element.appendChild(li);
        });
    }

    function addLogItem(time, title, desc, statusClass) {
        const item = document.createElement('div');
        item.className = `timeline-item ${statusClass || ''}`;
        item.innerHTML = `<span class="time">[${time}]</span> <span class="text"><strong>${title}:</strong> ${desc}</span>`;
        
        if (timelineLog.querySelector('.placeholder')) {
            timelineLog.innerHTML = '';
        }
        timelineLog.appendChild(item);
        timelineLog.scrollTop = timelineLog.scrollHeight;
    }

    function clearTimeline() {
        timelineLog.innerHTML = `
            <div class="timeline-item placeholder">
                <span class="time">--:--</span>
                <span class="text">Log reset. Ready for next simulation.</span>
            </div>`;
    }

    function resetDashboard() {
        resetVisualState();
        clearTimeline();
        currentSimulationData = null;
        downloadReportBtn.disabled = true;

        statSent.textContent = '0';
        statRecv.textContent = '0';
        statDrop.textContent = '0';
        statRetrans.textContent = '0';
        statLoss.textContent = '0.0%';
        statDuration.textContent = '0 ms';

        diagPoint.textContent = 'Run a simulation to analyze results.';
        diagEvidence.innerHTML = '<li>Awaiting simulation execution...</li>';
        diagCauses.innerHTML = '<li>Awaiting simulation execution...</li>';
        diagSteps.innerHTML = '<li>Awaiting simulation execution...</li>';

        comparisonContent.innerHTML = '<p class="placeholder-text">Run a simulation to view comparative analysis against a standard 3-way handshake.</p>';
        overallStatus.textContent = 'STATUS: IDLE';
        overallStatus.className = 'status-pill state-closed';
    }

    function resetVisualState() {
        animatedPacket.classList.add('hidden');
        dropIndicator.classList.add('hidden');
        stateA.textContent = 'CLOSED';
        stateB.textContent = 'LISTEN';
    }

    function setButtonStates(disabled) {
        runBtn.disabled = disabled;
        resetBtn.disabled = disabled;
    }

    async function downloadReport() {
        if (!currentSimulationData) return;

        try {
            const response = await fetch('/api/download-report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(currentSimulationData)
            });

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `tcp_diagnostic_report_${currentSimulationData.scenario_key}.txt`;
            document.body.appendChild(a);
            a.click();
            a.remove();
        } catch (err) {
            alert('Failed to download report: ' + err.message);
        }
    }

    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
});
