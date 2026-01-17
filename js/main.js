document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initCopyButtons();
    initAnimations();
    initFooter();
    hljs.highlightAll();
});

/* --- Footer Management --- */
function initFooter() {
    const footerText = document.querySelector('footer p');
    if (footerText) {
        const year = new Date().getFullYear();
        footerText.innerHTML = `&copy; ${year} MRC Project for Sunil Mishra.`;
    }
}

/* --- Theme Management --- */
function initTheme() {
    const themeToggle = document.getElementById('theme-toggle');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    // Load saved theme or default to system preference
    const savedTheme = localStorage.getItem('theme');
    const currentTheme = savedTheme ? savedTheme : (prefersDark ? 'dark' : 'light');

    document.documentElement.setAttribute('data-theme', currentTheme);
    updateToggleIcon(currentTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const newTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateToggleIcon(newTheme);
        });
    }
}

function updateToggleIcon(theme) {
    const themeToggle = document.getElementById('theme-toggle');
    if (!themeToggle) return;
    // Use Font Awesome icons
    themeToggle.innerHTML = theme === 'dark' ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
    themeToggle.setAttribute('aria-label', `Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`);
}

/* --- Copy Code Functionality --- */
function initCopyButtons() {
    const codeBlocks = document.querySelectorAll('pre');

    codeBlocks.forEach(block => {
        // Create button
        const button = document.createElement('button');
        button.className = 'copy-btn';
        button.textContent = 'Copy';
        button.setAttribute('aria-label', 'Copy code to clipboard');

        button.addEventListener('click', async () => {
            const code = block.querySelector('code')?.innerText || block.innerText;
            try {
                await navigator.clipboard.writeText(code);
                const originalText = button.textContent;
                button.textContent = 'Copied!';
                setTimeout(() => {
                    button.textContent = originalText;
                }, 2000);
            } catch (err) {
                console.error('Failed to copy class:', err);
                button.textContent = 'Error';
            }
        });

        block.appendChild(button);
    });
}

/* --- GSAP Animations --- */
function initAnimations() {
    // Check if GSAP is loaded
    if (typeof gsap === 'undefined') {
        console.warn('GSAP not loaded');
        return;
    }

    gsap.registerPlugin(ScrollTrigger);

    // Animate elements with .fade-in class
    const fadeElements = document.querySelectorAll('.fade-in');
    fadeElements.forEach(el => {
        gsap.to(el, {
            scrollTrigger: {
                trigger: el,
                start: "top 80%", // Component triggers when top of element hits 80% of viewport
                toggleActions: "play none none reverse"
            },
            opacity: 1,
            y: 0,
            duration: 0.8,
            ease: "power2.out"
        });
    });

    // Stagger animation for lists or grids if present
    const grids = document.querySelectorAll('.stagger-grid');
    grids.forEach(grid => {
        gsap.from(grid.children, {
            scrollTrigger: {
                trigger: grid,
                start: "top 85%"
            },
            y: 30,
            opacity: 0,
            duration: 0.6,
            stagger: 0.1,
            ease: "back.out(1.7)"
        });
    });
}
