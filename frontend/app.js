// THEME TOGGLE FUNCTIONALITY - FIXED
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.querySelector('.theme-toggle');
    const htmlElement = document.documentElement;

    // Function to toggle theme
    function toggleTheme() {
        console.log('Theme toggle clicked!'); // Debug log
        const currentTheme = htmlElement.getAttribute('data-theme');
        console.log('Current theme:', currentTheme); // Debug log
        
        if (currentTheme === 'dark') {
            htmlElement.removeAttribute('data-theme');
            localStorage.setItem('theme', 'light');
            updateThemeIcon('light');
            console.log('Switched to light mode');
        } else {
            htmlElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
            updateThemeIcon('dark');
            console.log('Switched to dark mode');
        }
    }

    // Function to update the icon
    function updateThemeIcon(theme) {
        if (!themeToggle) return;
        
        const svg = themeToggle.querySelector('svg');
        if (!svg) return;
        
        if (theme === 'dark') {
            // Sun icon for when in dark mode (click to go light)
            svg.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/>`;
        } else {
            // Moon icon for when in light mode (click to go dark)
            svg.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/>`;
        }
    }

    // Add click event listener
    if (themeToggle) {
        console.log('Theme toggle button found, adding listener'); // Debug log
        themeToggle.addEventListener('click', toggleTheme);
    } else {
        console.log('Theme toggle button NOT found!'); // Debug log
    }

    // Load saved theme on page load
    const savedTheme = localStorage.getItem('theme');
    console.log('Saved theme:', savedTheme); // Debug log
    
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
let candidates = [];
let internships = [];
let selectedCandidateId = null;

// result limits
let candidatesLimit = 8;
let internshipsLimit = 8;

// UI refs
const candidatesList = document.getElementById('candidatesList');
const internshipsList = document.getElementById('internshipsList');
const recommendationsArea = document.getElementById('recommendationsArea');
const recommendationsWrapper = document.getElementById('recommendationsAreaWrapper');
const selectedCandidateLabel = document.getElementById('selectedCandidateLabel');
const candidatesCount = document.getElementById('candidatesCount');
const internCount = document.getElementById('internCount');

// search inputs
const searchName = document.getElementById('searchName');
const filterSkill = document.getElementById('filterSkill');
const filterLocation = document.getElementById('filterLocation');

const internSearch = document.getElementById('internSearch');
const internLocation = document.getElementById('internLocation');

// show-more buttons
const candidatesShowMore = document.getElementById('candidatesShowMore');
const internShowMore = document.getElementById('internShowMore');

// buttons
document.getElementById('reloadBtn').addEventListener('click', loadAll);
document.getElementById('candidatesClear').addEventListener('click', clearCandidateFilters);
document.getElementById('internshipsClear').addEventListener('click', clearInternFilters);

// profile elements
const profileForm = document.getElementById('profileForm');
const pName = document.getElementById('p_name');
const pLocation = document.getElementById('p_location');
const pSkills = document.getElementById('p_skills');
const saveProfileBtn = document.getElementById('saveProfileBtn');
const resetProfileBtn = document.getElementById('resetProfileBtn');
const profileMsg = document.getElementById('profileMsg');

// helpers
function debounce(fn, ms=200){
  let t;
  return (...args)=>{ clearTimeout(t); t = setTimeout(()=>fn(...args), ms); };
}

function escapeHtml(s){
  if (s === null || s === undefined) return '';
  return String(s).replace(/[&<>"'`=\/]/g, function(ch){
    return ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;','/':'&#x2F;','`':'&#x60;','=':'&#x3D;' })[ch];
  });
}

function showProfileMessage(msg, isError=false){
  profileMsg.textContent = msg;
  profileMsg.className = isError ? 'error-msg' : 'success-msg';
  profileMsg.style.display = 'block';
  if (!isError) setTimeout(()=>{ 
    profileMsg.style.display = 'none';
    profileMsg.textContent = '';
  }, 5000);
}

