// Helper function to auto-scroll chat container to bottom
function scrollChatToBottom() {
    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

// Helper function to format relative time
function timeAgo(date) {
    const seconds = Math.floor((new Date() - new Date(date)) / 1000);
    
    let interval = seconds / 31536000;
    if (interval > 1) return Math.floor(interval) + " years ago";
    
    interval = seconds / 2592000;
    if (interval > 1) return Math.floor(interval) + " months ago";
    
    interval = seconds / 86400;
    if (interval > 1) return Math.floor(interval) + " days ago";
    
    interval = seconds / 3600;
    if (interval > 1) return Math.floor(interval) + " hours ago";
    
    interval = seconds / 60;
    if (interval > 1) return Math.floor(interval) + " minutes ago";
    
    return "just now";
}

// Initialize time ago for message timestamps
function initTimeAgo() {
    document.querySelectorAll('.time-ago').forEach(element => {
        const timestamp = element.getAttribute('data-timestamp');
        if (timestamp) {
            element.textContent = timeAgo(timestamp);
        }
    });
}

// Toggle vote button state
function toggleVoteButton(btn) {
    btn.classList.toggle('active');
    
    // Update vote count
    const voteCountEl = btn.querySelector('.vote-count');
    if (voteCountEl) {
        let count = parseInt(voteCountEl.textContent);
        if (btn.classList.contains('active')) {
            count += 1;
        } else {
            count -= 1;
        }
        voteCountEl.textContent = count;
    }
}

// Initialize textarea auto-resize
function initTextareaAutoResize() {
    document.querySelectorAll('textarea').forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    });
}

// Filter conversations by type
function initConversationFilters() {
    const filterLinks = document.querySelectorAll('[data-filter]');
    const conversationItems = document.querySelectorAll('.conversation-item');
    
    if (filterLinks.length === 0 || conversationItems.length === 0) {
        return; // Exit if elements don't exist
    }
    
    filterLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Update active state
            filterLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            
            const filter = this.getAttribute('data-filter');
            
            // Apply filter
            let visibleCount = 0;
            conversationItems.forEach(item => {
                if (filter === 'all' || item.getAttribute('data-type') === filter) {
                    item.classList.remove('d-none');
                    visibleCount++;
                } else {
                    item.classList.add('d-none');
                }
            });
            
            // Show/hide no results message
            const noResults = document.getElementById('no-results');
            if (noResults) {
                if (visibleCount === 0 && conversationItems.length > 0) {
                    noResults.classList.remove('d-none');
                } else {
                    noResults.classList.add('d-none');
                }
            }
        });
    });
}

// Search conversations
function initConversationSearch() {
    const searchInput = document.getElementById('conversation-search');
    const conversationItems = document.querySelectorAll('.conversation-item');
    
    if (!searchInput || conversationItems.length === 0) {
        return; // Exit if elements don't exist
    }
    
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase().trim();
        let visibleCount = 0;
        
        conversationItems.forEach(item => {
            const nameElement = item.querySelector('.conversation-name');
            const previewElement = item.querySelector('.conversation-preview');
            
            const name = nameElement ? nameElement.textContent.toLowerCase() : '';
            const preview = previewElement ? previewElement.textContent.toLowerCase() : '';
            
            if (name.includes(searchTerm) || preview.includes(searchTerm) || searchTerm === '') {
                item.classList.remove('d-none');
                visibleCount++;
            } else {
                item.classList.add('d-none');
            }
        });
        
        // Show/hide no results message
        const noResults = document.getElementById('no-results');
        if (noResults) {
            if (visibleCount === 0 && conversationItems.length > 0) {
                noResults.classList.remove('d-none');
            } else {
                noResults.classList.add('d-none');
            }
        }
    });
}

// Document ready function
document.addEventListener('DOMContentLoaded', function() {
    // Scroll chat to bottom when page loads
    scrollChatToBottom();
    
    // Initialize relative timestamps
    initTimeAgo();
    
    // Initialize textarea auto-resize
    initTextareaAutoResize();
    
    // Initialize conversation filters and search
    initConversationFilters();
    initConversationSearch();
    
    // Automatically submit message form when Enter is pressed (without Shift)
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('content');
    
    if (messageForm && messageInput) {
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (this.value.trim() !== '') {
                    messageForm.submit();
                }
            }
        });
    }
    
    // Enable Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
