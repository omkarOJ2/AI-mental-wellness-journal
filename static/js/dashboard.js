let sentimentChart = null;

// Load recent entries on page load
document.addEventListener('DOMContentLoaded', () => {
    loadRecentEntries();
    initializeChart();
});

// Journal form submission
document.getElementById('journalForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const content = document.getElementById('journalContent').value.trim();
    if (!content) return;

    const btn = document.getElementById('submitBtn');
    const analysisPreview = document.getElementById('analysisPreview');

    btn.classList.add('loading');

    try {
        const response = await fetch('/api/journal/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content })
        });

        const data = await response.json();

        if (data.success) {
            // Show analysis preview
            displayAnalysis(data.analysis);

            // Clear form
            document.getElementById('journalContent').value = '';

            // Reload entries
            await loadRecentEntries();

            // Show success message
            showNotification('Entry saved successfully!', 'success');
        } else {
            showNotification(data.error || 'Failed to save entry', 'error');
        }
    } catch (error) {
        showNotification('An error occurred. Please try again.', 'error');
    } finally {
        btn.classList.remove('loading');
    }
});

// Display sentiment analysis
function displayAnalysis(analysis) {
    const preview = document.getElementById('analysisPreview');

    const sentimentLabel = getSentimentLabel(analysis.sentiment_score);
    const emotionTags = analysis.emotions.map(e =>
        `<span class="emotion-tag">${e}</span>`
    ).join('');

    preview.innerHTML = `
        <div style="margin-bottom: 0.75rem;">
            <strong>Emotional Analysis:</strong>
            <span class="sentiment-score sentiment-${sentimentLabel.toLowerCase()}">
                ${sentimentLabel} (${analysis.sentiment_score.toFixed(2)})
            </span>
        </div>
        <div style="margin-bottom: 0.75rem;">
            <strong>Detected Emotions:</strong>
            <div class="emotion-tags">${emotionTags}</div>
        </div>
        <div>
            <strong>Insight:</strong> ${analysis.brief_insight}
        </div>
    `;

    // PHASE 4: Add chat button
    if (analysis.entry_id) {
        const chatBtn = document.createElement('button');
        chatBtn.className = 'chat-trigger-btn';
        chatBtn.innerHTML = '💬 Want to talk about this more?';
        chatBtn.onclick = () => openChatModal(analysis.entry_id);
        preview.appendChild(chatBtn);
    }

    preview.classList.add('show');

    // Hide after 15 seconds
    setTimeout(() => {
        preview.classList.remove('show');
    }, 15000);
}

// Load recent entries
async function loadRecentEntries() {
    const container = document.getElementById('recentEntries');

    try {
        const response = await fetch('/api/journal/entries');
        const data = await response.json();

        if (data.entries && data.entries.length > 0) {
            displayEntries(data.entries.slice(0, 10));
            updateChart(data.entries);
            updateMetrics(data.entries);
        } else {
            container.innerHTML = '<div class="loading-state">No entries yet. Start journaling!</div>';
        }
    } catch (error) {
        container.innerHTML = '<div class="loading-state">Failed to load entries</div>';
    }
}

// Calculate and Update Metrics
function updateMetrics(entries) {
    if (!entries || entries.length === 0) {
        document.getElementById('totalEntries').textContent = '0';
        document.getElementById('positiveMood').textContent = '0%';
        document.getElementById('weeklyEntries').textContent = '0';
        document.getElementById('currentStreak').textContent = '0 days';
        return;
    }

    // Total Entries
    document.getElementById('totalEntries').textContent = entries.length;

    // Positive Mood Percentage
    const positiveCount = entries.filter(e => e.sentiment_score > 0.3).length;
    const positivePercentage = Math.round((positiveCount / entries.length) * 100);
    document.getElementById('positiveMood').textContent = `${positivePercentage}%`;

    // This Week Entries
    const oneWeekAgo = new Date();
    oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
    const weeklyCount = entries.filter(e => new Date(e.created_at) >= oneWeekAgo).length;
    document.getElementById('weeklyEntries').textContent = weeklyCount;

    // Current Streak (consecutive days with entries)
    const sortedEntries = [...entries].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    let streak = 0;
    let currentDate = new Date();
    currentDate.setHours(0, 0, 0, 0);

    for (let entry of sortedEntries) {
        const entryDate = new Date(entry.created_at);
        entryDate.setHours(0, 0, 0, 0);

        const daysDiff = Math.floor((currentDate - entryDate) / (1000 * 60 * 60 * 24));

        if (daysDiff === streak) {
            streak++;
            currentDate.setDate(currentDate.getDate() - 1);
        } else if (daysDiff > streak) {
            break;
        }
    }

    document.getElementById('currentStreak').textContent = `${streak} day${streak !== 1 ? 's' : ''}`;
}

