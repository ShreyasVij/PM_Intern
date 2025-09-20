// Ensure we run from backend origin to avoid CORS/session issues when using Live Server
(function enforceBackendOrigin() {
    try {
        const host = window.location.host || '';
        if (!/:3000$/.test(host)) {
            const target = `http://127.0.0.1:3000${window.location.pathname}${window.location.search}${window.location.hash}`;
            console.warn('Redirecting to backend origin for proper API access:', target);
            window.location.replace(target);
        }
    } catch (e) {
        console.warn('Origin enforcement skipped:', e);
    }
})();

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
// Derive API base from current origin to keep cookies same-origin in dev
const API_BASE = `${window.location.origin}/api`;
document.getElementById('apiBaseDisplay').textContent = API_BASE;

// STATE
let allInternships = [];
let normalRecsLimit = 10;
let selectedInternshipIdForAI = null;
let isLoadingData = false; // Prevent multiple simultaneous requests
let hasTriedInitialLoad = false; // Prevent infinite loading loops
let isInitialized = false; // Prevent multiple script executions

// One-shot guards to prevent repeated API calls
let hasLoadedInternships = false;       // True after first successful /internships load
let internshipsLoadInFlight = false;    // True while /internships fetch is running
let hasLoadedPersonalized = false;      // True after first successful personalized recs
let personalizedLoadInFlight = false;   // True while personalized recs fetch is running

// Right panel mode state: 'personalized' or 'similar'
let rightPanelMode = 'similar';
let lastPersonalized = null; // { recommendations, candidateName }
let lastSimilar = null;      // { baseInternship, recommendations }

// UI REFS
const normalRecsList = document.getElementById('normalRecommendationsList');
const aiRecommendationsArea = document.getElementById('aiRecommendationsArea');
const normalRecsCount = document.getElementById('normalRecsCount');
const selectedAiTriggerLabel = document.getElementById('selectedAiTriggerLabel');

// SEARCH INPUTS for Normal Recommendations
const recSearchInput = document.getElementById('recSearchInput');
const recLocationInput = document.getElementById('recLocationInput');

// SHOW-MORE BUTTON (removed)

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
    // Strong guard to avoid loops
    if (internshipsLoadInFlight || hasLoadedInternships) {
        console.log('⛔ Skipping loadAllData: in-flight or already loaded', { internshipsLoadInFlight, hasLoadedInternships });
        return Promise.resolve();
    }
    if (isLoadingData) {
        console.log('Load already in progress, ignoring request');
        return Promise.resolve(); // Return resolved promise to avoid breaking .then() chains
    }
    internshipsLoadInFlight = true;
    
    isLoadingData = true;
    
    setLoading(true, document.querySelector('.panel')); // Load only left panel initially
    try {
        const res = await fetch(`${API_BASE}/internships`);
        if (!res.ok) throw new Error('Failed to load internship data');
        const json = await res.json();
        
        // Handle both response formats: direct array or wrapped in internships key
        if (Array.isArray(json)) {
            allInternships = json;
        } else if (Array.isArray(json.internships)) {
            allInternships = json.internships;
        } else if (Array.isArray(json.data)) {
            allInternships = json.data;
        } else {
            console.error('Unexpected API response format:', json);
            allInternships = [];
        }
        
        console.log(`Successfully loaded ${allInternships.length} internships`);
        console.log('Sample internship skills:', allInternships[0]?.skills_required); // Debug log
        if (allInternships.length > 0) {
            hasLoadedInternships = true;
        }
        
        // Clear the normal search results, and reset AI state on fresh load
        normalRecsCount.textContent = 'No search yet';
        normalRecsList.innerHTML = '<div class="empty"><h3>Find Opportunities</h3><p>Search for titles, companies, skills, or locations!</p></div>';
        
        // Clear search inputs
        recSearchInput.value = '';
        recLocationInput.value = '';
        
        // Clear AI recommendations on data reload to prevent state confusion
        clearAiRecommendations();
        // Note: loadPersonalizedRecommendations() is NOT called here to avoid reloading user data
    } catch (err) {
        console.error('Error loading data:', err);
        alert('Error loading data: ' + err.message);
    } finally {
        setLoading(false, document.querySelector('.panel'));
        isLoadingData = false;
        internshipsLoadInFlight = false;
    }
}