// initial load: fetch raw data (we don't render until searches typed)
async function loadAll(){
  setLoading(true);
  try {
    const [cRes, iRes] = await Promise.all([
      fetch(`${API_BASE}/candidates`),
      fetch(`${API_BASE}/internships`)
    ]);
    if (!cRes.ok) throw new Error('Failed to load candidates');
    if (!iRes.ok) throw new Error('Failed to load internships');
    const cjson = await cRes.json();
    const ijson = await iRes.json();
    candidates = Array.isArray(cjson.candidates) ? cjson.candidates : [];
    internships = Array.isArray(ijson.internships) ? ijson.internships : [];
    // reset UI counts and placeholders
    candidatesCount.textContent = 'No search yet';
    internCount.textContent = 'No search yet';
    candidatesList.innerHTML = '<div class="empty"><h3> Start Your Search</h3><p>Type a name, skill, or location to discover amazing candidates!</p></div>';
    internshipsList.innerHTML = '<div class="empty"><h3> Find Opportunities</h3><p>Search for internship titles, companies, or required skills!</p></div>';
    clearRecommendations();
  } catch (err){
    alert(' Error loading data: ' + err.message);
  } finally {
    setLoading(false);
  }
}

// filtering logic for candidates (search-first)
function getFilteredCandidates(){
  const q = (searchName.value||'').trim().toLowerCase();
  const skillQ = (filterSkill.value||'').trim().toLowerCase();
  const locQ = (filterLocation.value||'').trim().toLowerCase();

  if (!q && !skillQ && !locQ) return [];

  return candidates.filter(c=>{
    if (q && !((c.name||'').toLowerCase().includes(q))) return false;
    if (skillQ){
      const skills = (c.skills_possessed||[]).map(s=>s.toLowerCase());
      if (!skills.some(s=>s.includes(skillQ))) return false;
    }
    if (locQ && !((c.location_preference||'').toLowerCase().includes(locQ))) return false;
    return true;
  });
}

// filtering logic for internships
function getFilteredInternships(){
  const q = (internSearch.value||'').trim().toLowerCase();
  const locQ = (internLocation.value||'').trim().toLowerCase();
  if (!q && !locQ) return [];
  return internships.filter(it=>{
    const titleOk = q ? ((it.title||'').toLowerCase().includes(q) || (it.organization||'').toLowerCase().includes(q)) : true;
    if (!titleOk) {
      const skills = (it.skills_required||[]).map(s=>s.toLowerCase());
      if (!skills.some(s=>s.includes(q))) return false;
    }
    if (locQ && !((it.location||'').toLowerCase().includes(locQ))) return false;
    return true;
  });
}

// render candidates results (limited)
function renderCandidates(){
  const filtered = getFilteredCandidates();
  candidatesList.innerHTML = '';
  if (!filtered.length){
    candidatesCount.textContent = '0 results';
    candidatesList.innerHTML = '<div class="empty"><h3> No matches found</h3><p>Try different keywords or clear some filters!</p></div>';
    candidatesShowMore.style.display = 'none';
    return;
  }
  candidatesCount.textContent = ` ${filtered.length} candidate${filtered.length === 1 ? '' : 's'} found`;
  const toShow = filtered.slice(0, candidatesLimit);
  for (const c of toShow){
    const card = document.createElement('div');
    card.className = 'card';
    // Add selected class if this is the currently selected candidate
    if (selectedCandidateId === c.candidate_id) {
      card.classList.add('selected');
    }
    card.innerHTML = `
      <div class="card-header">
        <div>
          <div class="card-title"> ${escapeHtml(c.name || '—')}</div>
          <div class="small"> ${escapeHtml(c.candidate_id || '—')}</div>
        </div>
        <div class="small"> ${escapeHtml(c.location_preference || '—')}</div>
      </div>
      <div class="badges">${(c.skills_possessed||[]).slice(0,8).map(s=>`<span class="badge">${escapeHtml(s)}</span>`).join('')}</div>
    `;
    card.addEventListener('click', ()=> {
      // highlight card
      document.querySelectorAll('#candidatesList .card').forEach(x=>x.classList.remove('selected'));
      card.classList.add('selected');
      selectCandidate(c.candidate_id);
      fetchRecommendations(c.candidate_id);
    });
    candidatesList.appendChild(card);
  }
  if (filtered.length > candidatesLimit) candidatesShowMore.style.display = 'inline';
  else candidatesShowMore.style.display = 'none';
}

