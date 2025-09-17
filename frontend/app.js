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
      profileMsg.style.color = isError ? 'crimson' : 'var(--success)';
      if (!isError) setTimeout(()=>{ profileMsg.textContent = '' }, 5000);
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
        candidatesList.innerHTML = '<div class="empty">Start typing to search candidates.</div>';
        internshipsList.innerHTML = '<div class="empty">Start typing to search internships.</div>';
        clearRecommendations();
      } catch (err){
        alert('Error loading data: ' + err.message);
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
        candidatesList.innerHTML = '<div class="empty">No candidates match your search.</div>';
        candidatesShowMore.style.display = 'none';
        return;
      }
      candidatesCount.textContent = `${filtered.length} result(s)`;
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
              <div class="card-title">${escapeHtml(c.name || '—')}</div>
              <div class="small">ID: ${escapeHtml(c.candidate_id || '—')}</div>
            </div>
            <div class="small">${escapeHtml(c.location_preference || '—')}</div>
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
        internshipsList.innerHTML = '<div class="empty">No internships match your search.</div>';
        internShowMore.style.display = 'none';
        return;
      }
      internCount.textContent = `${filtered.length} result(s)`;
      const toShow = filtered.slice(0, internshipsLimit);

      const grid = document.createElement('div');
      grid.className = 'grid-2';

      for (const it of toShow){
        const div = document.createElement('div');
        div.className = 'card';
        div.innerHTML = `
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div>
              <div class="card-title">${escapeHtml(it.title)}</div>
              <div class="small">${escapeHtml(it.organization)} • ${escapeHtml(it.location)}</div>
            </div>
            <div class="small">${escapeHtml(it.sector||'—')}</div>
          </div>
          <div class="badges" style="margin-top:10px">
            ${(it.skills_required||[]).slice(0,8).map(s=>`<span class="badge">${escapeHtml(s)}</span>`).join('')}
          </div>
          <div class="small" style="margin-top:8px">${escapeHtml(it.description || '')}</div>
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
      recommendationsArea.innerHTML = '<div class="small">Loading recommendations…</div>';
      try {
        const res = await fetch(`${API_BASE}/recommendations/${encodeURIComponent(candidateId)}`);
        const json = await res.json();
        if (!res.ok) throw new Error(json.error || 'Failed to fetch recommendations');
        const recs = Array.isArray(json.recommendations) ? json.recommendations : [];
        renderRecommendations(candidateId, recs);
      } catch (err){
        recommendationsArea.innerHTML = `<div class="empty">Error fetching recommendations: ${escapeHtml(err.message)}</div><div class="note">If you just saved a profile and the server stores it in <code>profiles.json</code>, the recommendation endpoint may not find the candidate. Server should append new profiles into <code>candidates.json</code> or return the created candidate ID/object in the POST.</div>`;
      }
    }

    // render recommendations
    function renderRecommendations(candidateId, recs){
      recommendationsArea.innerHTML = '';
      if (!recs.length) {
        recommendationsArea.innerHTML = '<div class="empty">No recommended internships found for this candidate.</div>';
        return;
      }
      const candidate = candidates.find(c => c.candidate_id === candidateId) || {};
      const candSkills = (candidate.skills_possessed || []).map(s=>s.toLowerCase());
      for (const r of recs){
        const it = internships.find(i => i.internship_id === r.internship_id) || {};
        const internSkills = (it.skills_required || []).map(s=>s.toLowerCase());
        const matched = internSkills.filter(s=>candSkills.includes(s));
        const matchedHtml = matched.length ? matched.map(m=>`<span class="tag">${escapeHtml(m)}</span>`).join(' ') : '<span class="small">No exact skill match</span>';
        const block = document.createElement('div');
        block.className = 'recommendation';
        block.style.marginBottom = '8px';
        block.innerHTML = `
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div>
              <div class="card-title">${escapeHtml(r.title || it.title || '—')}</div>
              <div class="small">${escapeHtml(r.organization || it.organization || '')} • ${escapeHtml(it.location || r.location || '—')}</div>
            </div>
            <div class="small">Score: <span class="match">${escapeHtml(String(r.match_score ?? '0'))}</span></div>
          </div>
          <div style="margin-top:8px">${matchedHtml}</div>
          <div class="small" style="margin-top:8px">${escapeHtml(it.description || '')}</div>
        `;
        recommendationsArea.appendChild(block);
      }
      // scroll recommendations area to top for new results
      recommendationsWrapper.scrollTop = 0;
    }

    // clear recommendations
    function clearRecommendations(){
      recommendationsArea.innerHTML = '<div class="empty">Select a candidate (left) to see recommendations.</div>';
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
      console.log(`🎯 Auto-selecting candidate: ${candidateId} (${candidateName})`);
      
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
        console.log(`🔍 Candidate ${candidateId} not found by ID, trying name search`);
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
            const match = cardIdText.match(/ID:\s*(\w+)/);
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
          console.log(`📍 Found best match: ${candidateId}`);
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
        console.log(`🚀 Fetching recommendations for ${candidateId}`);
        await fetchRecommendations(candidateId);
        
        console.log(`✅ Successfully auto-selected and loaded recommendations for ${candidateId}`);
      } else {
        console.error(`❌ Could not find candidate card for ${candidateId}`);
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
        showProfileMessage('Please fill all fields', true);
        return;
      }
      
      saveProfileBtn.disabled = true;
      let createdCandidateId = null;
      
      try {
        console.log('🔄 Starting profile save process...');
        
        const candidate_id = 'CAND' + Date.now();
        const payload = {
          candidate_id,
          name,
          skills_possessed: skills,
          location_preference: location
        };
        
        showProfileMessage('Saving profile...');
        console.log('📤 Sending payload:', payload);
        
        const res = await fetch(`${API_BASE}/profile`, {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify(payload)
        });
        
        const json = await res.json();
        console.log('📥 Server response:', json);
        
        if (!res.ok) throw new Error(json.error || json.message || 'Failed to save profile');

        showProfileMessage('Profile saved successfully! Refreshing data...');
        
        // Get the created candidate ID from the response
        createdCandidateId = json.candidate?.candidate_id || json.candidate_id || candidate_id;
        const createdCandidateName = json.candidate?.name || name;
        
        console.log(`✅ Profile saved with ID: ${createdCandidateId}`);
        
        // Refresh the candidates list to include the new profile
        console.log('🔄 Refreshing candidate list...');
        await loadAll();
        
        // Auto-select and show recommendations for the new candidate
        showProfileMessage('Loading recommendations for new profile...');
        await autoSelectNewCandidate(createdCandidateId, createdCandidateName);
        
        showProfileMessage(`✅ Profile created successfully! ID: ${createdCandidateId}`);
        
        // Clear the form after successful save
        pName.value = '';
        pLocation.value = '';
        pSkills.value = '';
        
      } catch (err){
        console.error('❌ Profile save error:', err);
        showProfileMessage('Error saving profile: ' + err.message, true);
        
        // If we have a candidate ID but failed later, still try to load recommendations
        if (createdCandidateId) {
          console.log('🔄 Attempting recovery with candidate ID:', createdCandidateId);
          try {
            await loadAll();
            await autoSelectNewCandidate(createdCandidateId, name);
          } catch (recoveryErr) {
            console.error('❌ Recovery attempt failed:', recoveryErr);
          }
        }
      } finally {
        saveProfileBtn.disabled = false;
      }
    });

    resetProfileBtn.addEventListener('click', ()=>{
      pName.value = '';
      pLocation.value = '';
      pSkills.value = '';
      profileMsg.textContent = '';
    });

    // simple loading state: disable buttons when loading
    function setLoading(isLoading){
      document.querySelectorAll('button').forEach(b=>b.disabled = isLoading);
      // keep Clear buttons enabled
      document.getElementById('candidatesClear').disabled = false;
      document.getElementById('internshipsClear').disabled = false;
    }

    // initial fetch of data (but we do not render lists until user searches)
    loadAll();