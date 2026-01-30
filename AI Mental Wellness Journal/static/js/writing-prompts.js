// Writing Prompts System for Mental Wellness Journal
// Provides therapeutic prompts to reduce writer's block

const WRITING_PROMPTS = {
    daily: [
        "What are you grateful for today?",
        "Describe a moment that made you smile",
        "What challenged you today, and how did you handle it?",
        "What's on your mind right now?",
        "How are you feeling emotionally and physically?"
    ],
    reflection: [
        "What patterns have you noticed in your mood lately?",
        "What activities bring you the most joy?",
        "What would you like to let go of?",
        "What are you proud of accomplishing recently?",
        "How have you grown in the past month?"
    ],
    goals: [
        "What are your priorities for this week?",
        "What small step can you take toward your goals?",
        "What obstacles are holding you back?",
        "How can you be kinder to yourself?",
        "What does success look like for you?"
    ],
    stress: [
        "What's causing you stress right now?",
        "What coping strategies have worked for you before?",
        "What can you control in this situation?",
        "Who can you reach out to for support?",
        "What would you tell a friend in this situation?"
    ],
    gratitude: [
        "List three things you're grateful for today",
        "Who made a positive impact on your life recently?",
        "What simple pleasure did you enjoy today?",
        "What opportunity are you thankful for?",
        "What about yourself are you grateful for?"
    ]
};

class WritingPromptsManager {
    constructor() {
        this.currentCategory = 'daily';
        this.usedPrompts = new Set();
    }

    getRandomPrompt(category = null) {
        const cat = category || this.currentCategory;
        const prompts = WRITING_PROMPTS[cat] || WRITING_PROMPTS.daily;

        // Filter out used prompts
        const availablePrompts = prompts.filter(p => !this.usedPrompts.has(p));

        // Reset if all prompts used
        if (availablePrompts.length === 0) {
            this.usedPrompts.clear();
            return prompts[Math.floor(Math.random() * prompts.length)];
        }

        const prompt = availablePrompts[Math.floor(Math.random() * availablePrompts.length)];
        this.usedPrompts.add(prompt);
        return prompt;
    }

    getAllCategories() {
        return Object.keys(WRITING_PROMPTS);
    }

    setCategory(category) {
        if (WRITING_PROMPTS[category]) {
            this.currentCategory = category;
        }
    }
}

// Initialize writing prompts UI
function initWritingPrompts() {
    const promptsContainer = document.getElementById('writingPromptsContainer');
    const journalTextarea = document.getElementById('journalContent');

    if (!promptsContainer) return;

    const manager = new WritingPromptsManager();

    // Create prompts UI
    const promptsHTML = `
        <div class="prompts-header">
            <h3>Writing Prompts</h3>
            <button id="refreshPromptBtn" class="btn-icon">
                <i class="fas fa-sync-alt"></i>
            </button>
        </div>
        <div class="prompts-categories">
            ${manager.getAllCategories().map(cat => `
                <button class="category-btn ${cat === 'daily' ? 'active' : ''}" data-category="${cat}">
                    ${cat.charAt(0).toUpperCase() + cat.slice(1)}
                </button>
            `).join('')}
        </div>
        <div class="prompt-display">
            <p id="currentPrompt">${manager.getRandomPrompt()}</p>
            <button id="usePromptBtn" class="btn-primary">
                <i class="fas fa-pen"></i> Use This Prompt
            </button>
        </div>
    `;

    promptsContainer.innerHTML = promptsHTML;

    // Event listeners
    const categoryButtons = promptsContainer.querySelectorAll('.category-btn');
    const refreshBtn = document.getElementById('refreshPromptBtn');
    const usePromptBtn = document.getElementById('usePromptBtn');
    const promptDisplay = document.getElementById('currentPrompt');

    categoryButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            categoryButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const category = btn.dataset.category;
            manager.setCategory(category);
            promptDisplay.textContent = manager.getRandomPrompt();
        });
    });

    refreshBtn.addEventListener('click', () => {
        promptDisplay.textContent = manager.getRandomPrompt();
        refreshBtn.querySelector('i').classList.add('fa-spin');
        setTimeout(() => {
            refreshBtn.querySelector('i').classList.remove('fa-spin');
        }, 500);
    });

    usePromptBtn.addEventListener('click', () => {
        if (journalTextarea) {
            const prompt = promptDisplay.textContent;
            journalTextarea.value = `${prompt}\n\n`;
            journalTextarea.focus();

            // Scroll to textarea
            journalTextarea.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    });
}

// Auto-initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWritingPrompts);
} else {
    initWritingPrompts();
}