// render internships results (limited)
function renderInternships(){
  const filtered = getFilteredInternships();
  internshipsList.innerHTML = '';
  if (!filtered.length){
    internCount.textContent = '0 results';
    internshipsList.innerHTML = '<div class="empty"><h3> No opportunities found</h3><p>Try different search terms or locations!</p></div>';
    internShowMore.style.display = 'none';
    return;
  }
  internCount.textContent = ` ${filtered.length} internship${filtered.length === 1 ? '' : 's'} found`;
  const toShow = filtered.slice(0, internshipsLimit);

  const grid = document.createElement('div');
  grid.className = 'grid-2';

  for (const it of toShow){
    const div = document.createElement('div');
    div.className = 'card';
    div.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div>
          <div class="card-title"> ${escapeHtml(it.title)}</div>
          <div class="small"> ${escapeHtml(it.organization)} •  ${escapeHtml(it.location)}</div>
        </div>
        <div class="small"> ${escapeHtml(it.sector||'—')}</div>
      </div>
      <div class="badges" style="margin-top:10px">
        ${(it.skills_required||[]).slice(0,8).map(s=>`<span class="badge">${escapeHtml(s)}</span>`).join('')}
      </div>
      <div class="small" style="margin-top:8px;color:var(--text-muted)">${escapeHtml(it.description || '')}</div>
    `;
    grid.appendChild(div);
  }
  internshipsList.appendChild(grid);

  if (filtered.length > internshipsLimit) internShowMore.style.display = 'inline';
  else internShowMore.style.display = 'none';
}

// select candidate: update UI tag and store selected ID
function selectCandidate(candidateId){
  selectedCandidateId = candidateId;
  const c = candidates.find(x=>x.candidate_id === candidateId);
  selectedCandidateLabel.textContent = c ? `${c.name} (${c.candidate_id})` : candidateId;
}

// fetch recommendations from backend
async function fetchRecommendations(candidateId){
  if (!candidateId) return;
  recommendationsArea.innerHTML = '<div class="small" style="text-align:center;padding:2rem;"><div class="loading" style="position:relative;height:20px;"> AI is analyzing the perfect matches...</div></div>';
  try {
    const res = await fetch(`${API_BASE}/recommendations/${encodeURIComponent(candidateId)}`);
    const json = await res.json();
    if (!res.ok) throw new Error(json.error || 'Failed to fetch recommendations');
    const recs = Array.isArray(json.recommendations) ? json.recommendations : [];
    renderRecommendations(candidateId, recs);
  } catch (err){
    recommendationsArea.innerHTML = `<div class="empty"><h4> Oops! Something went wrong</h4><p>${escapeHtml(err.message)}</p><div class="note" style="margin-top:1rem"><strong>💡 Troubleshooting:</strong> If you just created a profile, make sure your backend properly saves it to <code>candidates.json</code> for the AI recommendations to work.</div></div>`;
  }
}

// render recommendations
function renderRecommendations(candidateId, recs){
  recommendationsArea.innerHTML = '';
  if (!recs.length) {
    recommendationsArea.innerHTML = '<div class="empty"><h4> No matches found</h4><p>Our AI couldn\'t find suitable internships for this candidate\'s profile. Try expanding the search criteria!</p></div>';
    return;
  }
  const candidate = candidates.find(c => c.candidate_id === candidateId) || {};
  const candSkills = (candidate.skills_possessed || []).map(s=>s.toLowerCase());
  
  for (const r of recs){
    const it = internships.find(i => i.internship_id === r.internship_id) || {};
    const internSkills = (it.skills_required || []).map(s=>s.toLowerCase());
    const matched = internSkills.filter(s=>candSkills.includes(s));
    const matchedHtml = matched.length ? matched.map(m=>`<span class="tag" style="background:var(--success);margin-right:4px">${escapeHtml(m)}</span>`).join(' ') : '<span class="small" style="color:var(--text-dim)">⚡ Skills match to be determined</span>';
    
    const block = document.createElement('div');
    block.className = 'recommendation';
    block.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
        <div>
          <div class="card-title"> ${escapeHtml(r.title || it.title || '—')}</div>
          <div class="small"> ${escapeHtml(r.organization || it.organization || '')} •  ${escapeHtml(it.location || r.location || '—')}</div>
        </div>
        <div class="small"> Score: <span class="match">${escapeHtml(String(r.match_score ?? '0'))}</span></div>
      </div>
      <div style="margin-bottom:8px"><strong> Matched Skills:</strong> ${matchedHtml}</div>
      <div class="small" style="color:var(--text-muted)">${escapeHtml(it.description || '')}</div>
    `;
    recommendationsArea.appendChild(block);
  }
  // scroll recommendations area to top for new results
  recommendationsWrapper.scrollTop = 0;
}