// Initialize sentiment chart
function initializeChart() {
    const ctx = document.getElementById('sentimentChart');

    sentimentChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Emotional Trend',
                data: [],
                borderColor: '#6366f1',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    min: -1,
                    max: 1,
                    ticks: {
                        callback: function (value) {
                            if (value > 0.3) return 'Positive';
                            if (value < -0.3) return 'Negative';
                            return 'Neutral';
                        }
                    }
                }
            }
        }
    });
}

// Update chart with entry data
function updateChart(entries) {
    if (!sentimentChart || !entries.length) return;

    const last7Days = entries.slice(0, 7).reverse();

    sentimentChart.data.labels = last7Days.map(e => {
        const date = new Date(e.created_at);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    sentimentChart.data.datasets[0].data = last7Days.map(e => e.sentiment_score);
    sentimentChart.update();
}

// Generate weekly report
document.getElementById('generateReportBtn').addEventListener('click', async () => {
    const btn = document.getElementById('generateReportBtn');
    const reportDiv = document.getElementById('weeklyReport');

    btn.classList.add('loading');
    reportDiv.innerHTML = '<div class="loading-state">Analyzing your week...</div>';
    reportDiv.classList.add('show');

    try {
        const response = await fetch('/api/weekly-report');
        const data = await response.json();

        if (data.report) {
            displayWeeklyReport(data.report);
        } else {
            reportDiv.innerHTML = `<div class="loading-state">${data.message}</div>`;
        }
    } catch (error) {
        reportDiv.innerHTML = '<div class="loading-state">Failed to generate report</div>';
    } finally {
        btn.classList.remove('loading');
    }
});

// Display weekly report
function displayWeeklyReport(report) {
    const reportDiv = document.getElementById('weeklyReport');

    const insights = report.key_insights.map(insight =>
        `<li>${insight}</li>`
    ).join('');

    const recommendations = report.recommendations.map(rec =>
        `<li>${rec}</li>`
    ).join('');

    reportDiv.innerHTML = `
        <div class="report-section">
            <h3>Overall Mood</h3>
            <p><strong>${report.overall_mood}</strong> - ${report.trajectory}</p>
        </div>
        
        <div class="report-section">
            <h3>Key Insights</h3>
            <ul>${insights}</ul>
        </div>
        
        <div class="report-section">
            <h3>Recommendations</h3>
            <ul>${recommendations}</ul>
        </div>
    `;
}

// Helper functions
function getSentimentLabel(score) {
    if (score > 0.3) return 'Positive';
    if (score < -0.3) return 'Negative';
    return 'Neutral';
}

function formatDate(date) {
    return date.toLocaleDateString('en-US', {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 2rem;
        right: 2rem;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? 'var(--success)' : 'var(--danger)'};
        color: white;
        border-radius: 8px;
        box-shadow: var(--shadow-lg);
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
    `;

    document.body.appendChild(notification);

    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Character Counter
const journalContent = document.getElementById('journalContent');
const characterCounter = document.getElementById('characterCounter');

journalContent.addEventListener('input', () => {
    const count = journalContent.value.length;
    characterCounter.textContent = `${count} character${count !== 1 ? 's' : ''}`;
});

// FIXED Voice Input - No Repetition + Multi-Language Support
let recognition = null;
let isRecording = false;

// Check if browser supports speech recognition
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();

    recognition.continuous = false; // FIXED: Changed to false to prevent repetition
    recognition.interimResults = false; // FIXED: Changed to false for cleaner results
    recognition.lang = 'en-US'; // Default language

    recognition.onstart = () => {
        isRecording = true;
        document.getElementById('voiceInputBtn').classList.add('recording');
        console.log('Voice recognition started');
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;

        // Simply append the new transcript to existing content
        const currentValue = journalContent.value;
        const newValue = currentValue + (currentValue ? ' ' : '') + transcript;

        journalContent.value = newValue;

        // Update character counter
        characterCounter.textContent = `${newValue.length} character${newValue.length !== 1 ? 's' : ''}`;
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        isRecording = false;
        document.getElementById('voiceInputBtn').classList.remove('recording');

        if (event.error === 'not-allowed') {
            showNotification('Microphone access denied. Please allow microphone access.', 'error');
        } else if (event.error === 'no-speech') {
            showNotification('No speech detected. Please try again.', 'error');
        } else {
            showNotification('Voice recognition error. Please try again.', 'error');
        }
    };

    recognition.onend = () => {
        isRecording = false;
        document.getElementById('voiceInputBtn').classList.remove('recording');
        console.log('Voice recognition ended');
    };
}

// Voice input button click handler
document.getElementById('voiceInputBtn').addEventListener('click', () => {
    if (!recognition) {
        showNotification('Voice input is not supported in your browser. Please use Chrome, Edge, or Safari.', 'error');
        return;
    }

    // Get selected language
    const langSelect = document.getElementById('voiceLangSelect');
    if (langSelect) {
        recognition.lang = langSelect.value;
    }

    if (isRecording) {
        recognition.stop();
    } else {
        recognition.start();
    }
});

// Edit Modal Character Counter
const editContent = document.getElementById('editContent');
const editCharacterCounter = document.getElementById('editCharacterCounter');

editContent.addEventListener('input', () => {
    const count = editContent.value.length;
    editCharacterCounter.textContent = `${count} character${count !== 1 ? 's' : ''}`;
});

// Search and Filter
const searchInput = document.getElementById('searchInput');
const sentimentFilter = document.getElementById('sentimentFilter');

let searchTimeout;
searchInput.addEventListener('input', () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        performSearch();
    }, 500);
});

sentimentFilter.addEventListener('change', () => {
    performSearch();
});

async function performSearch() {
    const query = searchInput.value.trim();
    const sentiment = sentimentFilter.value;

    const container = document.getElementById('recentEntries');
    container.innerHTML = '<div class="loading-state">Searching...</div>';

    try {
        let url = '/api/journal/search?';
        if (query) url += `q=${encodeURIComponent(query)}&`;
        if (sentiment) url += `sentiment=${sentiment}&`;

        const response = await fetch(url);
        const data = await response.json();

        if (data.entries && data.entries.length > 0) {
            displayEntries(data.entries);
        } else {
            container.innerHTML = '<div class="loading-state">No entries found</div>';
        }
    } catch (error) {
        container.innerHTML = '<div class="loading-state">Search failed</div>';
    }
}

// Display entries with edit/delete buttons
function displayEntries(entries) {
    const container = document.getElementById('recentEntries');

    container.innerHTML = entries.map(entry => {
        const date = new Date(entry.created_at);
        const sentimentLabel = getSentimentLabel(entry.sentiment_score);

        return `
            <div class="entry-item">
                <div class="entry-date">${formatDate(date)}</div>
                <div class="entry-content">${entry.content}</div>
                <div class="entry-sentiment">
                    <span>Mood:</span>
                    <span class="sentiment-score sentiment-${sentimentLabel.toLowerCase()}">
                        ${sentimentLabel}
                    </span>
                    <div class="emotion-tags">
                        ${entry.emotions.slice(0, 3).map(e =>
            `<span class="emotion-tag">${e}</span>`
        ).join('')}
                    </div>
                </div>
                <div class="entry-actions">
                    <button class="btn btn-small btn-edit" onclick="openEditModal(${entry.id}, '${entry.content.replace(/'/g, "\\'")}')">
                        ✏️ Edit
                    </button>
                    <button class="btn btn-small btn-delete" onclick="deleteEntry(${entry.id})">
                        🗑️ Delete
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// Edit Modal Functions
let currentEditId = null;

function openEditModal(entryId, content) {
    currentEditId = entryId;
    const modal = document.getElementById('editModal');
    const editContent = document.getElementById('editContent');

    editContent.value = content;
    editCharacterCounter.textContent = `${content.length} character${content.length !== 1 ? 's' : ''}`;

    modal.classList.add('show');
}

function closeEditModal() {
    const modal = document.getElementById('editModal');
    modal.classList.remove('show');
    currentEditId = null;
}

// Edit Form Submission
document.getElementById('editForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const content = document.getElementById('editContent').value.trim();
    if (!content || !currentEditId) return;

    const btn = e.target.querySelector('.btn-primary');
    btn.classList.add('loading');

    try {
        const response = await fetch(`/api/journal/update/${currentEditId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content })
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Entry updated successfully!', 'success');
            closeEditModal();
            await loadRecentEntries();
        } else {
            showNotification(data.error || 'Failed to update entry', 'error');
        }
    } catch (error) {
        showNotification('An error occurred. Please try again.', 'error');
    } finally {
        btn.classList.remove('loading');
    }
});

// Delete Entry
async function deleteEntry(entryId) {
    if (!confirm('Are you sure you want to delete this entry? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`/api/journal/delete/${entryId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            showNotification('Entry deleted successfully', 'success');
            await loadRecentEntries();
        } else {
            showNotification(data.error || 'Failed to delete entry', 'error');
        }
    } catch (error) {
        showNotification('An error occurred. Please try again.', 'error');
    }
}

// Export JSON
document.getElementById('exportJsonBtn').addEventListener('click', async () => {
    try {
        const response = await fetch('/api/export/json');
        const blob = await response.blob();

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `journal_export_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showNotification('Journal exported successfully!', 'success');
    } catch (error) {
        showNotification('Failed to export journal', 'error');
    }
});

// Enhanced Weekly Report Display
function displayWeeklyReport(report) {
    const reportDiv = document.getElementById('weeklyReport');

    const insights = report.key_insights.map(insight =>
        `<li>${insight}</li>`
    ).join('');

    const recommendations = report.recommendations.map(rec =>
        `<li>${rec}</li>`
    ).join('');

    // Mood distribution HTML
    let moodDistributionHTML = '';
    if (report.mood_distribution) {
        moodDistributionHTML = `
            <div class="report-section">
                <h3>Mood Distribution</h3>
                <div class="mood-distribution">
                    <div class="mood-stat positive">
                        <div class="mood-stat-number">${report.mood_distribution.positive}</div>
                        <div class="mood-stat-label">Positive Days</div>
                    </div>
                    <div class="mood-stat neutral">
                        <div class="mood-stat-number">${report.mood_distribution.neutral}</div>
                        <div class="mood-stat-label">Neutral Days</div>
                    </div>
                    <div class="mood-stat negative">
                        <div class="mood-stat-number">${report.mood_distribution.negative}</div>
                        <div class="mood-stat-label">Challenging Days</div>
                    </div>
                </div>
            </div>
        `;
    }

    // Best/Worst day highlights
    let dayHighlightsHTML = '';
    if (report.best_day && report.worst_day) {
        dayHighlightsHTML = `
            <div class="report-section">
                <h3>Week Highlights</h3>
                <div class="day-highlight best">
                    <div class="day-highlight-title">🌟 Best Day</div>
                    <div class="day-highlight-date">${report.best_day.date} (Score: ${report.best_day.score.toFixed(2)})</div>
                    <div class="day-highlight-preview">"${report.best_day.content_preview}"</div>
                </div>
                <div class="day-highlight worst">
                    <div class="day-highlight-title">💪 Most Challenging Day</div>
                    <div class="day-highlight-date">${report.worst_day.date} (Score: ${report.worst_day.score.toFixed(2)})</div>
                    <div class="day-highlight-preview">"${report.worst_day.content_preview}"</div>
                </div>
            </div>
        `;
    }

    reportDiv.innerHTML = `
        <div class="report-section">
            <h3>Overall Mood</h3>
            <p><strong>${report.overall_mood}</strong> - ${report.trajectory}</p>
        </div>
        
        ${moodDistributionHTML}
        
        ${dayHighlightsHTML}
        
        <div class="report-section">
            <h3>Key Insights</h3>
            <ul>${insights}</ul>
        </div>
        
        <div class="report-section">
            <h3>Recommendations</h3>
            <ul>${recommendations}</ul>
        </div>
    `;
}

// Update loadRecentEntries to use displayEntries
async function loadRecentEntries() {
    const container = document.getElementById('recentEntries');

    try {
        const response = await fetch('/api/journal/entries');
        const data = await response.json();

        if (data.entries && data.entries.length > 0) {
            displayEntries(data.entries.slice(0, 10));
            updateChart(data.entries);
            updateMetrics(data.entries);
        } else {
            container.innerHTML = '<div class="loading-state">No entries yet. Start journaling!</div>';
        }
    } catch (error) {
        container.innerHTML = '<div class="loading-state">Failed to load entries</div>';
    }
}

// Make functions global for onclick handlers
window.openEditModal = openEditModal;
window.closeEditModal = closeEditModal;
window.deleteEntry = deleteEntry;

// Auto-save Draft
let autoSaveTimeout;
const AUTOSAVE_DELAY = 3000; // 3 seconds

journalContent.addEventListener('input', () => {
    clearTimeout(autoSaveTimeout);
    autoSaveTimeout = setTimeout(() => {
        saveDraft();
    }, AUTOSAVE_DELAY);
});

async function saveDraft() {
    const content = journalContent.value.trim();
    if (!content) return;

    try {
        await fetch('/api/draft/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ content })
        });
        // Silent save - no notification
    } catch (error) {
        console.error('Failed to save draft:', error);
    }
}

// Load Draft on Page Load
async function loadDraft() {
    try {
        const response = await fetch('/api/draft/load');
        const data = await response.json();

        if (data.content) {
            const shouldLoad = confirm('You have an unsaved draft. Would you like to restore it?');
            if (shouldLoad) {
                journalContent.value = data.content;
                characterCounter.textContent = `${data.content.length} character${data.content.length !== 1 ? 's' : ''}`;
            }
        }
    } catch (error) {
        console.error('Failed to load draft:', error);
    }
}

// Clear draft after successful submission
const originalSubmit = document.getElementById('journalForm').onsubmit;
document.getElementById('journalForm').addEventListener('submit', async (e) => {
    // After successful submission, clear draft
    const content = document.getElementById('journalContent').value.trim();
    if (content) {
        try {
            await fetch('/api/draft/clear', { method: 'DELETE' });
        } catch (error) {
            console.error('Failed to clear draft:', error);
        }
    }
});

// Load draft on page load
loadDraft();

// Writing Timer
let writingStartTime = null;
let writingTimer = null;
let totalWritingTime = 0;

// Create timer element
const timerElement = document.createElement('div');
timerElement.className = 'writing-timer';
timerElement.id = 'writingTimer';
timerElement.textContent = 'Writing time: 0:00';
characterCounter.parentElement.insertBefore(timerElement, characterCounter.nextSibling);

journalContent.addEventListener('focus', () => {
    if (!writingStartTime) {
        writingStartTime = Date.now();
        timerElement.classList.add('timer-active');

        writingTimer = setInterval(() => {
            const elapsed = Math.floor((Date.now() - writingStartTime) / 1000) + totalWritingTime;
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            timerElement.textContent = `Writing time: ${minutes}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }
});

journalContent.addEventListener('blur', () => {
    if (writingStartTime) {
        totalWritingTime += Math.floor((Date.now() - writingStartTime) / 1000);
        writingStartTime = null;
        clearInterval(writingTimer);
        timerElement.classList.remove('timer-active');
    }
});

// Reset timer on form submission
document.getElementById('journalForm').addEventListener('submit', () => {
    totalWritingTime = 0;
    writingStartTime = null;
    clearInterval(writingTimer);
    timerElement.textContent = 'Writing time: 0:00';
    timerElement.classList.remove('timer-active');
});

// Week-over-Week Comparison
async function loadWeekComparison() {
    const container = document.getElementById('weekComparison');

    try {
        const response = await fetch('/api/weekly-comparison');
        const data = await response.json();

        if (data.error) {
            container.innerHTML = '<div class="loading-state">Unable to load comparison</div>';
            return;
        }

        const arrow = data.trend === 'improving' ? '📈' : data.trend === 'declining' ? '📉' : '➡️';
        const changeText = data.change > 0 ? `+${data.change}` : data.change;
        const percentText = data.change_percent > 0 ? `+${data.change_percent}%` : `${data.change_percent}%`;

        container.innerHTML = `
            <div class="week-stat">
                <div class="week-stat-label">Last Week</div>
                <div class="week-stat-value">${data.last_week.avg_sentiment.toFixed(2)}</div>
                <div class="week-stat-count">${data.last_week.entry_count} entries</div>
            </div>
            
            <div class="week-stat">
                <div class="week-stat-label">This Week</div>
                <div class="week-stat-value">${data.this_week.avg_sentiment.toFixed(2)}</div>
                <div class="week-stat-count">${data.this_week.entry_count} entries</div>
            </div>
            
            <div class="comparison-summary ${data.trend}">
                ${arrow} ${changeText} (${percentText}) - Your mood is ${data.trend}
            </div>
        `;
    } catch (error) {
        container.innerHTML = '<div class="loading-state">Failed to load comparison</div>';
    }
}

// Load week comparison on page load
document.addEventListener('DOMContentLoaded', () => {
    loadWeekComparison();
});

// PDF Export
document.getElementById('exportPdfBtn').addEventListener('click', async () => {
    try {
        const response = await fetch('/api/export/pdf');
        const blob = await response.blob();

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `journal_export_${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showNotification('Journal exported successfully!', 'success');
    } catch (error) {
        showNotification('Failed to export journal', 'error');
    }
});
