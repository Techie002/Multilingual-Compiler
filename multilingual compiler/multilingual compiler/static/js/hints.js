/* Non-AI Code & Problem Hint Engine JavaScript */

document.addEventListener('DOMContentLoaded', () => {
    const fetchHintsBtn = document.getElementById('fetch-hints-btn');
    if (fetchHintsBtn) {
        fetchHintsBtn.addEventListener('click', () => fetchCodeHints(true));
    }

    // Auto-fetch hints when user navigates to the Code Hints tab
    const hintsTabBtn = document.querySelector('[data-tab="tab-hints"]');
    if (hintsTabBtn) {
        hintsTabBtn.addEventListener('click', () => {
            fetchCodeHints(false);
        });
    }

    // Initial load of hints if on editor page
    if (document.getElementById('tab-hints')) {
        setTimeout(() => fetchCodeHints(false), 500);
    }
});

let isFetchingHints = false;

async function fetchCodeHints(showToastNotice = false) {
    if (isFetchingHints) return;
    
    const codeEditor = document.getElementById('code-editor');
    if (!codeEditor) return;

    const code = codeEditor.value;
    const language = document.getElementById('language-select') ? document.getElementById('language-select').value : 'python';
    const assignmentId = document.getElementById('assignment-id') ? document.getElementById('assignment-id').value : null;
    const consoleOutput = document.getElementById('console-output') ? document.getElementById('console-output').innerText : '';
    const problemInput = document.getElementById('ai-problem-input') ? document.getElementById('ai-problem-input').value : '';

    const problemContainer = document.getElementById('problem-hints-container');
    const diagnosticsContainer = document.getElementById('code-diagnostics-container');
    const errorGuidanceContainer = document.getElementById('error-guidance-container');

    if (showToastNotice) {
        showToast("Analyzing code structure & problem hints...", "info");
    }

    isFetchingHints = true;
    const fetchBtn = document.getElementById('fetch-hints-btn');
    if (fetchBtn) {
        fetchBtn.disabled = true;
        fetchBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing...';
    }

    try {
        const response = await fetch('/api/hints', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code: code,
                language: language,
                assignment_id: assignmentId,
                compiler_output: consoleOutput,
                problem_statement: problemInput
            })
        });

        const result = await response.json();

        if (result.success) {
            const data = result.data;
            renderProblemHints(data.problem_hints);
            renderCodeDiagnostics(data.code_diagnostics);
            renderErrorGuidance(data.error_guidance);

            if (showToastNotice) {
                showToast("Hints & diagnostics updated!", "success");
            }
        } else {
            if (showToastNotice) {
                showToast(result.message || "Failed to load hints.", "danger");
            }
        }
    } catch (err) {
        console.error("Hints error:", err);
        if (showToastNotice) {
            showToast("Network error fetching hints.", "danger");
        }
    } finally {
        isFetchingHints = false;
        if (fetchBtn) {
            fetchBtn.disabled = false;
            fetchBtn.innerHTML = '<i class="fa-solid fa-rotate"></i> Refresh Hints';
        }
    }
}

