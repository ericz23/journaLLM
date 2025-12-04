/**
 * JournaLLM Frontend Application
 */

const API_BASE = '/api/chat';

// DOM Elements
const chatContainer = document.getElementById('chat-container');
const welcomeMessage = document.getElementById('welcome-message');
const chatForm = document.getElementById('chat-form');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const startDateInput = document.getElementById('start-date');
const endDateInput = document.getElementById('end-date');
const clearChatBtn = document.getElementById('clear-chat');

// State
let conversationHistory = [];
let isLoading = false;

// Initialize
function init() {
    // Set default dates (last 14 days)
    const today = new Date();
    const twoWeeksAgo = new Date(today);
    twoWeeksAgo.setDate(today.getDate() - 14);
    
    endDateInput.value = formatDate(today);
    startDateInput.value = formatDate(twoWeeksAgo);
    
    // Event listeners
    chatForm.addEventListener('submit', handleSubmit);
    messageInput.addEventListener('input', autoResize);
    messageInput.addEventListener('keydown', handleKeyDown);
    clearChatBtn.addEventListener('click', clearChat);
    
    // Auto-resize textarea on load
    autoResize.call(messageInput);
}

// Format date to YYYY-MM-DD
function formatDate(date) {
    return date.toISOString().split('T')[0];
}

// Format time for message display
function formatTime(date) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Auto-resize textarea
function autoResize() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
}

// Handle keyboard shortcuts
function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
}

// Handle form submission
async function handleSubmit(e) {
    e.preventDefault();
    
    const message = messageInput.value.trim();
    if (!message || isLoading) return;
    
    const startDate = startDateInput.value;
    const endDate = endDateInput.value;
    
    if (!startDate || !endDate) {
        showError('Please select both start and end dates.');
        return;
    }
    
    if (startDate > endDate) {
        showError('Start date must be before or equal to end date.');
        return;
    }
    
    // Hide welcome message
    if (welcomeMessage) {
        welcomeMessage.style.display = 'none';
    }
    
    // Add user message to UI
    addMessage('user', message);
    conversationHistory.push({ role: 'user', content: message });
    
    // Clear input
    messageInput.value = '';
    autoResize.call(messageInput);
    
    // Show loading indicator
    setLoading(true);
    const loadingEl = addLoadingIndicator();
    
    try {
        const response = await fetch(API_BASE + '/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                start_date: startDate,
                end_date: endDate,
                history: conversationHistory.slice(0, -1), // Exclude the message we just added
            }),
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Failed to get response');
        }
        
        const data = await response.json();
        
        // Remove loading indicator
        loadingEl.remove();
        
        // Add assistant message to UI
        addMessage('assistant', data.response);
        conversationHistory.push({ role: 'assistant', content: data.response });
        
    } catch (error) {
        console.error('Error:', error);
        loadingEl.remove();
        showError(error.message || 'An error occurred. Please try again.');
    } finally {
        setLoading(false);
    }
}

// Add a message to the chat
function addMessage(role, content) {
    const messageEl = document.createElement('div');
    messageEl.className = `message ${role}`;
    
    const bubbleEl = document.createElement('div');
    bubbleEl.className = 'message-bubble';
    bubbleEl.textContent = content;
    
    const timeEl = document.createElement('div');
    timeEl.className = 'message-time';
    timeEl.textContent = formatTime(new Date());
    
    messageEl.appendChild(bubbleEl);
    messageEl.appendChild(timeEl);
    
    chatContainer.appendChild(messageEl);
    scrollToBottom();
}

// Add loading indicator
function addLoadingIndicator() {
    const messageEl = document.createElement('div');
    messageEl.className = 'message assistant';
    
    const bubbleEl = document.createElement('div');
    bubbleEl.className = 'message-bubble typing-indicator';
    bubbleEl.innerHTML = '<span></span><span></span><span></span>';
    
    messageEl.appendChild(bubbleEl);
    chatContainer.appendChild(messageEl);
    scrollToBottom();
    
    return messageEl;
}

// Show error message
function showError(message) {
    const errorEl = document.createElement('div');
    errorEl.className = 'error-message';
    errorEl.textContent = message;
    
    chatContainer.appendChild(errorEl);
    scrollToBottom();
    
    // Remove after 5 seconds
    setTimeout(() => {
        errorEl.remove();
    }, 5000);
}

// Scroll to bottom of chat
function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Set loading state
function setLoading(loading) {
    isLoading = loading;
    sendBtn.disabled = loading;
    messageInput.disabled = loading;
}

// Clear chat
function clearChat() {
    conversationHistory = [];
    
    // Remove all messages except welcome
    const messages = chatContainer.querySelectorAll('.message, .error-message');
    messages.forEach(msg => msg.remove());
    
    // Show welcome message
    if (welcomeMessage) {
        welcomeMessage.style.display = 'flex';
    }
    
    messageInput.focus();
}

// Initialize app
init();

