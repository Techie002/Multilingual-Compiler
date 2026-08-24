/* Compiler Execution, Multi-Language Templates & Analysis JavaScript */

const LANGUAGE_FILES = {
    python: "solution.py",
    c: "solution.c",
    cpp: "solution.cpp",
    java: "Solution.java",
    javascript: "solution.js",
    sql: "queries.sql",
    rag: "pipeline.rag",
    php: "solution.php",
    go: "solution.go",
    rust: "solution.rs",
    bash: "script.sh"
};

document.addEventListener('DOMContentLoaded', () => {
    const runBtn = document.getElementById('run-code-btn');
    const analyzeBtn = document.getElementById('analyze-code-btn');
    const submitBtn = document.getElementById('submit-code-btn');
    const langSelect = document.getElementById('language-select');

    if (runBtn) runBtn.addEventListener('click', runCode);
    if (analyzeBtn) analyzeBtn.addEventListener('click', analyzeCode);
    if (submitBtn) submitBtn.addEventListener('click', submitCode);
    if (langSelect) langSelect.addEventListener('change', handleLanguageChange);
});

function handleLanguageChange() {
    const langSelect = document.getElementById('language-select');
    if (!langSelect) return;

    const lang = langSelect.value.toLowerCase();
    const fileName = LANGUAGE_FILES[lang] || `solution.${lang}`;

    const fileNameLabel = document.getElementById('file-name-label');
    if (fileNameLabel) {
        fileNameLabel.innerHTML = `<i class="fa-regular fa-file-code"></i> ${fileName}`;
    }

    showToast(`Switched language to ${lang.toUpperCase()}`, "info");

    if (typeof fetchCodeHints === 'function') {
        fetchCodeHints(false);
    }
}

function clearEditor() {
    const codeEditor = document.getElementById('code-editor');
    if (codeEditor) {
        codeEditor.value = '';
        codeEditor.focus();
        showToast("Editor cleared.", "info");
        if (typeof fetchCodeHints === 'function') fetchCodeHints(false);
    }
}

function toggleProblemDetails() {
    const details = document.getElementById('problem-banner-details');
    const icon = document.getElementById('problem-toggle-icon');
    const label = document.getElementById('problem-toggle-label');
    if (!details) return;
    
    if (details.style.display === 'none') {
        details.style.display = 'block';
        if (icon) icon.style.transform = 'rotate(0deg)';
        if (label) label.innerText = 'Hide Details';
    } else {
        details.style.display = 'none';
        if (icon) icon.style.transform = 'rotate(-90deg)';
        if (label) label.innerText = 'Show Details';
    }
}

async function runCode() {
    const codeEditor = document.getElementById('code-editor');
    const code = codeEditor ? codeEditor.value : '';
    const language = document.getElementById('language-select').value;
    const customInput = document.getElementById('custom-input') ? document.getElementById('custom-input').value : '';
    const runBtn = document.getElementById('run-code-btn');

    const consoleOutput = document.getElementById('console-output');
    const metricsDisplay = document.getElementById('metrics-display');
    
    if (!code.trim()) {
        showToast("Please write your code in the editor before running.", "warning");
        if (consoleOutput) consoleOutput.innerText = "Error: Cannot run empty source code. Please write your program above.";
        return;
    }
    
    if (consoleOutput) consoleOutput.innerText = `Compiling & executing ${language.toUpperCase()} in sandbox...`;
    
    // Switch to console tab
    if (typeof switchTab === 'function') {
        switchTab('tab-console');
    }

    if (runBtn) {
        runBtn.disabled = true;
        runBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Running...';
    }

    try {
        const response = await fetch('/api/compile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, language, custom_input: customInput })
        });
        const result = await response.json();

        if (result.success) {
            const data = result.data;
            let outputText = "";
            if (data.stderr) {
                outputText += `[Message / Trace]\n${data.stderr}\n\n`;
            }
            outputText += data.stdout || "[Process completed with no output]";

            if (consoleOutput) consoleOutput.innerText = outputText;
            if (metricsDisplay) {
                metricsDisplay.innerHTML = `
                    <span class="badge badge-easy">Time: ${data.execution_time}s</span>
                    <span class="badge badge-medium">Memory: ${data.memory_usage_mb} MB</span>
                    <span class="badge ${data.exit_code === 0 ? 'badge-easy' : 'badge-hard'}">Exit Code: ${data.exit_code}</span>
                `;
            }
            showToast("Execution finished.", "success");
            if (typeof fetchCodeHints === 'function') fetchCodeHints(false);
        } else {
            if (consoleOutput) consoleOutput.innerText = result.message || "Execution error.";
            showToast(result.message || "Error running code.", "danger");
            if (typeof fetchCodeHints === 'function') fetchCodeHints(false);
        }
    } catch (err) {
        if (consoleOutput) consoleOutput.innerText = `Error: ${err.message}`;
        showToast("Server network error.", "danger");
    } finally {
        if (runBtn) {
            runBtn.disabled = false;
            runBtn.innerHTML = '<i class="fa-solid fa-play" style="color: var(--accent-emerald);"></i> Run Code';
        }
    }
}

