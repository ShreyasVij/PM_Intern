// THEME TOGGLE FUNCTIONALITY
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.querySelector('.theme-toggle');
    const htmlElement = document.documentElement;

    function toggleTheme() {
        const currentTheme = htmlElement.getAttribute('data-theme');
        if (currentTheme === 'dark') {
            htmlElement.removeAttribute('data-theme');
            localStorage.setItem('theme', 'light');
            updateThemeIcon('light');
        } else {
            htmlElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
            updateThemeIcon('dark');
        }
    }

    function updateThemeIcon(theme) {
        if (!themeToggle) return;
        const svg = themeToggle.querySelector('svg');
        if (!svg) return;
        if (theme === 'dark') {
            svg.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/>`;
        } else {
            svg.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/>`;
        }
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }

    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        htmlElement.setAttribute('data-theme', 'dark');
        updateThemeIcon('dark');
    } else {
        htmlElement.removeAttribute('data-theme');
        updateThemeIcon('light');
    }
});

// CONFIG
const API_BASE = "http://127.0.0.1:3000/api";
document.getElementById('apiBaseDisplay').textContent = API_BASE;

// STATE
let allInternships = [];
let normalRecsLimit = 10;
let selectedInternshipIdForAI = null;

// UI REFS
const normalRecsList = document.getElementById('normalRecommendationsList');
const aiRecommendationsArea = document.getElementById('aiRecommendationsArea');
const normalRecsCount = document.getElementById('normalRecsCount');
const selectedAiTriggerLabel = document.getElementById('selectedAiTriggerLabel');

// SEARCH INPUTS for Normal Recommendations
const recSearchInput = document.getElementById('recSearchInput');
const recLocationInput = document.getElementById('recLocationInput');

// SHOW-MORE BUTTON
const normalRecsShowMore = document.getElementById('normalRecsShowMore');

// BUTTONS
document.getElementById('reloadBtn').addEventListener('click', loadAllData);
document.getElementById('normalRecsClear').addEventListener('click', clearNormalRecFilters);

// HELPERS
function debounce(fn, ms = 250) {
    let t;
    return (...args) => {
        clearTimeout(t);
        t = setTimeout(() => fn(...args), ms);
    };
}

function escapeHtml(s) {
    if (s === null || s === undefined) return '';
    return String(s).replace(/[&<>"'`=\/]/g, ch => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;', '/': '&#x2F;', '`': '&#x60;', '=': '&#x3D;'
    })[ch]);
}

// INITIAL LOAD: Fetch all internship data
async function loadAllData() {
    setLoading(true, document.querySelector('.panel')); // Load only left panel initially
    try {
        const res = await fetch(`${API_BASE}/internships`);
        if (!res.ok) throw new Error('Failed to load internship data');
        const json = await res.json();
        allInternships = Array.isArray(json.internships) ? json.internships : [];
        
        normalRecsCount.textContent = 'No search yet';
        normalRecsList.innerHTML = '<div class="empty"><h3>Find Opportunities</h3><p>Search for titles, companies, skills, or locations!</p></div>';
        clearAiRecommendations();
    } catch (err) {
        alert('Error loading data: ' + err.message);
    } finally {
        setLoading(false, document.querySelector('.panel'));
    }
}

// FILTERING LOGIC for Normal Recommendations
function getFilteredNormalRecommendations() {
    const q = (recSearchInput.value || '').trim().toLowerCase();
    const locQ = (recLocationInput.value || '').trim().toLowerCase();

    if (!q && !locQ) return []; // Only show results after a search

    return allInternships.filter(it => {
        const searchCorpus = `${it.title || ''} ${it.organization || ''}`.toLowerCase();
        let titleOk = q ? searchCorpus.includes(q) : true;
        
        if (!titleOk) {
            const skills = (it.skills_required || []).map(s => s.toLowerCase());
            if (!skills.some(s => s.includes(q))) return false;
        }
        if (locQ && !((it.location || '').toLowerCase().includes(locQ))) return false;
        return true;
    });
}

