/**
 * FYP Recommendation System - JavaScript
 * Handles AJAX requests, form validation, and interactive features
 */

// ============================================
// DOM Ready Event
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    initializeEvents();
    initializeFormValidation();
    initializeAnimations();
});

// ============================================
// Event Handlers
// ============================================

function initializeEvents() {
    // Toggle skill via AJAX
    document.querySelectorAll('[data-toggle-skill]').forEach(el => {
        el.addEventListener('click', function(e) {
            e.preventDefault();
            toggleSkillAjax(this);
        });
    });
    
    // Save project
    document.querySelectorAll('[data-save-project]').forEach(el => {
        el.addEventListener('click', function(e) {
            e.preventDefault();
            saveProjectAjax(this);
        });
    });
    
    // Bookmark project
    document.querySelectorAll('[data-bookmark]').forEach(el => {
        el.addEventListener('click', function(e) {
            e.preventDefault();
            bookmarkProjectAjax(this);
        });
    });
}

// ============================================
// AJAX Functions
// ============================================

/**
 * Toggle skill selection via AJAX
 */
function toggleSkillAjax(element) {
    const skillId = element.getAttribute('data-toggle-skill');
    const skillName = element.textContent;
    
    fetch('/api/toggle-skill/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ skill_id: skillId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Toggle visual state
            element.classList.toggle('active');
            showNotification(`${skillName} ${data.added ? 'added' : 'removed'}!`, 'success');
        } else {
            showNotification('Error updating skill', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Network error occurred', 'error');
    });
}

/**
 * Save project to student's list
 */
function saveProjectAjax(element) {
    const projectId = element.getAttribute('data-save-project');
    const btn = element;
    const originalText = btn.textContent;
    
    btn.disabled = true;
    btn.textContent = '⏳ Saving...';
    
    fetch('/save-project/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ project_id: projectId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            btn.textContent = '✓ Saved';
            btn.classList.add('saved');
            showNotification('Project saved successfully!', 'success');
        } else {
            btn.textContent = originalText;
            btn.disabled = false;
            showNotification('Error saving project', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        btn.textContent = originalText;
        btn.disabled = false;
        showNotification('Network error occurred', 'error');
    });
}

/**
 * Bookmark project
 */
function bookmarkProjectAjax(element) {
    const projectId = element.getAttribute('data-bookmark');
    const isBookmarked = element.classList.contains('bookmarked');
    
    fetch('/api/bookmark/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ 
            project_id: projectId,
            action: isBookmarked ? 'remove' : 'add'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            element.classList.toggle('bookmarked');
            element.innerHTML = data.bookmarked ? '❤️' : '🤍';
            showNotification(data.bookmarked ? 'Bookmarked!' : 'Removed from bookmarks', 'success');
        }
    })
    .catch(error => console.error('Error:', error));
}

// ============================================
// Form Validation
// ============================================

function initializeFormValidation() {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                showNotification('Please fix the errors in the form', 'error');
            }
        });
    });
}

function validateForm(form) {
    let isValid = true;
    
    form.querySelectorAll('input, select, textarea').forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });
    
    return isValid;
}

function validateField(field) {
    const value = field.value.trim();
    const type = field.type;
    
    // Required field
    if (field.required && !value) {
        markFieldError(field, 'This field is required');
        return false;
    }
    
    // Email validation
    if (type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            markFieldError(field, 'Invalid email address');
            return false;
        }
    }
    
    // Number validation
    if (type === 'number' && value) {
        if (isNaN(value)) {
            markFieldError(field, 'Must be a number');
            return false;
        }
    }
    
    clearFieldError(field);
    return true;
}

function markFieldError(field, message) {
    field.classList.add('error');
    const errorEl = document.createElement('span');
    errorEl.className = 'error-message';
    errorEl.textContent = message;
    
    const existing = field.parentElement.querySelector('.error-message');
    if (existing) existing.remove();
    field.parentElement.appendChild(errorEl);
}

function clearFieldError(field) {
    field.classList.remove('error');
    const errorEl = field.parentElement.querySelector('.error-message');
    if (errorEl) errorEl.remove();
}

// ============================================
// Animations
// ============================================

function initializeAnimations() {
    // Fade in animations for elements with data-fade attribute
    document.querySelectorAll('[data-fade]').forEach((el, idx) => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        setTimeout(() => {
            el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        }, 100 * idx);
    });
    
    // Counter animations
    document.querySelectorAll('[data-counter]').forEach(el => {
        const target = parseInt(el.getAttribute('data-counter'), 10);
        animateCounter(el, target);
    });
}

function animateCounter(element, target) {
    let current = 0;
    const step = Math.ceil(target / 50);
    const interval = setInterval(() => {
        current += step;
        if (current >= target) {
            element.textContent = target;
            clearInterval(interval);
        } else {
            element.textContent = current;
        }
    }, 20);
}

// ============================================
// Notifications
// ============================================

function showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container');
    if (!container) return;
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    container.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ============================================
// Utility Functions
// ============================================

/**
 * Get CSRF token from cookies
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Scroll to element smoothly
 */
function scrollToElement(selector) {
    const element = document.querySelector(selector);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}

/**
 * Format date string
 */
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-US', options);
}