function renderProblemHints(problemData) {
    const container = document.getElementById('problem-hints-container');
    if (!container) return;

    if (!problemData || !problemData.hints || problemData.hints.length === 0) {
        container.innerHTML = `<p style="color: var(--text-muted);">No specific algorithmic hints available for this problem.</p>`;
        return;
    }

    let html = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
            <span style="font-size: 0.85rem; font-weight: 600; color: var(--accent-cyan);">
                <i class="fa-solid fa-book-bookmark"></i> Topic: ${escapeHtml(problemData.matched_topic || 'Algorithmic Guidance')}
            </span>
            <span style="font-size: 0.75rem; color: var(--text-muted);">Progressive Guidance</span>
        </div>
        <div class="hints-accordion">
    `;

    problemData.hints.forEach((hint, idx) => {
        const isFirst = (idx === 0);
        const levelBadgeClass = hint.level === 1 ? 'badge-easy' : (hint.level === 2 ? 'badge-medium' : 'badge-hard');
        
        html += `
            <div class="hint-card glass-card" id="hint-item-${idx}" style="margin-bottom: 0.75rem; border: 1px solid var(--border-color); padding: 0.85rem 1rem; border-radius: var(--radius-sm);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center; gap: 0.6rem;">
                        <span class="badge ${levelBadgeClass}" style="font-size: 0.75rem;">Hint ${hint.level}</span>
                        <strong style="font-size: 0.9rem; color: #f8fafc;">${escapeHtml(hint.title)}</strong>
                    </div>
                    <button class="btn btn-secondary btn-sm hint-toggle-btn" onclick="toggleHintReveal(${idx})" style="padding: 0.25rem 0.6rem; font-size: 0.75rem;">
                        <span id="hint-btn-text-${idx}">${isFirst ? '<i class="fa-solid fa-eye-slash"></i> Hide' : '<i class="fa-solid fa-eye"></i> Reveal'}</span>
                    </button>
                </div>
                <div id="hint-body-${idx}" class="hint-body" style="margin-top: 0.65rem; padding-top: 0.65rem; border-top: 1px dashed rgba(255,255,255,0.1); font-size: 0.875rem; color: #cbd5e1; line-height: 1.5; display: ${isFirst ? 'block' : 'none'};">
                    ${formatHintMarkdown(hint.content)}
                </div>
            </div>
        `;
    });

    html += `</div>`;
    container.innerHTML = html;
}

function toggleHintReveal(idx) {
    const body = document.getElementById(`hint-body-${idx}`);
    const btnText = document.getElementById(`hint-btn-text-${idx}`);
    if (!body || !btnText) return;

    if (body.style.display === 'none') {
        body.style.display = 'block';
        btnText.innerHTML = '<i class="fa-solid fa-eye-slash"></i> Hide';
    } else {
        body.style.display = 'none';
        btnText.innerHTML = '<i class="fa-solid fa-eye"></i> Reveal';
    }
}

function renderCodeDiagnostics(diagnostics) {
    const container = document.getElementById('code-diagnostics-container');
    if (!container) return;

    if (!diagnostics || diagnostics.length === 0) {
        container.innerHTML = `
            <div class="glass-card" style="padding: 0.75rem 1rem; border-left: 4px solid var(--accent-emerald);">
                <strong style="color: var(--accent-emerald);"><i class="fa-solid fa-circle-check"></i> Code Analysis Clean</strong>
                <p style="color: var(--text-secondary); font-size: 0.85rem; margin-top: 0.25rem;">No syntax or logical anti-patterns detected.</p>
            </div>
        `;
        return;
    }

    let html = "";
    diagnostics.forEach(diag => {
        let borderColor = "#38bdf8"; // info / cyan
        let icon = "fa-info-circle";
        let badgeClass = "badge-medium";

        if (diag.type === 'error') {
            borderColor = "#f43f5e"; // rose
            icon = "fa-triangle-exclamation";
            badgeClass = "badge-hard";
        } else if (diag.type === 'warning') {
            borderColor = "#f59e0b"; // amber
            icon = "fa-circle-exclamation";
            badgeClass = "badge-medium";
        } else if (diag.type === 'tip') {
            borderColor = "#a855f7"; // purple
            icon = "fa-lightbulb";
            badgeClass = "badge-easy";
        } else if (diag.type === 'success') {
            borderColor = "#10b981"; // emerald
            icon = "fa-circle-check";
            badgeClass = "badge-easy";
        }

        html += `
            <div class="glass-card" style="margin-bottom: 0.6rem; padding: 0.75rem 1rem; border-left: 4px solid ${borderColor};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem;">
                    <strong style="font-size: 0.875rem; color: #f8fafc;">
                        <i class="fa-solid ${icon}" style="color: ${borderColor}; margin-right: 0.35rem;"></i>
                        ${escapeHtml(diag.title)}
                    </strong>
                    <span class="badge ${badgeClass}" style="font-size: 0.7rem;">${escapeHtml(diag.badge || 'Diagnostic')}</span>
                </div>
                <p style="color: #cbd5e1; font-size: 0.84rem; line-height: 1.45; margin: 0;">
                    ${formatHintMarkdown(diag.message)}
                </p>
            </div>
        `;
    });

    container.innerHTML = html;
}

function renderErrorGuidance(errorData) {
    const container = document.getElementById('error-guidance-container');
    if (!container) return;

    if (!errorData) {
        container.style.display = 'none';
        container.innerHTML = '';
        return;
    }

    container.style.display = 'block';
    container.innerHTML = `
        <div class="glass-card" style="border-left: 4px solid #f43f5e; padding: 0.85rem 1rem; margin-bottom: 1rem; background: rgba(244, 63, 94, 0.08);">
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.4rem;">
                <span class="badge badge-hard" style="font-size: 0.75rem;">Runtime / Compiler Fix</span>
                <strong style="color: #fca5a5; font-size: 0.9rem;">${escapeHtml(errorData.error_type)}</strong>
            </div>
            <p style="color: #f1f5f9; font-size: 0.85rem; margin-bottom: 0.4rem;"><strong>Diagnosis:</strong> ${escapeHtml(errorData.explanation)}</p>
            <div style="background: rgba(0,0,0,0.3); padding: 0.5rem 0.75rem; border-radius: var(--radius-sm); border: 1px solid rgba(244,63,94,0.2);">
                <strong style="color: var(--accent-amber); font-size: 0.8rem;"><i class="fa-solid fa-wrench"></i> Suggested Remedy:</strong>
                <p style="color: #cbd5e1; font-size: 0.825rem; margin: 0.2rem 0 0 0;">${escapeHtml(errorData.remedy)}</p>
            </div>
        </div>
    `;
}

function formatHintMarkdown(text) {
    if (!text) return '';
    let formatted = escapeHtml(text);
    // Replace `code` with styled <code>
    formatted = formatted.replace(/`([^`]+)`/g, '<code style="background: rgba(0,0,0,0.4); padding: 0.1rem 0.35rem; border-radius: 3px; color: #38bdf8; font-family: var(--font-mono); font-size: 0.82rem;">$1</code>');
    // Replace math notations like $O(N)$
    formatted = formatted.replace(/\$([^\$]+)\$/g, '<span style="color: var(--accent-amber); font-family: var(--font-mono);">$1</span>');
    // Replace **bold**
    formatted = formatted.replace(/\*\*([^\*]+)\*\*/g, '<strong>$1</strong>');
    return formatted;
}

function escapeHtml(str) {
    if (typeof str !== 'string') return '';
    return str.replace(/&/g, '&amp;')
              .replace(/</g, '&lt;')
              .replace(/>/g, '&gt;')
              .replace(/"/g, '&quot;')
              .replace(/'/g, '&#039;');
}