// RENDER Normal Recommendations results (left panel)
function renderNormalRecommendations() {
    const filtered = getFilteredNormalRecommendations();
    normalRecsList.innerHTML = '';
    if (!filtered.length) {
        normalRecsCount.textContent = '0 results';
        normalRecsList.innerHTML = '<div class="empty"><h3>No opportunities found</h3><p>Try different search terms or locations!</p></div>';
        normalRecsShowMore.style.display = 'none';
        return;
    }
    normalRecsCount.textContent = `${filtered.length} result${filtered.length === 1 ? '' : 's'}`;
    const toShow = filtered.slice(0, normalRecsLimit);

    for (const it of toShow) {
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
            <div class="card-header">
                <div>
                    <div class="card-title">${escapeHtml(it.title)}</div>
                    <div class="small">${escapeHtml(it.organization)} • ${escapeHtml(it.location)}</div>
                </div>
                <div class="small">${escapeHtml(it.sector || '—')}</div>
            </div>
            <div class="badges" style="margin-top:10px">
                ${(it.skills_required || []).slice(0, 8).map(s => `<span class="badge">${escapeHtml(s)}</span>`).join('')}
            </div>
            <div class="small" style="margin-top:10px; color:var(--text-muted)">${escapeHtml(it.description || '')}</div>
            <div style="text-align:right; margin-top:1rem;">
                <button class="btn ghost btn-sm ai-trigger-btn" data-internship-id="${escapeHtml(it.internship_id)}">Find Similar (AI)</button>
            </div>
        `;
        normalRecsList.appendChild(card);
    }

    document.querySelectorAll('.ai-trigger-btn').forEach(btn => {
        btn.addEventListener('click', handleAiTriggerClick);
    });

    normalRecsShowMore.style.display = filtered.length > normalRecsLimit ? 'inline-block' : 'none';
}

function handleAiTriggerClick(e) {
    const internshipId = e.target.getAttribute('data-internship-id');
    const internship = allInternships.find(i => i.internship_id === internshipId);
    if (internship) {
        document.querySelectorAll('#normalRecommendationsList .card').forEach(c => c.classList.remove('selected'));
        e.target.closest('.card').classList.add('selected');
        
        selectInternshipForAI(internship);
        fetchAiRecommendations(internship);
    }
}

// SELECT Internship for AI: update UI tag and store ID
function selectInternshipForAI(internship) {
    selectedInternshipIdForAI = internship.internship_id;
    selectedAiTriggerLabel.textContent = `${internship.title}`;
}

// FETCH AI Recommendations from backend (Right Panel)
async function fetchAiRecommendations(baseInternship) {
    if (!baseInternship) return;
    const aiPanel = aiRecommendationsArea.closest('.panel');
    setLoading(true, aiPanel);
    
    try {
        const res = await fetch(`${API_BASE}/recommendations/by_internship/${encodeURIComponent(baseInternship.internship_id)}`);
        const json = await res.json();
        if (!res.ok) throw new Error(json.error || 'Failed to fetch AI recommendations');
        
        renderAiRecommendations(Array.isArray(json.recommendations) ? json.recommendations : [], baseInternship);
    } catch (err) {
        aiRecommendationsArea.innerHTML = `<div class="empty"><h4>Oops! Something went wrong</h4><p>${escapeHtml(err.message)}</p></div>`;
    } finally {
        setLoading(false, aiPanel);
    }
}

// RENDER AI Recommendations
function renderAiRecommendations(recs, baseInternship) {
    aiRecommendationsArea.innerHTML = '';
    if (!recs.length) {
        aiRecommendationsArea.innerHTML = '<div class="empty"><h4>No AI Matches Found</h4><p>Our AI couldn\'t find similar internships. Try another one!</p></div>';
        return;
    }
    
    const baseSkills = (baseInternship.skills_required || []).map(s => s.toLowerCase());

    for (const r of recs) {
        const it = allInternships.find(i => i.internship_id === r.internship_id) || r;
        const internSkills = (it.skills_required || []).map(s => s.toLowerCase());
        const matched = internSkills.filter(s => baseSkills.includes(s));
        const matchedHtml = matched.length ? matched.map(m => `<span class="tag">${escapeHtml(m)}</span>`).join(' ') : '<span class="small" style="color:var(--text-dim)">⚡ Unique skill set</span>';

        const block = document.createElement('div');
        block.className = 'recommendation';
        block.innerHTML = `
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                <div>
                    <div class="card-title">${escapeHtml(it.title || '—')}</div>
                    <div class="small">${escapeHtml(it.organization || '')} • ${escapeHtml(it.location || '—')}</div>
                </div>
                <div class="small">Similarity: <span class="match">${(r.match_score * 100).toFixed(0)}%</span></div>
            </div>
            <div style="margin-bottom:8px"><strong>Shared Skills:</strong> ${matchedHtml}</div>
            <div class="small" style="color:var(--text-muted)">${escapeHtml(it.description || '')}</div>
        `;
        aiRecommendationsArea.appendChild(block);
    }
}

// CLEAR AI Recommendations
function clearAiRecommendations() {
    aiRecommendationsArea.innerHTML = '<div class="empty"><h4>AI-Powered Discovery</h4><p>Click "Find Similar (AI)" on an internship to see related opportunities here!</p></div>';
    selectedAiTriggerLabel.textContent = 'none';
    selectedInternshipIdForAI = null;
}

// CLEAR FILTERS
function clearNormalRecFilters() {
    recSearchInput.value = '';
    recLocationInput.value = '';
    normalRecsLimit = 10;
    renderNormalRecommendations();
}

// SHOW MORE HANDLER
normalRecsShowMore.addEventListener('click', () => {
    normalRecsLimit += 10;
    renderNormalRecommendations();
});

// HOOK INPUT EVENTS (debounced)
const debouncedRender = debounce(() => {
    normalRecsLimit = 10;
    renderNormalRecommendations();
});
recSearchInput.addEventListener('input', debouncedRender);
recLocationInput.addEventListener('input', debouncedRender);


// SIMPLE LOADING STATE
function setLoading(isLoading, element) {
    if (isLoading) {
        element.classList.add('loading');
        element.querySelectorAll('button, input').forEach(el => el.disabled = true);
    } else {
        element.classList.remove('loading');
        element.querySelectorAll('button, input').forEach(el => el.disabled = false);
    }
    document.getElementById('normalRecsClear').disabled = false; // Always keep clear enabled
}

// INITIAL FETCH of data
loadAllData();