// clear recommendations
function clearRecommendations(){
  recommendationsArea.innerHTML = '<div class="empty"><h4> Smart Matching</h4><p>Select a candidate to see personalized internship recommendations powered by AI!</p></div>';
  selectedCandidateLabel.textContent = 'none';
  selectedCandidateId = null;
}

// clear filters
function clearCandidateFilters(){
  searchName.value = '';
  filterSkill.value = '';
  filterLocation.value = '';
  candidatesLimit = 8;
  renderCandidates();
}
function clearInternFilters(){
  internSearch.value = '';
  internLocation.value = '';
  internshipsLimit = 8;
  renderInternships();
}

// show more handlers
candidatesShowMore.addEventListener('click', ()=>{
  candidatesLimit += 8;
  renderCandidates();
});
internShowMore.addEventListener('click', ()=>{
  internshipsLimit += 8;
  renderInternships();
});

// hook input events (debounced)
const debCandidates = debounce(()=>{
  candidatesLimit = 8;
  renderCandidates();
}, 160);
searchName.addEventListener('input', debCandidates);
filterSkill.addEventListener('input', debCandidates);
filterLocation.addEventListener('input', debCandidates);

const debInterns = debounce(()=>{
  internshipsLimit = 8;
  renderInternships();
}, 160);
internSearch.addEventListener('input', debInterns);
internLocation.addEventListener('input', debInterns);

// Auto-select new candidate after creation
async function autoSelectNewCandidate(candidateId, candidateName) {
  console.log(` Auto-selecting candidate: ${candidateId} (${candidateName})`);
  
  // Clear all search filters first to ensure we can find the candidate
  searchName.value = '';
  filterSkill.value = '';
  filterLocation.value = '';
  
  // Wait a moment for any pending operations
  await new Promise(resolve => setTimeout(resolve, 50));
  
  // Search specifically by candidate ID to find the exact candidate
  searchName.value = candidateId;
  candidatesLimit = 20; // Increase limit to ensure we find it
  
  // Trigger search and wait for render
  renderCandidates();
  await new Promise(resolve => setTimeout(resolve, 100));
  
  // Find the candidate card by looking for the exact candidate ID
  let candidateCard = null;
  const allCards = document.querySelectorAll('#candidatesList .card');
  
  for (const card of allCards) {
    const idElement = card.querySelector('.small');
    if (idElement && idElement.textContent.includes(candidateId)) {
      candidateCard = card;
      break;
    }
  }
  
  // If not found by ID search, try by name
  if (!candidateCard) {
    console.log(` Candidate ${candidateId} not found by ID, trying name search`);
    searchName.value = candidateName;
    renderCandidates();
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Look for the most recent candidate with this name (highest timestamp in ID)
    let bestMatch = null;
    let bestTimestamp = 0;
    
    for (const card of document.querySelectorAll('#candidatesList .card')) {
      const idElement = card.querySelector('.small');
      if (idElement) {
        const cardIdText = idElement.textContent;
        const match = cardIdText.match(/\s*(\w+)/);
        if (match) {
          const cardId = match[1];
          // Extract timestamp from candidate ID (CAND + timestamp)
          const timestampMatch = cardId.match(/CAND(\d+)/);
          if (timestampMatch) {
            const timestamp = parseInt(timestampMatch[1]);
            if (timestamp > bestTimestamp) {
              bestTimestamp = timestamp;
              bestMatch = { card, candidateId: cardId };
            }
          }
        }
      }
    }
    
    if (bestMatch) {
      candidateCard = bestMatch.card;
      candidateId = bestMatch.candidateId; // Update to the actual found ID
      console.log(` Found best match: ${candidateId}`);
    }
  }
  
  if (candidateCard) {
    // Clear previous selections and select the new candidate
    document.querySelectorAll('#candidatesList .card').forEach(x => x.classList.remove('selected'));
    candidateCard.classList.add('selected');
    
    // Update UI state
    selectCandidate(candidateId);
    
    // Scroll the candidate into view
    candidateCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
    
    // Fetch recommendations
    console.log(` Fetching recommendations for ${candidateId}`);
    await fetchRecommendations(candidateId);
    
    console.log(` Successfully auto-selected and loaded recommendations for ${candidateId}`);
  } else {
    console.error(` Could not find candidate card for ${candidateId}`);
    // Fallback: just try to fetch recommendations by ID
    selectCandidate(candidateId);
    await fetchRecommendations(candidateId);
  }
}