async function analyzeCode() {
    const code = document.getElementById('code-editor').value;
    const language = document.getElementById('language-select').value;
    const analyzeBtn = document.getElementById('analyze-code-btn');

    if (!code.trim()) {
        showToast("Please write your code in the editor before running analysis.", "warning");
        return;
    }

    if (analyzeBtn) {
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing...';
    }

    try {
        const response = await fetch('/api/analyze-code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, language })
        });
        const result = await response.json();

        if (result.success) {
            const data = result.data;
            renderTokens(data.tokens);
            renderSyntaxErrors(data.syntax_errors);
            renderParseTree(data.parse_tree);
            renderAST(data.ast);
            renderSemantics(data.semantic_issues);
            renderOptimization(data.optimization);
            
            // Switch to Lexer tab so user immediately sees analysis results!
            if (typeof switchTab === 'function') {
                switchTab('tab-lexer');
            }
            
            showToast("Compiler analysis complete! Showing Lexer tokens.", "success");
            if (typeof fetchCodeHints === 'function') fetchCodeHints(false);
        } else {
            showToast(result.message || "Analysis error.", "danger");
        }
    } catch (err) {
        showToast("Analysis error: " + err.message, "danger");
    } finally {
        if (analyzeBtn) {
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = '<i class="fa-solid fa-microchip" style="color: var(--accent-cyan);"></i> Compiler Analysis';
        }
    }
}

function renderTokens(tokens) {
    const container = document.getElementById('tokens-container');
    if (!container) return;
    if (!tokens || tokens.length === 0) {
        container.innerHTML = "<p>No tokens generated.</p>";
        return;
    }
    let html = `<table class="tokens-table"><thead><tr><th>Line</th><th>Type</th><th>Value</th></tr></thead><tbody>`;
    tokens.forEach(t => {
        html += `<tr><td>${t.line}</td><td><span class="badge badge-medium">${t.type}</span></td><td><code>${escapeHtml(t.value)}</code></td></tr>`;
    });
    html += `</tbody></table>`;
    container.innerHTML = html;
}

function renderSyntaxErrors(errors) {
    const container = document.getElementById('syntax-container');
    if (!container) return;
    if (!errors || errors.length === 0) {
        container.innerHTML = `<p class="badge badge-easy">No Syntax Errors Detected</p>`;
        return;
    }
    let html = "";
    errors.forEach(e => {
        html += `<div style="color: var(--accent-rose); margin-bottom: 0.5rem;">Line ${e.line}: ${escapeHtml(e.message)}</div>`;
    });
    container.innerHTML = html;
}

function renderParseTree(parseTree) {
    const container = document.getElementById('parsetree-container');
    if (!container) return;
    container.innerHTML = `<pre class="console-output" style="max-height: 250px; overflow-y: auto;">${JSON.stringify(parseTree, null, 2)}</pre>`;
}

function renderAST(astNode) {
    const container = document.getElementById('ast-container');
    if (!container) return;
    
    function buildAstHtml(node) {
        if (!node) return '';
        let html = `<div class="ast-node"><span class="ast-node-name">${escapeHtml(node.name)}</span>`;
        if (node.details) html += ` <span style="color: var(--text-muted);">(${escapeHtml(node.details)})</span>`;
        if (node.children && node.children.length > 0) {
            node.children.forEach(child => {
                html += buildAstHtml(child);
            });
        }
        html += `</div>`;
        return html;
    }
    container.innerHTML = buildAstHtml(astNode);
}

function renderSemantics(issues) {
    const container = document.getElementById('semantics-container');
    if (!container) return;
    if (!issues || issues.length === 0) {
        container.innerHTML = `<p class="badge badge-easy">No Semantic Violations Detected</p>`;
        return;
    }
    let html = "";
    issues.forEach(i => {
        html += `<div style="color: var(--accent-amber); margin-bottom: 0.4rem;">[${escapeHtml(i.type)}] Line ${i.line}: ${escapeHtml(i.message)}</div>`;
    });
    container.innerHTML = html;
}

function renderOptimization(opt) {
    const container = document.getElementById('optimization-container');
    if (!container) return;
    let html = `<div style="margin-bottom: 0.75rem;">
        <strong>Performance Score:</strong> <span class="badge ${opt.performance_score >= 80 ? 'badge-easy' : 'badge-medium'}">${opt.performance_score} / 100</span>
    </div><ul>`;
    opt.suggestions.forEach(s => {
        html += `<li style="margin-bottom: 0.3rem;">${escapeHtml(s)}</li>`;
    });
    html += `</ul>`;
    container.innerHTML = html;
}

async function submitCode() {
    const submitBtn = document.getElementById('submit-code-btn');
    const code = document.getElementById('code-editor').value;
    const language = document.getElementById('language-select').value;
    const assignmentId = document.getElementById('assignment-id') ? document.getElementById('assignment-id').value : null;

    if (!code.trim()) {
        showToast("Cannot submit empty source code.", "warning");
        return;
    }

    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Evaluating...';
    }

    try {
        const response = await fetch('/api/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, language, assignment_id: assignmentId })
        });
        const result = await response.json();
        
        if (result.success) {
            const data = result.data;
            showToast(`Submitted successfully! Score: ${data.final_score}/100`, "success");
            renderSubmissionModal(data);
            openModal('submission-result-modal');
        } else {
            showToast(result.message || "Evaluation error.", "danger");
        }
    } catch (err) {
        showToast("Submission failed. Please check server connection.", "danger");
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Submit Solution';
        }
    }
}

