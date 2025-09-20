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
const API_BASE = `${window.location.origin}/api`;
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

// SHOW-MORE BUTTON (removed)

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
        
        // Only clear the normal search results, not the AI recommendations
        normalRecsCount.textContent = 'No search yet';
        normalRecsList.innerHTML = '<div class="empty"><h3>Find Opportunities</h3><p>Search for titles, companies, skills, or locations!</p></div>';
        
        // Clear search inputs
        recSearchInput.value = '';
        recLocationInput.value = '';
        
        // Note: Do NOT call clearAiRecommendations() here to preserve user recommendations
        // Note: loadPersonalizedRecommendations() is NOT called here to avoid reloading user data
    } catch (err) {
        alert('Error loading data: ' + err.message);
    } finally {
        setLoading(false, document.querySelector('.panel'));
    }
}

// FILTERING LOGIC for Normal Recommendations
function getFilteredNormalRecommendations() {
    const qRaw = (recSearchInput.value || '').trim().toLowerCase();
    const locQ = (recLocationInput.value || '').trim().toLowerCase();

    if (!qRaw && !locQ) return []; // Only show results after a search

    // Split by comma, trim, filter out empty
    const qList = qRaw.split(',').map(s => s.trim()).filter(Boolean);

    return allInternships.filter(it => {
        const searchCorpus = `${it.title || ''} ${it.organization || ''}`.toLowerCase();
        const skills = (it.skills_required || []).map(s => s.toLowerCase());

        // If only one search term, keep old behavior (title/org or skill)
        if (qList.length === 1) {
            const q = qList[0];
            let titleOk = q ? searchCorpus.includes(q) : true;
            if (!titleOk) {
                if (!skills.some(s => s.includes(q))) return false;
            }
        } else if (qList.length > 1) {
            // For multiple skills, require ALL to be present in skills_required
            if (!qList.every(skillQ => skills.some(s => s.includes(skillQ)))) return false;
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

    // Show more button removed
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
        aiRecommendationsArea.innerHTML = '<div class="empty"><h4>No matches found</h4><p>None of your profile skills matched current internships. Try adding more skills or editing your profile.</p></div>';
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
                <div class="small">Similarity: <span class="match">${Math.round(r.match_score)}%</span></div>
            </div>
            <div style="margin-bottom:8px"><strong>Shared Skills:</strong> ${matchedHtml}</div>
            <div class="small" style="color:var(--text-muted); margin-bottom: 8px;">${escapeHtml(it.description || '')}</div>
            <div class="skills-display">
                <strong>All Skills:</strong> ${internSkills.slice(0, 5).map(skill => escapeHtml(skill)).join(', ')}${internSkills.length > 5 ? '...' : ''}
            </div>
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

// CLEAR FILTERS - Only clears normal search, preserves AI recommendations
function clearNormalRecFilters() {
    recSearchInput.value = '';
    recLocationInput.value = '';
    normalRecsLimit = 10;
    renderNormalRecommendations();
    // Note: AI recommendations are preserved and not cleared
}

// SHOW MORE HANDLER (removed)

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

// LOGIN/LOGOUT FUNCTIONALITY
function checkLoginStatus() {
    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    const loginBtn = document.getElementById('loginBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const profileBtn = document.getElementById('profileBtn');
    
    if (isLoggedIn) {
        loginBtn.style.display = 'none';
        logoutBtn.style.display = 'inline-block';
        if (profileBtn) profileBtn.style.display = 'inline-block';
    } else {
        loginBtn.style.display = 'inline-block';
        logoutBtn.style.display = 'none';
        if (profileBtn) profileBtn.style.display = 'none';
    }
}

function logout() {
    localStorage.removeItem('isLoggedIn');
    localStorage.removeItem('username');
    localStorage.removeItem('candidate_id'); // Clear candidate_id on logout
    checkLoginStatus();
    // Clear personalized recommendations only when user logs out
    clearAiRecommendations();
    // Optionally redirect to login page
    // window.location.href = 'login.html';
}

// Load personalized recommendations for logged-in users
async function loadPersonalizedRecommendations() {
    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    const candidateId = localStorage.getItem('candidate_id');
    if (!isLoggedIn || !candidateId) {
        return;
    }
    try {
        const response = await fetch(`${API_BASE}/recommendations/${candidateId}?t=${Date.now()}`);
        if (response.ok) {
            const result = await response.json();
            displayPersonalizedRecommendations(result.recommendations || [], result.candidate || 'your');
        }
    } catch (error) {
        console.log('No personalized recommendations available');
    }
}

// Display personalized recommendations in the AI panel
function displayPersonalizedRecommendations(recommendations, candidateName) {
    const aiPanel = aiRecommendationsArea.closest('.panel');
    const titleElement = aiPanel.querySelector('strong');
    const subtitleElement = aiPanel.querySelector('.small');
    // Update the panel title
    titleElement.textContent = 'Personalized Recommendations';
    subtitleElement.textContent = `Based on ${candidateName}'s profile`;
    // Clear and populate recommendations
    aiRecommendationsArea.innerHTML = '';
    if (!recommendations.length) {
        aiRecommendationsArea.innerHTML = '<div class="empty"><h4>No personalized matches yet</h4><p>We couldn\'t find internships matching your current skills. Try adding or editing skills in your profile.</p></div>';
        return;
    }
    recommendations.forEach(rec => {
        const block = document.createElement('div');
        block.className = 'recommendation';
        // Get the full internship data to show skills
        const fullInternship = allInternships.find(i => i.internship_id === rec.internship_id) || rec;
        const skills = fullInternship.skills_required || rec.skills_required || [];
        block.innerHTML = `
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                <div>
                    <div class="card-title">${escapeHtml(rec.title || '—')}</div>
                    <div class="small">${escapeHtml(rec.organization || '')} • ${escapeHtml(rec.location || '—')}</div>
                </div>
                <div class="small">Match: <span class="match">${Math.round(rec.match_score)}%</span></div>
            </div>
            <div class="small" style="color:var(--text-muted); margin-bottom: 8px;">${escapeHtml(rec.description || '')}</div>
            <div class="skills-display">
                <strong>Skills:</strong> ${skills.slice(0, 5).map(skill => escapeHtml(skill)).join(', ')}${skills.length > 5 ? '...' : ''}
            </div>
        `;
        aiRecommendationsArea.appendChild(block);
    });
}

// INITIAL FETCH of data
loadAllData();
checkLoginStatus();
// Only load personalized recommendations if user is logged in and candidate_id is set
if (localStorage.getItem('isLoggedIn') === 'true') {
    // Wait for candidate_id to be set (e.g., after profile creation)
    const tryLoadRecs = () => {
        const cid = localStorage.getItem('candidate_id');
        if (cid) {
            loadPersonalizedRecommendations();
        } else {
            setTimeout(tryLoadRecs, 300); // Poll until candidate_id is set
        }
    };
    tryLoadRecs();
}