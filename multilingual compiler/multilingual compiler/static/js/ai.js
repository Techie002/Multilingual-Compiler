/* AI Generator & Comparison Features JavaScript */

document.addEventListener('DOMContentLoaded', () => {
    const aiGenBtn = document.getElementById('ai-generate-btn');
    const aiCompareBtn = document.getElementById('ai-compare-btn');

    if (aiGenBtn) aiGenBtn.addEventListener('click', generateAICode);
    if (aiCompareBtn) aiCompareBtn.addEventListener('click', compareAIvsStudent);
});

async function generateAICode() {
    const problemInput = document.getElementById('ai-problem-input');
    const problem = problemInput ? problemInput.value.trim() : '';
    const difficulty = document.getElementById('ai-difficulty-select') ? document.getElementById('ai-difficulty-select').value : 'Medium';
    const language = document.getElementById('language-select') ? document.getElementById('language-select').value : 'python';
    const genBtn = document.getElementById('ai-generate-btn');

    if (!problem) {
        showToast("Please enter a problem statement.", "warning");
        return;
    }

    showToast("AI is generating solution...", "info");
    if (genBtn) {
        genBtn.disabled = true;
        genBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating AI Code...';
    }

    try {
        const response = await fetch('/api/generate-code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ problem_statement: problem, difficulty, language })
        });
        const result = await response.json();

        if (result.success) {
            const data = result.data;
            const container = document.getElementById('ai-generated-display');
            if (container) {
                container.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <h4 style="margin: 0;"><i class="fa-solid fa-wand-magic-sparkles" style="color: var(--accent-purple);"></i> Generated Solution (${escapeHtml(language.toUpperCase())})</h4>
                        <div style="display: flex; gap: 0.5rem;">
                            <button class="btn btn-primary btn-sm" onclick="insertAICodeToEditor()">
                                <i class="fa-solid fa-arrow-left"></i> Insert into Editor
                            </button>
                            <button class="btn btn-secondary btn-sm" onclick="copyAICode()">
                                <i class="fa-solid fa-copy"></i> Copy
                            </button>
                        </div>
                    </div>
                    <pre class="console-output" style="max-height: 250px; overflow-y: auto;"><code>${escapeHtml(data.generated_code)}</code></pre>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-top: 0.75rem;">
                        <div class="glass-card" style="padding: 0.5rem 0.75rem; font-size: 0.85rem;">
                            <strong>Time Complexity:</strong> <span class="badge badge-medium">${escapeHtml(data.time_complexity)}</span>
                        </div>
                        <div class="glass-card" style="padding: 0.5rem 0.75rem; font-size: 0.85rem;">
                            <strong>Space Complexity:</strong> <span class="badge badge-medium">${escapeHtml(data.space_complexity)}</span>
                        </div>
                    </div>
                    <p style="margin-top: 0.75rem; font-size: 0.85rem; color: #cbd5e1;"><strong>Explanation:</strong> ${escapeHtml(data.explanation)}</p>
                `;
            }
            // Store global AI code
            window.latestAICode = data.generated_code;
            showToast("AI Solution generated successfully!", "success");
        } else {
            showToast(result.message || "Failed to generate AI code.", "danger");
        }
    } catch (err) {
        showToast("Error connecting to AI code generator.", "danger");
    } finally {
        if (genBtn) {
            genBtn.disabled = false;
            genBtn.innerHTML = 'Generate AI Solution';
        }
    }
}

function insertAICodeToEditor() {
    if (window.latestAICode) {
        const editor = document.getElementById('code-editor');
        if (editor) {
            editor.value = window.latestAICode;
            closeModal('ai-drawer-modal');
            showToast("AI Solution loaded into Editor!", "success");
            if (typeof fetchCodeHints === 'function') fetchCodeHints(false);
        }
    } else {
        showToast("No generated code available to insert.", "warning");
    }
}

function copyAICode() {
    if (window.latestAICode) {
        navigator.clipboard.writeText(window.latestAICode).then(() => {
            showToast("Code copied to clipboard!", "success");
        });
    }
}

async function compareAIvsStudent() {
    const studentCode = document.getElementById('code-editor').value;
    const aiCode = window.latestAICode || "# AI Code Solution\ndef solve(): pass";
    const language = document.getElementById('language-select').value;

    showToast("Comparing Student Code with AI...", "info");

    try {
        const response = await fetch('/api/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ student_code: studentCode, ai_code: aiCode, language })
        });
        const result = await response.json();

        if (result.success) {
            const data = result.data;
            const modal = document.getElementById('comparison-modal');
            const content = document.getElementById('comparison-modal-content');
            if (modal && content) {
                content.innerHTML = `
                    <h3>Student vs AI Code Comparison</h3>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 1rem 0;">
                        <div class="glass-card"><strong>Overall Similarity</strong>: <span class="badge badge-medium">${data.overall_similarity}%</span></div>
                        <div class="glass-card"><strong>Logic Match</strong>: <span class="badge badge-easy">${data.logic_similarity}%</span></div>
                        <div class="glass-card"><strong>Structural Match</strong>: <span class="badge badge-hard">${data.structural_similarity}%</span></div>
                    </div>
                    <h4>Unified Code Diff</h4>
                    <pre class="console-output" style="max-height: 350px; overflow-y: auto;">${escapeHtml(data.unified_diff.join('\n'))}</pre>
                `;
                openModal('comparison-modal');
            }
        }
    } catch (err) {
        showToast("Error executing comparison.", "danger");
    }
}

function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.add('active');
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.remove('active');
}

function escapeHtml(str) {
    if (typeof str !== 'string') return String(str);
    return str.replace(/&/g, '&amp;')
              .replace(/</g, '&lt;')
              .replace(/>/g, '&gt;')
              .replace(/"/g, '&quot;')
              .replace(/'/g, '&#039;');
}
