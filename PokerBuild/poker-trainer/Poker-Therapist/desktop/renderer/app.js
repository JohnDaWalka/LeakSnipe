// Poker Therapist - Renderer Process

document.addEventListener('DOMContentLoaded', () => {
  initApp();
});

async function initApp() {
  setupNavigation();
  setupEventListeners();
  await checkBackendConnection();
  await loadDashboardData();
  
  // Listen for menu events
  window.api.onMenuSyncHands(() => {
    showView('sync');
    document.querySelector('[data-view="sync"]').click();
  });
}

// Navigation
function setupNavigation() {
  const navButtons = document.querySelectorAll('.nav-btn');
  
  navButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const viewId = btn.dataset.view;
      showView(viewId);
      
      // Update active state
      navButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });
}

function showView(viewId) {
  const views = document.querySelectorAll('.view');
  views.forEach(view => view.classList.remove('active'));
  
  const targetView = document.getElementById(`view-${viewId}`);
  if (targetView) {
    targetView.classList.add('active');
    
    // Load view-specific data
    if (viewId === 'tilt') {
      loadTiltAnalysis();
    }
  }
}

// Event Listeners
function setupEventListeners() {
  // Sync button
  document.getElementById('btn-sync').addEventListener('click', syncHands);
  
  // Search
  document.getElementById('btn-search').addEventListener('click', searchHands);
  document.getElementById('search-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') searchHands();
  });
  
  // Tilt refresh
  document.getElementById('btn-refresh-tilt').addEventListener('click', loadTiltAnalysis);
}

// Backend Connection
async function checkBackendConnection() {
  const statusDot = document.getElementById('connection-status');
  const statusText = document.getElementById('connection-text');
  
  try {
    const result = await window.api.checkHealth();
    
    if (result.status === 'ok' || result.status === 'healthy') {
      statusDot.classList.remove('offline');
      statusDot.classList.add('online');
      statusText.textContent = 'Connected';
      addAlert('Connected to Rex Poker Coach backend', 'info');
      return true;
    }
  } catch (error) {
    console.error('Connection check failed:', error);
  }
  
  statusDot.classList.remove('online');
  statusDot.classList.add('offline');
  statusText.textContent = 'Disconnected';
  addAlert('Cannot connect to backend. Ensure Rex Poker Coach is running on port 3001.', 'danger');
  return false;
}

// Dashboard Data
async function loadDashboardData() {
  try {
    const tiltData = await window.api.getTiltAnalysis();
    
    if (tiltData && tiltData.success !== false) {
      updateTiltMeter(tiltData.tiltLevel || tiltData.level || 0);
      document.getElementById('stat-hands').textContent = tiltData.handsAnalyzed || tiltData.hands || '--';
      
      if (tiltData.insight || tiltData.message) {
        document.getElementById('ai-insight').textContent = tiltData.insight || tiltData.message;
      }
    }
  } catch (error) {
    console.error('Failed to load dashboard data:', error);
  }
}

// Tilt Meter
function updateTiltMeter(level) {
  const meterFill = document.querySelector('.meter-fill');
  const tiltLevelText = document.getElementById('tilt-level');
  
  // Level is 0-100
  const percentage = Math.min(100, Math.max(0, level));
  meterFill.style.width = `${percentage}%`;
  
  // Determine text and class
  let levelClass = 'low';
  let levelText = 'Calm & Focused';
  
  if (percentage > 70) {
    levelClass = 'high';
    levelText = 'High Tilt - Consider Taking a Break';
  } else if (percentage > 40) {
    levelClass = 'medium';
    levelText = 'Moderate Tilt - Stay Aware';
  }
  
  tiltLevelText.textContent = levelText;
  tiltLevelText.className = `tilt-level ${levelClass}`;
}

// Hand Sync
async function syncHands() {
  const btn = document.getElementById('btn-sync');
  const statusDiv = document.getElementById('sync-status');
  const logArea = document.getElementById('sync-log');
  const limit = parseInt(document.getElementById('sync-limit').value) || 100;
  const recentOnly = document.getElementById('sync-recent').checked;
  
  // Disable button and show loading
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Syncing...';
  statusDiv.classList.remove('visible', 'success', 'error');
  
  // Add log entry
  addLogEntry(logArea, `Starting sync of ${limit} hands...`);
  
  try {
    const result = await window.api.syncHands({ limit, recentOnly });
    
    if (result.success) {
      statusDiv.textContent = `✓ Successfully synced ${result.count || limit} hands`;
      statusDiv.classList.add('visible', 'success');
      addLogEntry(logArea, `✓ Sync completed: ${result.count || limit} hands processed`);
      addAlert(`Synced ${result.count || limit} hands successfully`, 'info');
      
      // Update stats
      document.getElementById('stat-sync').textContent = new Date().toLocaleTimeString();
      
      // Refresh dashboard
      await loadDashboardData();
    } else {
      throw new Error(result.error || 'Sync failed');
    }
  } catch (error) {
    statusDiv.textContent = `✗ Error: ${error.message}`;
    statusDiv.classList.add('visible', 'error');
    addLogEntry(logArea, `✗ Error: ${error.message}`);
    addAlert(`Sync failed: ${error.message}`, 'danger');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span class="btn-icon">🔄</span> Start Sync';
  }
}

