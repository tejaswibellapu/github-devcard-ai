const API_BASE = "http://localhost:8000";
// DOM Elements
const usernameInput = document.getElementById('username-input');
const generateBtn = document.getElementById('generate-btn');
const btnText = generateBtn.querySelector('.btn-text');
const btnLoader = generateBtn.querySelector('.btn-loader');
const loadingState = document.getElementById('loading-state');
const cardContainer = document.getElementById('card-container');
const actionButtons = document.getElementById('action-buttons');
const toast = document.getElementById('toast');

// Action Buttons
const copyUrlBtn = document.getElementById('copy-url-btn');
const downloadHtmlBtn = document.getElementById('download-html-btn');
const exportPngBtn = document.getElementById('export-png-btn');

let currentCardData = null;
let currentCardUrl = '';

// Helper: Show Toast
function showToast(message, duration = 3000) {
    toast.textContent = message;
    toast.classList.remove('hidden');
    toast.style.animation = 'none';
    toast.offsetHeight; // trigger reflow
    toast.style.animation = 'fadeIn 0.3s ease forwards';
    
    setTimeout(() => {
        toast.classList.add('hidden');
    }, duration);
}

// Helper: Set Loading State
function setLoading(isLoading) {
    if (isLoading) {
        generateBtn.disabled = true;
        btnText.classList.add('hidden');
        btnLoader.classList.remove('hidden');
        loadingState.classList.remove('hidden');
        cardContainer.classList.add('hidden');
        actionButtons.classList.add('hidden');
    } else {
        generateBtn.disabled = false;
        btnText.classList.remove('hidden');
        btnLoader.classList.add('hidden');
        loadingState.classList.add('hidden');
        cardContainer.classList.remove('hidden');
        actionButtons.classList.remove('hidden');
    }
}

// Component: Render Stats Grid
function createStatsGrid(stats) {
    return `
        <div class="stats-grid">
            <div class="stat-item">
                <span class="stat-value">${stats.total_stars || 0}</span>
                <span class="stat-label">Total Stars</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">${stats.public_repos || 0}</span>
                <span class="stat-label">Public Repos</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">${stats.followers || 0}</span>
                <span class="stat-label">Followers</span>
            </div>
        </div>
    `;
}

// Component: Render Skills Section
function createSkillsSection(skills) {
    const topLangs = skills.top_languages || [];
    const strongestSkills = skills.strongest_skills || [];
    
    const langBadges = topLangs.map(lang => `<span class="skill-badge">${lang}</span>`).join('');
    
    const skillBars = strongestSkills.slice(0, 3).map((skill, index) => `
        <div class="lang-item">
            <span class="lang-name">${skill}</span>
            <div class="lang-bar-container">
                <div class="lang-bar-fill" style="width: ${100 - (index * 15)}%"></div>
            </div>
        </div>
    `).join('');

    return `
        <div class="skills-section">
            <h3 class="section-title">Technical DNA</h3>
            <div class="skills-badges">${langBadges}</div>
            <div class="language-bars">${skillBars}</div>
        </div>
    `;
}

// Component: Render Featured Repos
function createReposGrid(repos) {
    const repoCards = repos.slice(0, 4).map(repo => `
        <div class="repo-card">
            <span class="repo-name">${repo.name}</span>
            <p class="repo-desc">${repo.description || 'No description provided.'}</p>
            <div class="repo-meta">
                <div class="repo-stars">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/></svg>
                    <span>${repo.stars || 0}</span>
                </div>
                <span>${repo.language || ''}</span>
            </div>
        </div>
    `).join('');

    return `
        <div class="repos-section">
            <h3 class="section-title">Featured Repositories</h3>
            <div class="repos-grid">${repoCards}</div>
        </div>
    `;
}

// Main Render Function
function renderCard(data) {
    const { profile, stats, skills, analysis, top_repos, theme } = data.card_data;
    currentCardData = data.card_data;
    currentCardUrl = `${window.location.origin}${data.image_url}`;

    const cardHTML = `
        <div id="dev-card" class="dev-card ${theme}">
            <div class="card-left">
                <img src="${profile.avatar_url}" alt="${profile.name}" class="card-avatar">
                <h2 class="card-name">${profile.name || profile.username}</h2>
                <span class="card-handle">@${profile.username}</span>
                <div class="hero-badge archetype-badge">${analysis.archetype || 'Developer'}</div>
                <p class="card-bio">${profile.bio || 'Building the future, one commit at a time.'}</p>
                <div class="card-location">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                    <span>${profile.location || 'The Internet'}</span>
                </div>
                <div id="qrcode" class="card-qr"></div>
            </div>
            <div class="card-right">
                ${createStatsGrid(stats)}
                ${createSkillsSection(skills)}
                ${createReposGrid(top_repos)}
                <div class="analysis-quote">
                    "${analysis.fun_insight}"
                </div>
            </div>
        </div>
    `;

    cardContainer.innerHTML = cardHTML;

    // Generate QR Code
    setTimeout(() => {
        new QRCode(document.getElementById("qrcode"), {
            text: `https://github.com/${profile.username}`,
            width: 84,
            height: 84,
            colorDark: "#000000",
            colorLight: "#ffffff",
            correctLevel: QRCode.CorrectLevel.H
        });
    }, 100);
}

// API Call
async function handleGenerate() {
    const username = usernameInput.value.trim();
    if (!username) {
        showToast("Please enter a GitHub username");
        return;
    }

    setLoading(true);

    try {
        const response = await fetch(`${API_BASE}/api/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
        });

        if (!response.ok) throw new Error("Failed to fetch data");

        const data = await response.json();
        
        if (data.card_data) {
            renderCard(data);
            showToast("Identity synthesized successfully");
        } else {
            throw new Error("Invalid data received");
        }
    } catch (error) {
        console.error(error);
        showToast("Error generating card. Please try again.");
    } finally {
        setLoading(false);
    }
}

// Actions
copyUrlBtn.addEventListener('click', () => {
    if (!currentCardUrl) return;
    navigator.clipboard.writeText(currentCardUrl).then(() => {
        showToast("Link copied to clipboard!");
    });
});

downloadHtmlBtn.addEventListener('click', async () => {
    if (!currentCardData) return;
    try {
        const response = await fetch(`${API_BASE}${currentCardUrl.replace(window.location.origin, '')}`);
        const html = await response.text();
        const blob = new Blob([html], { type: 'text/html' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${currentCardData.profile.username}-dev-card.html`;
        a.click();
        window.URL.revokeObjectURL(url);
        showToast("HTML downloaded successfully");
    } catch (e) {
        showToast("Failed to download HTML");
    }
});

exportPngBtn.addEventListener('click', () => {
    const card = document.getElementById('dev-card');
    if (!card) return;
    
    showToast("Preparing PNG export...");
    
    html2canvas(card, {
        useCORS: true,
        scale: 2,
        backgroundColor: null
    }).then(canvas => {
        const url = canvas.toDataURL('image/png');
        const a = document.createElement('a');
        a.href = url;
        a.download = `${currentCardData.profile.username}-dev-card.png`;
        a.click();
        showToast("PNG exported successfully");
    });
});

// Event Listeners
generateBtn.addEventListener('click', handleGenerate);
usernameInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleGenerate();
});

// Initial focus
usernameInput.focus();