function renderSubmissionModal(data) {
    const container = document.getElementById('submission-result-content');
    if (!container) return;

    const score = data.final_score || 0;
    const scoreClass = score >= 80 ? 'badge-easy' : (score >= 50 ? 'badge-medium' : 'badge-hard');
    const scoreColor = score >= 80 ? 'var(--accent-emerald)' : (score >= 50 ? 'var(--accent-amber)' : 'var(--accent-rose)');

    let certBanner = '';
    if (data.certificate_eligible) {
        certBanner = `
            <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: var(--radius-sm); padding: 0.75rem 1rem; margin-bottom: 1rem; display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <strong style="color: var(--accent-emerald);"><i class="fa-solid fa-award"></i> Certificate of Accomplishment Earned!</strong>
                    <p style="margin: 0.2rem 0 0 0; font-size: 0.8rem; color: var(--text-secondary);">100% of benchmark test cases successfully passed for this challenge!</p>
                </div>
                <a href="/certificate/${data.submission_id}" class="btn btn-success btn-sm" target="_blank">
                    <i class="fa-solid fa-certificate"></i> View Certificate
                </a>
            </div>
        `;
    }

    container.innerHTML = `
        ${certBanner}
        
        <!-- Score & Test Cases Overview -->
        <div style="display: flex; gap: 1rem; margin-bottom: 1.25rem; align-items: center; background: rgba(15, 23, 42, 0.6); padding: 1rem; border-radius: var(--radius-sm); border: 1px solid var(--border-color);">
            <div style="text-align: center; min-width: 130px; border-right: 1px solid var(--border-color); padding-right: 1rem;">
                <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">Overall Score</div>
                <div style="font-size: 2.2rem; font-weight: 800; color: ${scoreColor}; font-family: var(--font-mono);">${score}<span style="font-size: 1rem; color: var(--text-muted);">/100</span></div>
            </div>
            <div style="flex: 1;">
                <div style="font-size: 0.95rem; font-weight: 600; margin-bottom: 0.25rem;">
                    Test Cases Passed: <span class="badge ${scoreClass}">${data.test_cases_passed} / ${data.total_test_cases}</span>
                </div>
                <div style="font-size: 0.85rem; color: var(--text-secondary);">
                    ${escapeHtml(data.feedback || "Automated evaluation completed.")}
                </div>
            </div>
        </div>

        <!-- Metric Details Grid -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 1.5rem;">
            <div style="padding: 0.6rem 0.8rem; background: rgba(30, 41, 59, 0.4); border-radius: var(--radius-sm); border: 1px solid var(--border-color); font-size: 0.85rem;">
                <span style="color: var(--text-muted);">Correctness:</span> <strong>${data.correctness_score || 0} / 100</strong>
            </div>
            <div style="padding: 0.6rem 0.8rem; background: rgba(30, 41, 59, 0.4); border-radius: var(--radius-sm); border: 1px solid var(--border-color); font-size: 0.85rem;">
                <span style="color: var(--text-muted);">Code Style & Quality:</span> <strong>${data.style_score || 0} / 100</strong>
            </div>
            <div style="padding: 0.6rem 0.8rem; background: rgba(30, 41, 59, 0.4); border-radius: var(--radius-sm); border: 1px solid var(--border-color); font-size: 0.85rem;">
                <span style="color: var(--text-muted);">Execution Time:</span> <strong>${data.execution_time || 0}s</strong>
            </div>
            <div style="padding: 0.6rem 0.8rem; background: rgba(30, 41, 59, 0.4); border-radius: var(--radius-sm); border: 1px solid var(--border-color); font-size: 0.85rem;">
                <span style="color: var(--text-muted);">AI Probability:</span> <strong>${data.ai_probability_score || 0}%</strong>
            </div>
        </div>

        <!-- Action Buttons -->
        <div style="display: flex; gap: 0.75rem; justify-content: flex-end; flex-wrap: wrap;">
            <a href="/api/reports/pdf/${data.submission_id}" class="btn btn-primary" target="_blank" id="download-report-btn">
                <i class="fa-solid fa-file-pdf"></i> Download PDF Report
            </a>
            <a href="/leaderboard" class="btn btn-secondary">
                <i class="fa-solid fa-trophy" style="color: var(--accent-amber);"></i> View Leaderboard
            </a>
            <button class="btn btn-secondary" onclick="closeModal('submission-result-modal')">
                Close
            </button>
        </div>
    `;
}

function escapeHtml(str) {
    if (typeof str !== 'string') return String(str);
    return str.replace(/&/g, '&amp;')
              .replace(/</g, '&lt;')
              .replace(/>/g, '&gt;')
              .replace(/"/g, '&quot;')
              .replace(/'/g, '&#039;');
}