// Save profile + try to get match - FIXED with preventDefault
profileForm.addEventListener('submit', async (event) => {
  event.preventDefault(); // Prevent form submission and page reload
  
  const name = (pName.value || '').trim();
  const location = (pLocation.value || '').trim();
  const skills = (pSkills.value || '').split(',').map(s=>s.trim()).filter(Boolean);
  
  if (!name || !location || !skills.length){
    showProfileMessage(' Please fill all fields with valid information', true);
    return;
  }
  
  saveProfileBtn.disabled = true;
  saveProfileBtn.textContent = ' Creating Profile...';
  let createdCandidateId = null;
  
  try {
    console.log(' Starting profile save process...');
    
    const candidate_id = 'CAND' + Date.now();
    const payload = {
      candidate_id,
      name,
      skills_possessed: skills,
      location_preference: location
    };
    
    showProfileMessage(' Creating your profile and preparing AI matching...');
    console.log(' Sending payload:', payload);
    
    const res = await fetch(`${API_BASE}/profile`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(payload)
    });
    
    const json = await res.json();
    console.log(' Server response:', json);
    
    if (!res.ok) throw new Error(json.error || json.message || 'Failed to save profile');

    showProfileMessage('✨ Profile created! Refreshing candidate database...');
    
    // Get the created candidate ID from the response
    createdCandidateId = json.candidate?.candidate_id || json.candidate_id || candidate_id;
    const createdCandidateName = json.candidate?.name || name;
    
    console.log(` Profile saved with ID: ${createdCandidateId}`);
    
    // Refresh the candidates list to include the new profile
    console.log(' Refreshing candidate list...');
    await loadAll();
    
    // Auto-select and show recommendations for the new candidate
    showProfileMessage(' AI is analyzing your profile for perfect matches...');
    await autoSelectNewCandidate(createdCandidateId, createdCandidateName);
    
    showProfileMessage(` Success! Your profile is ready and AI recommendations are loaded. ID: ${createdCandidateId}`);
    
    // Clear the form after successful save
    pName.value = '';
    pLocation.value = '';
    pSkills.value = '';
    
  } catch (err){
    console.error(' Profile save error:', err);
    showProfileMessage(' Failed to create profile: ' + err.message, true);
    
    // If we have a candidate ID but failed later, still try to load recommendations
    if (createdCandidateId) {
      console.log(' Attempting recovery with candidate ID:', createdCandidateId);
      try {
        await loadAll();
        await autoSelectNewCandidate(createdCandidateId, name);
      } catch (recoveryErr) {
        console.error(' Recovery attempt failed:', recoveryErr);
      }
    }
  } finally {
    saveProfileBtn.disabled = false;
    saveProfileBtn.textContent = ' Save + Get Match';
  }
});

resetProfileBtn.addEventListener('click', ()=>{
  pName.value = '';
  pLocation.value = '';
  pSkills.value = '';
  profileMsg.style.display = 'none';
  profileMsg.textContent = '';
});

// simple loading state: disable buttons when loading
function setLoading(isLoading){
  const panels = document.querySelectorAll('.panel');
  panels.forEach(panel => {
    if (isLoading) {
      panel.classList.add('loading');
    } else {
      panel.classList.remove('loading');
    }
  });
  
  document.querySelectorAll('button').forEach(b=>b.disabled = isLoading);
  // keep Clear buttons enabled
  document.getElementById('candidatesClear').disabled = false;
  document.getElementById('internshipsClear').disabled = false;
}

// initial fetch of data (but we do not render lists until user searches)
loadAll();