// Hand Search
async function searchHands() {
  const btn = document.getElementById('btn-search');
  const input = document.getElementById('search-input');
  const resultsDiv = document.getElementById('search-results');
  const position = document.getElementById('filter-position').value;
  const action = document.getElementById('filter-action').value;
  
  const query = input.value.trim();
  if (!query && !position && !action) {
    resultsDiv.innerHTML = '<p class="results-empty">Please enter a search query or select filters</p>';
    return;
  }
  
  btn.disabled = true;
  resultsDiv.innerHTML = '<p class="loading"><span class="spinner"></span> Searching...</p>';
  
  try {
    const result = await window.api.searchHands({ 
      query, 
      position, 
      action 
    });
    
    if (result.success && result.hands && result.hands.length > 0) {
      displaySearchResults(result.hands);
    } else if (result.hands && result.hands.length === 0) {
      resultsDiv.innerHTML = '<p class="results-empty">No hands found matching your criteria</p>';
    } else {
      throw new Error(result.error || 'Search failed');
    }
  } catch (error) {
    resultsDiv.innerHTML = `<p class="results-empty" style="color: var(--danger);">Error: ${error.message}</p>`;
  } finally {
    btn.disabled = false;
  }
}

function displaySearchResults(hands) {
  const resultsDiv = document.getElementById('search-results');
  
  if (!hands || hands.length === 0) {
    resultsDiv.innerHTML = '<p class="results-empty">No hands found</p>';
    return;
  }
  
  const html = hands.map(hand => `
    <div class="result-item" onclick="analyzeHand('${hand.id}')">
      <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
        <strong>${hand.position || 'Unknown'} - ${hand.action || 'Unknown Action'}</strong>
        <span style="color: var(--text-secondary);">${hand.date || ''}</span>
      </div>
      <div style="color: var(--text-secondary); font-size: 0.9rem;">
        ${hand.cards || hand.summary || 'No details available'}
      </div>
    </div>
  `).join('');
  
  resultsDiv.innerHTML = html;
}

// Tilt Analysis
async function loadTiltAnalysis() {
  const reportDiv = document.getElementById('tilt-report');
  const triggersDiv = document.getElementById('tilt-triggers');
  const recsDiv = document.getElementById('tilt-recommendations');
  
  reportDiv.innerHTML = '<p class="loading"><span class="spinner"></span> Analyzing...</p>';
  
  try {
    const result = await window.api.getTiltAnalysis();
    
    if (result.success !== false) {
      // Update report
      reportDiv.innerHTML = `
        <div style="margin-bottom: 1rem;">
          <strong>Tilt Score:</strong> 
          <span style="color: ${getTiltColor(result.tiltLevel || result.level || 0)}; font-size: 1.25rem;">
            ${result.tiltLevel || result.level || 0}/100
          </span>
        </div>
        <p>${result.analysis || result.message || 'Complete a hand sync to see detailed analysis.'}</p>
      `;
      
      // Update triggers
      if (result.triggers && result.triggers.length > 0) {
        triggersDiv.innerHTML = result.triggers.map(t => 
          `<li class="${t.active ? 'active' : ''}">${t.name || t}: ${t.description || ''}</li>`
        ).join('');
      } else {
        triggersDiv.innerHTML = '<li>No tilt triggers detected</li>';
      }
      
      // Update recommendations
      if (result.recommendations && result.recommendations.length > 0) {
        recsDiv.innerHTML = result.recommendations.map(r => 
          `<p style="margin-bottom: 0.5rem;">• ${r}</p>`
        ).join('');
      } else {
        recsDiv.innerHTML = '<p>You are playing well. Keep up the focus!</p>';
      }
      
      // Update dashboard tilt meter too
      updateTiltMeter(result.tiltLevel || result.level || 0);
    } else {
      throw new Error(result.error || 'Analysis failed');
    }
  } catch (error) {
    reportDiv.innerHTML = `<p style="color: var(--danger);">Error: ${error.message}</p>`;
  }
}

function getTiltColor(level) {
  if (level > 70) return 'var(--danger)';
  if (level > 40) return 'var(--warning)';
  return 'var(--success)';
}

// Analyze specific hand
async function analyzeHand(handId) {
  try {
    const result = await window.api.analyzeHand({ handId });
    
    if (result.success) {
      // Show analysis in an alert or modal
      addAlert(`Hand analysis: ${result.summary || 'Analysis complete'}`, 'info');
    }
  } catch (error) {
    addAlert(`Analysis error: ${error.message}`, 'danger');
  }
}

// Alerts
function addAlert(message, type = 'info') {
  const alertsList = document.getElementById('alerts-list');
  const alertItem = document.createElement('li');
  alertItem.className = `alert-item ${type}`;
  alertItem.textContent = message;
  
  // Add to top
  alertsList.insertBefore(alertItem, alertsList.firstChild);
  
  // Keep only last 5 alerts
  while (alertsList.children.length > 5) {
    alertsList.removeChild(alertsList.lastChild);
  }
}

// Log entries
function addLogEntry(logArea, message) {
  // Remove empty state if present
  const emptyState = logArea.querySelector('.log-empty');
  if (emptyState) {
    emptyState.remove();
  }
  
  const entry = document.createElement('div');
  entry.className = 'log-entry';
  entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
  logArea.appendChild(entry);
  logArea.scrollTop = logArea.scrollHeight;
}

// Periodic connection check
setInterval(checkBackendConnection, 30000);
