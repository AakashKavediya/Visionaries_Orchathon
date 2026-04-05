document.addEventListener('DOMContentLoaded', () => {
    const dropZone       = document.getElementById('drop-zone');
    const fileInput      = document.getElementById('file-input');
    const uploadContent  = document.querySelector('.upload-content');
    const uploadIcon     = document.getElementById('upload-icon');
    const loader         = document.getElementById('loader');
    const successState   = document.getElementById('success');
    const progressBar    = document.getElementById('progress');
    const resultFilename = document.getElementById('result-filename');
    const downloadBtn    = document.getElementById('download-btn');
    const resetBtn       = document.getElementById('reset-btn');
    const errorToast     = document.getElementById('error-message');

    // MEP elements
    const mepSection       = document.getElementById('mep-section');
    const mepLoading       = document.getElementById('mep-loading');
    const mepStats         = document.getElementById('mep-stats');
    const mepTableWrapper  = document.getElementById('mep-table-wrapper');
    const mepTbody         = document.getElementById('mep-tbody');
    const mepEmpty         = document.getElementById('mep-empty');
    const mepTypeFilter    = document.getElementById('mep-type-filter');

    // Clash elements
    const clashSection     = document.getElementById('clash-section');
    const clashLoading     = document.getElementById('clash-loading');
    const clashStats       = document.getElementById('clash-stats');
    const clashTableWrapper= document.getElementById('clash-table-wrapper');
    const clashTbody       = document.getElementById('clash-tbody');
    const clashEmpty       = document.getElementById('clash-empty');

    // Store all fetched MEP rows for client-side filtering
    let _allMepElements = [];

    // ─── Drag-and-drop / Click ──────────────────────────────────────────────
    dropZone.addEventListener('click', (e) => {
        if (!loader.classList.contains('hidden') || !successState.classList.contains('hidden')) return;
        fileInput.click();
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) handleFile(fileInput.files[0]);
    });

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(ev =>
        dropZone.addEventListener(ev, e => { e.preventDefault(); e.stopPropagation(); })
    );

    ['dragenter', 'dragover'].forEach(ev => dropZone.addEventListener(ev, () => {
        if (!loader.classList.contains('hidden') || !successState.classList.contains('hidden')) return;
        dropZone.classList.add('dragover');
    }));

    ['dragleave', 'drop'].forEach(ev => dropZone.addEventListener(ev, () =>
        dropZone.classList.remove('dragover')
    ));

    dropZone.addEventListener('drop', (e) => {
        if (!loader.classList.contains('hidden') || !successState.classList.contains('hidden')) return;
        const files = e.dataTransfer.files;
        if (files.length > 0) { fileInput.files = files; handleFile(files[0]); }
    });

    // ─── Reset flow ─────────────────────────────────────────────────────────
    resetBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.value = '';
        successState.classList.add('hidden');
        uploadIcon.classList.remove('hidden');
        uploadContent.classList.remove('hidden');
        dropZone.style.cursor = 'pointer';

        // Hide MEP panel
        mepSection.classList.add('hidden');
        mepTbody.innerHTML = '';
        mepStats.innerHTML = '';
        mepStats.classList.add('hidden');
        mepTableWrapper.classList.add('hidden');
        mepEmpty.classList.add('hidden');
        mepLoading.classList.add('hidden');
        mepTypeFilter.value = 'all';
        _allMepElements = [];

        // Hide clash panel
        if (clashSection) clashSection.classList.add('hidden');
        if (clashTbody) clashTbody.innerHTML = '';
        if (clashStats) { clashStats.innerHTML = ''; clashStats.classList.add('hidden'); }
        if (clashTableWrapper) clashTableWrapper.classList.add('hidden');
        if (clashEmpty) clashEmpty.classList.add('hidden');
        if (clashLoading) clashLoading.classList.add('hidden');
    });

    // ─── Type filter ────────────────────────────────────────────────────────
    mepTypeFilter.addEventListener('change', () => applyFilter());

    // ─── File validation & upload ───────────────────────────────────────────
    function handleFile(file) {
        if (!file.name.toLowerCase().endsWith('.rvt')) {
            showError('Only .rvt files are supported');
            return;
        }
        uploadFile(file);
    }

    function uploadFile(file) {
        uploadIcon.classList.add('hidden');
        uploadContent.classList.add('hidden');
        loader.classList.remove('hidden');
        dropZone.style.cursor = 'default';
        progressBar.style.width = '0%';

        const formData = new FormData();
        formData.append('file', file);

        let progressVal = 0;
        const progressInterval = setInterval(() => {
            if (progressVal < 90) {
                progressVal += Math.random() * 10;
                progressBar.style.width = Math.min(progressVal, 90) + '%';
            }
        }, 300);

        fetch('/api/convert', { method: 'POST', body: formData })
            .then(res => {
                if (!res.ok) return res.text().then(txt => {
                    try { const e = JSON.parse(txt); throw new Error(e.error || 'Upload failed'); }
                    catch { throw new Error(`Server error ${res.status}: ${res.statusText}`); }
                });
                return res.json();
            })
            .then(data => {
                clearInterval(progressInterval);
                progressBar.style.width = '100%';
                setTimeout(() => showSuccess(data.filename, data.download_url), 500);
            })
            .catch(error => {
                clearInterval(progressInterval);
                loader.classList.add('hidden');
                uploadIcon.classList.remove('hidden');
                uploadContent.classList.remove('hidden');
                dropZone.style.cursor = 'pointer';
                progressBar.style.width = '0%';
                showError(error.message);
            });
    }

    // ─── Success state ───────────────────────────────────────────────────────
    function showSuccess(filename, downloadUrl) {
        loader.classList.add('hidden');
        successState.classList.remove('hidden');
        resultFilename.textContent = filename;
        downloadBtn.href = downloadUrl;
        downloadBtn.download = filename;

        // Fetch MEP data and clash data in parallel
        fetchMEPData(filename);
        fetchClashData(filename);
    }

    // ─── MEP Data fetching ───────────────────────────────────────────────────
    function fetchMEPData(filename) {
        // Show panel + loading spinner
        mepSection.classList.remove('hidden');
        mepLoading.classList.remove('hidden');
        mepStats.classList.add('hidden');
        mepTableWrapper.classList.add('hidden');
        mepEmpty.classList.add('hidden');

        // Scroll to mep section
        mepSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

        fetch(`/api/mep-data/${encodeURIComponent(filename)}`)
            .then(res => {
                if (!res.ok) return res.text().then(txt => {
                    try { const e = JSON.parse(txt); throw new Error(e.error || 'MEP fetch failed'); }
                    catch { throw new Error(`Server error ${res.status}: ${res.statusText}`); }
                });
                return res.json();
            })
            .then(data => {
                mepLoading.classList.add('hidden');
                _allMepElements = data.elements || [];

                if (_allMepElements.length === 0) {
                    mepEmpty.classList.remove('hidden');
                    return;
                }

                renderStats(_allMepElements);
                renderTable(_allMepElements);
                mepStats.classList.remove('hidden');
                mepTableWrapper.classList.remove('hidden');
            })
            .catch(err => {
                mepLoading.classList.add('hidden');
                showError(`MEP extraction failed: ${err.message}`);
            });
    }

    // ─── Render stats chips ──────────────────────────────────────────────────
    function renderStats(elements) {
        const counts = {};
        elements.forEach(el => { counts[el.type] = (counts[el.type] || 0) + 1; });

        const totalChip = `<div class="stat-chip">Total <strong>${elements.length}</strong> elements</div>`;
        const typeChips = Object.entries(counts)
            .map(([type, count]) => `<div class="stat-chip"><strong>${count}</strong> ${type.replace('Ifc','')}</div>`)
            .join('');

        mepStats.innerHTML = totalChip + typeChips;
    }

    // ─── Render table rows ───────────────────────────────────────────────────
    function renderTable(elements) {
        mepTbody.innerHTML = elements.map((el, i) => {
            const badgeClass = [
                'IfcPipeSegment','IfcDuctSegment','IfcFlowTerminal','IfcFlowFitting','IfcFlowController'
            ].includes(el.type) ? `type-${el.type}` : 'type-default';

            const propsHtml = buildPropsHtml(el.properties);
            const locHtml   = buildLocationHtml(el.location);

            return `<tr data-type="${el.type}">
                <td><span class="type-badge ${badgeClass}">${el.type}</span></td>
                <td>${escHtml(el.name)}</td>
                <td><span class="id-mono">${escHtml(el.id)}</span></td>
                <td class="props-cell">${propsHtml}</td>
                <td class="location-cell">${locHtml}</td>
            </tr>`;
        }).join('');
    }

    function buildPropsHtml(props) {
        if (!props || Object.keys(props).length === 0) return '<span style="color:#475569">—</span>';
        const entries = Object.entries(props);
        const gridRows = entries.map(([k, v]) =>
            `<span class="pk">${escHtml(k)}</span><span class="pv">${escHtml(String(v))}</span>`
        ).join('');
        return `<details>
            <summary>${entries.length} propert${entries.length === 1 ? 'y' : 'ies'}</summary>
            <div class="props-grid">${gridRows}</div>
        </details>`;
    }

    function buildLocationHtml(loc) {
        if (!loc || Object.keys(loc).length === 0) return '<span style="color:#475569">—</span>';
        return `<span>X: ${fmt(loc.x)}</span><span>Y: ${fmt(loc.y)}</span><span>Z: ${fmt(loc.z)}</span>`;
    }

    function fmt(n) { return (typeof n === 'number') ? n.toFixed(2) : '—'; }

    // ─── Filter ──────────────────────────────────────────────────────────────
    function applyFilter() {
        const selected = mepTypeFilter.value;
        const rows = mepTbody.querySelectorAll('tr');
        let visible = 0;
        rows.forEach(row => {
            const match = selected === 'all' || row.dataset.type === selected;
            row.style.display = match ? '' : 'none';
            if (match) visible++;
        });

        mepEmpty.classList.toggle('hidden', visible > 0);
        mepTableWrapper.classList.toggle('hidden', visible === 0);
    }

    // ─── Clash Data fetching ─────────────────────────────────────────────────
    function fetchClashData(filename) {
        if (!clashSection) return;
        clashSection.classList.remove('hidden');
        clashLoading.classList.remove('hidden');
        clashStats.classList.add('hidden');
        clashTableWrapper.classList.add('hidden');
        clashEmpty.classList.add('hidden');

        fetch(`/api/clash-data/${encodeURIComponent(filename)}`)
            .then(res => {
                if (!res.ok) return res.text().then(txt => {
                    try { const e = JSON.parse(txt); throw new Error(e.error || 'Clash fetch failed'); }
                    catch { throw new Error(`Server error ${res.status}`); }
                });
                return res.json();
            })
            .then(data => {
                clashLoading.classList.add('hidden');
                const clashes = data.clashes || [];
                // Stats chip
                clashStats.innerHTML = `<div class="stat-chip"><strong>${clashes.length}</strong> clash${clashes.length !== 1 ? 'es' : ''} detected</div>
                    <div class="stat-chip">across <strong>${data.mep_element_count}</strong> MEP elements</div>`;
                clashStats.classList.remove('hidden');

                if (clashes.length === 0) {
                    clashEmpty.classList.remove('hidden');
                    return;
                }
                renderClashTable(clashes);
                clashTableWrapper.classList.remove('hidden');
            })
            .catch(err => {
                clashLoading.classList.add('hidden');
                showError(`Clash detection failed: ${err.message}`);
            });
    }

    function renderClashTable(clashes) {
        const DIRECTION_ARROWS = { UP:'↑', DOWN:'↓', NORTH:'→', SOUTH:'←', EAST:'→', WEST:'←' };
        const TYPE_COLORS = {
            'DUCT_DUCT':   '#22d3ee', 'PIPE_PIPE': '#60a5fa',
            'DUCT_PIPE':   '#f59e0b', 'PIPE_DUCT': '#f59e0b',
            'TERMINAL_DUCT':'#a78bfa','TERMINAL_PIPE':'#a78bfa',
        };
        clashTbody.innerHTML = clashes.map((c, i) => {
            const color = TYPE_COLORS[c.clash_type] || '#94a3b8';
            const arrow = DIRECTION_ARROWS[c.direction] || '';
            const origPos = c.original_position.map(v => v.toFixed(3)).join(', ');
            const newPos  = c.new_position.map(v => v.toFixed(3)).join(', ');
            return `<tr>
                <td><span style="color:${color};font-weight:600">${escHtml(c.clash_id)}</span></td>
                <td><span class="id-mono">${escHtml(c.move_element_id)}</span><br><small style="color:#64748b">${escHtml(c.move_element_type)}: ${escHtml(c.move_element_name||'')}</small></td>
                <td><span class="id-mono">${escHtml(c.fixed_element_id)}</span><br><small style="color:#64748b">${escHtml(c.fixed_element_type)}: ${escHtml(c.fixed_element_name||'')}</small></td>
                <td><span class="type-badge" style="background:rgba(99,102,241,0.2);border:1px solid rgba(99,102,241,0.4);color:#a5b4fc">${escHtml(c.clash_type)}</span></td>
                <td class="location-cell"><span>[${escHtml(origPos)}]</span><span style="color:#6366f1;font-size:0.8rem">→ [${escHtml(newPos)}]</span></td>
                <td><span style="color:#4ade80;font-weight:600">${arrow} ${escHtml(c.direction)}</span><br><small>${escHtml(String(c.offset))}m</small></td>
                <td style="max-width:220px;font-size:0.75rem;color:#94a3b8">${escHtml(c.reason)}</td>
            </tr>`;
        }).join('');
    }

    // ─── Error toast ─────────────────────────────────────────────────────────
    function showError(message) {
        errorToast.textContent = message;
        errorToast.classList.remove('hidden');
        errorToast.classList.add('show');
        setTimeout(() => {
            errorToast.classList.remove('show');
            setTimeout(() => errorToast.classList.add('hidden'), 300);
        }, 4000);
    }

    // ─── Utility ─────────────────────────────────────────────────────────────
    function escHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }
});
