// script.js: Modern client-side utilities for GreedyComicHub
// Features: Theme toggle, scroll-to-top, lazy loading, accessibility

// ============ THEME TOGGLE ============
(function initThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    const htmlElement = document.documentElement;
    const bodyElement = document.body;
    
    // Load theme from localStorage or system preference
    function loadTheme() {
        const savedTheme = localStorage.getItem('theme');
        
        if (savedTheme) {
            applyTheme(savedTheme);
        } else {
            // Check system preference
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            applyTheme(prefersDark ? 'dark' : 'light');
        }
    }
    
    function applyTheme(theme) {
        if (theme === 'light') {
            bodyElement.classList.add('light');
            if (themeToggle) themeToggle.textContent = '☀️';
            localStorage.setItem('theme', 'light');
        } else {
            bodyElement.classList.remove('light');
            if (themeToggle) themeToggle.textContent = '🌙';
            localStorage.setItem('theme', 'dark');
        }
    }
    
    // Initialize
    loadTheme();
    
    // Toggle on button click
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const isDarkMode = bodyElement.classList.contains('light');
            applyTheme(isDarkMode ? 'dark' : 'light');
        });
        
        // Keyboard shortcut: Alt + T
        document.addEventListener('keydown', (e) => {
            if (e.altKey && e.key === 't') {
                themeToggle.click();
            }
        });
    }
    
    // Sync theme across tabs
    window.addEventListener('storage', (e) => {
        if (e.key === 'theme') {
            applyTheme(e.newValue);
        }
    });
})();

// ============ SCROLL TO TOP ============
(function initScrollToTop() {
    const scrollBtn = document.getElementById('scroll-to-top');
    if (!scrollBtn) return;
    
    // Show/hide button based on scroll position
    window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
            scrollBtn.classList.add('show');
        } else {
            scrollBtn.classList.remove('show');
        }
    });
    
    // Smooth scroll to top
    scrollBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
})();

// ============ PROGRESS BAR ============
(function initProgressBar() {
    const progressBar = document.getElementById('progress-bar');
    if (!progressBar) return;
    
    window.addEventListener('scroll', () => {
        const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrolled = (window.scrollY / totalHeight) * 100;
        progressBar.style.width = scrolled + '%';
    });
})();

// ============ LAZY LOADING FALLBACK ============
(function initLazyLoading() {
    // For older browsers that don't support loading="lazy"
    if ('IntersectionObserver' in window) {
        const images = document.querySelectorAll('img[loading="lazy"]');
        
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                    }
                    observer.unobserve(img);
                }
            });
        }, {
            rootMargin: '50px'
        });
        
        images.forEach(img => imageObserver.observe(img));
    }
})();

// ============ READER AUTO-NEXT (OPTIONAL) ============
(function initReaderAutoNext() {
    const nextChapterLink = document.getElementById('next-chapter-bottom');
    if (!nextChapterLink || nextChapterLink.style.display === 'none') return;
    
    // Auto-load next chapter when scrolled to bottom
    if ('IntersectionObserver' in window) {
        const lastImage = document.querySelector('#reader .image-frame:last-child');
        if (!lastImage) return;
        
        const bottomObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    // Show hint or auto-navigate
                    // For now, just highlight the button
                    nextChapterLink.style.boxShadow = '0 0 20px rgba(0, 212, 255, 0.5)';
                }
            });
        });
        
        bottomObserver.observe(lastImage);
    }
})();

// ============ KEYBOARD NAVIGATION ============
(function initKeyboardNav() {
    document.addEventListener('keydown', (e) => {
        // Right arrow: Next chapter
        if (e.key === 'ArrowRight') {
            const nextLink = document.getElementById('next-chapter');
            if (nextLink && nextLink.style.display !== 'none') {
                nextLink.click();
            }
        }
        
        // Left arrow: Previous chapter
        if (e.key === 'ArrowLeft') {
            const prevLink = document.getElementById('prev-chapter');
            if (prevLink && prevLink.style.display !== 'none') {
                prevLink.click();
            }
        }
        
        // Escape: Go back to comic
        if (e.key === 'Escape') {
            const backLink = document.getElementById('back-to-comic');
            if (backLink) {
                backLink.click();
            }
        }
    });
})();

// ============ SEARCH ENHANCEMENT ============
(function initSearchEnhancement() {
    const searchBar = document.getElementById('search-bar');
    if (!searchBar) return;
    
    // Clear search on Escape
    searchBar.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            searchBar.value = '';
            searchBar.dispatchEvent(new Event('input'));
        }
    });
})();

// ============ ACCESSIBILITY IMPROVEMENTS ============
(function initAccessibility() {
    // Add skip-to-content link (optional)
    // Enhance keyboard navigation
    const links = document.querySelectorAll('a, button');
    links.forEach(link => {
        if (!link.getAttribute('aria-label') && !link.textContent.trim()) {
            // For images in links, ensure they have alt text
            const img = link.querySelector('img');
            if (img && img.alt) {
                link.setAttribute('aria-label', img.alt);
            }
        }
    });
})();

// ============ PINCH ZOOM FOR IMAGES (MOBILE) ============
(function initPinchZoom() {
    const reader = document.getElementById('reader');
    if (!reader) return;
    
    let currentScale = 1;
    let lastDistance = 0;
    
    reader.addEventListener('touchmove', (e) => {
        if (e.touches.length === 2) {
            const touch1 = e.touches[0];
            const touch2 = e.touches[1];
            const distance = Math.hypot(
                touch2.clientX - touch1.clientX,
                touch2.clientY - touch1.clientY
            );
            
            if (lastDistance > 0) {
                const scale = distance / lastDistance;
                currentScale = Math.min(Math.max(currentScale * scale, 1), 3);
                
                const images = reader.querySelectorAll('img');
                images.forEach(img => {
                    img.style.transform = `scale(${currentScale})`;
                });
            }
            
            lastDistance = distance;
            e.preventDefault();
        }
    }, { passive: false });
    
    reader.addEventListener('touchend', () => {
        lastDistance = 0;
        currentScale = 1;
        const images = reader.querySelectorAll('img');
        images.forEach(img => {
            img.style.transform = 'scale(1)';
        });
    });
})();

// ============ INITIALIZATION LOG ============
console.log('✓ GreedyComicHub modern scripts loaded successfully');