// FILTERING LOGIC for Normal Recommendations
function getFilteredNormalRecommendations() {
    const qRaw = (recSearchInput.value || '').trim().toLowerCase();
    const locQ = (recLocationInput.value || '').trim().toLowerCase();

    if (!qRaw && !locQ) return []; // Only show results after a search

    // Split by comma, trim, filter out empty
    const qList = qRaw.split(',').map(s => s.trim()).filter(Boolean);

    const filtered = allInternships.filter(it => {
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
    
    return filtered;
}

// RENDER Normal Recommendations results (left panel)
function renderNormalRecommendations() {
    const filtered = getFilteredNormalRecommendations();
    normalRecsList.innerHTML = '';
    if (!filtered.length) {
        normalRecsCount.textContent = '0 results';
        normalRecsList.innerHTML = '<div class="empty"><h3>No opportunities found</h3><p>Try different search terms or locations!</p></div>';
        // normalRecsShowMore.style.display = 'none'; // Commented out - button doesn't exist
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

    // Event listeners are now handled via delegation at the document level
    // No need to attach individual listeners to each button

    // Show more button removed
}

function handleAiTriggerClick(e) {
    // Safeguard: Don't proceed if data isn't loaded
    if (!allInternships || allInternships.length === 0) {
        console.log('AI trigger clicked but no internships data loaded');
        return;
    }
    
    const internshipId = e.target.getAttribute('data-internship-id');
    const internship = allInternships.find(i => i.internship_id === internshipId);
    if (internship) {
        document.querySelectorAll('#normalRecommendationsList .card').forEach(c => c.classList.remove('selected'));
        e.target.closest('.card').classList.add('selected');
        
        selectInternshipForAI(internship);
        fetchAiRecommendations(internship);
    } else {
        console.log('AI trigger clicked but internship not found:', internshipId);
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
        const recs = Array.isArray(json.recommendations) ? json.recommendations : [];
        lastSimilar = { baseInternship, recommendations: recs };
        setRightPanelHeaderForSimilar(baseInternship);
        renderAiRecommendations(recs, baseInternship);
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
    if (rightPanelMode === 'personalized') {
        aiRecommendationsArea.innerHTML = '<div class="empty"><h4>No personalized matches yet</h4><p>Sign in and create/update your profile to see tailored opportunities.</p></div>';
    } else {
        aiRecommendationsArea.innerHTML = '<div class="empty"><h4>AI-Powered Discovery</h4><p>Click "Find Similar (AI)" on an internship to see related opportunities here!</p></div>';
        selectedAiTriggerLabel.textContent = 'none';
    }
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
    console.log('Search triggered:', recSearchInput.value, recLocationInput.value); // Debug log
    normalRecsLimit = 10;
    renderNormalRecommendations();
});


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
    if (personalizedLoadInFlight || hasLoadedPersonalized) {
        console.log('⛔ Skipping personalized load: in-flight or already loaded', { personalizedLoadInFlight, hasLoadedPersonalized });
        return;
    }
    personalizedLoadInFlight = true;
    try {
        const response = await fetch(`${API_BASE}/recommendations/${candidateId}?t=${Date.now()}`, {
            credentials: 'include'
        });
        if (response.ok) {
            const result = await response.json();
            const recs = Array.isArray(result.recommendations) ? result.recommendations : [];
            displayPersonalizedRecommendations(recs, result.candidate || 'your');
            hasLoadedPersonalized = true;
        }
    } catch (error) {
        console.log('No personalized recommendations available');
    } finally {
        personalizedLoadInFlight = false;
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
    lastPersonalized = { recommendations: recommendations.slice(), candidateName };
    // Clear and populate recommendations
    aiRecommendationsArea.innerHTML = '';
    if (!Array.isArray(recommendations) || recommendations.length === 0) {
        aiRecommendationsArea.innerHTML = '<div class="empty"><h4>No personalized matches yet</h4><p>We couldn\'t find internships matching your current skills. Try adding or editing skills in your profile.</p></div>';
        return;
    }
    recommendations.forEach(rec => {
        const block = document.createElement('div');
        block.className = 'recommendation';
        // Get the full internship data to show skills
        const fullInternship = allInternships.find(i => i.internship_id === rec.internship_id) || rec;
        
        // Try multiple sources for skills data
        let displaySkills = [];
        if (fullInternship.skills_required && fullInternship.skills_required.length > 0) {
            displaySkills = fullInternship.skills_required;
        } else if (rec.skills_required && rec.skills_required.length > 0) {
            displaySkills = rec.skills_required;
        } else if (rec.skills && rec.skills.length > 0) {
            displaySkills = rec.skills;
        }
        
        console.log('Skills for', rec.title, ':', displaySkills); // Debug log
        
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
                <strong>Skills:</strong> ${displaySkills.length > 0 ? displaySkills.slice(0, 5).map(skill => escapeHtml(skill)).join(', ') + (displaySkills.length > 5 ? '...' : '') : 'Not specified'}
            </div>
        `;
        aiRecommendationsArea.appendChild(block);
    });
}

// Update header for Similar mode
function setRightPanelHeaderForSimilar(baseInternship) {
    const aiPanel = aiRecommendationsArea.closest('.panel');
    const titleElement = aiPanel.querySelector('strong');
    const subtitleElement = aiPanel.querySelector('.small');
    titleElement.textContent = 'Similar Internships';
    const label = baseInternship ? baseInternship.title : 'none';
    subtitleElement.innerHTML = `Based on: <b id="selectedAiTriggerLabel">${escapeHtml(label)}</b>`;
}

// Toggle UI helpers
function updateModeUI() {
    const btnPers = document.getElementById('togglePersonalized');
    const btnSimilar = document.getElementById('toggleSimilar');
    if (!btnPers || !btnSimilar) return;
    if (rightPanelMode === 'personalized') {
        btnPers.classList.remove('ghost');
        btnSimilar.classList.add('ghost');
    } else {
        btnSimilar.classList.remove('ghost');
        btnPers.classList.add('ghost');
    }
}

function setRightPanelMode(mode) {
    if (mode !== 'personalized' && mode !== 'similar') return;
    if (rightPanelMode === mode) return;
    rightPanelMode = mode;
    updateModeUI();
    if (mode === 'personalized') {
        // Show personalized recommendations (if available)
        const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
        const candidateId = localStorage.getItem('candidate_id');
        if (!isLoggedIn || !candidateId) {
            const aiPanel = aiRecommendationsArea.closest('.panel');
            const titleElement = aiPanel.querySelector('strong');
            const subtitleElement = aiPanel.querySelector('.small');
            titleElement.textContent = 'Personalized Recommendations';
            subtitleElement.textContent = 'Login to see personalized matches';
            aiRecommendationsArea.innerHTML = '<div class="empty"><h4>Login required</h4><p>Please login and create your profile to view personalized recommendations.</p></div>';
            return;
        }
        if (lastPersonalized) {
            displayPersonalizedRecommendations(lastPersonalized.recommendations, lastPersonalized.candidateName);
        } else {
            // Trigger load
            loadPersonalizedRecommendations();
        }
    } else {
        // Similar mode
        if (selectedInternshipIdForAI) {
            const base = allInternships.find(i => i.internship_id === selectedInternshipIdForAI);
            if (base) {
                if (lastSimilar && lastSimilar.baseInternship && lastSimilar.baseInternship.internship_id === base.internship_id) {
                    setRightPanelHeaderForSimilar(base);
                    renderAiRecommendations(lastSimilar.recommendations, base);
                } else {
                    fetchAiRecommendations(base);
                }
            } else {
                setRightPanelHeaderForSimilar(null);
                clearAiRecommendations();
            }
        } else {
            setRightPanelHeaderForSimilar(null);
            clearAiRecommendations();
        }
    }
}

// Ensure initialization only runs when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Prevent multiple initializations if script loads multiple times
    if (window.appInitialized) {
        console.log('App already initialized, skipping');
        return;
    }
    window.appInitialized = true;
    
    console.log('🚀 Starting app initialization...');
    
    // Setup event listeners
    const debouncedLoadAllData = debounce(loadAllData, 1000); // Debounce to 1 second
    document.getElementById('normalRecsClear').addEventListener('click', clearNormalRecFilters);

    // Event delegation for AI trigger buttons (prevents multiple listeners)
    document.addEventListener('click', function(e) {
        if (e.target && e.target.classList.contains('ai-trigger-btn')) {
            handleAiTriggerClick(e);
            // Switch to Similar mode when user actively requests similar recs
            rightPanelMode = 'similar';
            updateModeUI();
        }
    });
    
    // Setup search input listeners
    if (recSearchInput && recLocationInput) {
        recSearchInput.addEventListener('input', debouncedRender);
        recLocationInput.addEventListener('input', debouncedRender);
        console.log('✅ Search event listeners attached'); // Debug log
    } else {
        console.error('❌ Search input elements not found!', {recSearchInput, recLocationInput});
    }
    
    // Ensure login controls reflect current state immediately
    checkLoginStatus();

    // INITIAL FETCH of data - only if not already loaded recently
    const lastDataLoad = localStorage.getItem('lastDataLoad');
    const now = Date.now();
    const tenMinutes = 10 * 60 * 1000; // 10 minutes in milliseconds

    // Function to load personalized recommendations after internships data is ready
    function loadPersonalizedRecsWhenReady() {
        if (localStorage.getItem('isLoggedIn') === 'true') {
            console.log('📊 Loading personalized recommendations...');
            // Wait for candidate_id to be set (e.g., after profile creation)
            let retryCount = 0;
            const maxRetries = 5; // Reduced from 10 to 5 to prevent excessive polling
            const tryLoadRecs = () => {
                const cid = localStorage.getItem('candidate_id');
                if (cid) {
                    console.log('✅ Found candidate_id, loading recommendations');
                    loadPersonalizedRecommendations();
                } else if (retryCount < maxRetries) {
                    retryCount++;
                    console.log(`⏳ Waiting for candidate_id... (${retryCount}/${maxRetries})`);
                    setTimeout(tryLoadRecs, 500); // Increased interval from 300ms to 500ms
                } else {
                    console.log('❌ Max retries reached waiting for candidate_id, stopping polling');
                }
            };
            tryLoadRecs();
        } else {
            console.log('ℹ️ User not logged in, skipping personalized recommendations');
        }
    }

    const shouldLoadFreshData = !lastDataLoad || (now - parseInt(lastDataLoad)) > tenMinutes;
    const needsDataLoad = allInternships.length === 0 && !hasTriedInitialLoad;

    console.log('🔍 Initialization check:', {
        isInitialized,
        shouldLoadFreshData,
        needsDataLoad,
        lastDataLoad: lastDataLoad ? new Date(parseInt(lastDataLoad)).toLocaleTimeString() : 'none',
        internshipsLoaded: allInternships.length
    });

    if (!isInitialized && (shouldLoadFreshData || needsDataLoad)) {
        // Load general data first, then personalized recommendations
        console.log('📥 Loading fresh data...', {shouldLoadFreshData, needsDataLoad}); 
        isInitialized = true; // Mark as initialized to prevent re-execution
        hasTriedInitialLoad = true; // Prevent infinite loops
        loadAllData().then(() => {
            loadPersonalizedRecsWhenReady();
        });
        localStorage.setItem('lastDataLoad', now.toString());
    } else if (!isInitialized) {
        console.log('✅ Data was loaded recently and available, skipping auto-load');
        isInitialized = true; // Mark as initialized
        
        // Check if AI state exists but data is missing - clear AI state if so
        if (selectedInternshipIdForAI && allInternships.length === 0) {
            console.log('🧹 AI state exists but no data loaded, clearing AI recommendations');
            clearAiRecommendations();
        }
        
        // Data is available, just load personalized recommendations
        loadPersonalizedRecsWhenReady();
    } else {
        console.log('⚠️ Script already initialized, skipping data load');
    }

    checkLoginStatus();
    console.log('✅ App initialization complete');

    // Wire up right-panel toggle buttons
    const btnPers = document.getElementById('togglePersonalized');
    const btnSim = document.getElementById('toggleSimilar');
    if (btnPers && btnSim) {
        btnPers.addEventListener('click', () => setRightPanelMode('personalized'));
        btnSim.addEventListener('click', () => setRightPanelMode('similar'));
        // Initialize mode: default to personalized if logged in; otherwise similar
        const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
        rightPanelMode = isLoggedIn ? 'personalized' : 'similar';
        updateModeUI();
        if (rightPanelMode === 'personalized') {
            // Try to populate personalized after data
            const cid = localStorage.getItem('candidate_id');
            if (cid) loadPersonalizedRecommendations();
        } else {
            setRightPanelHeaderForSimilar(selectedInternshipIdForAI ? allInternships.find(i => i.internship_id === selectedInternshipIdForAI) : null);
            // Keep default empty similar state
        }
    }
});