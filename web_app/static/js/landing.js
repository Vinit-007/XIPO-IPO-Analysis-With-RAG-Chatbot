/**
 * XIPO Landing Page Logic
 * - Cursor Trails
 * - Search Interaction
 * - Spline Integration
 */

/* --- Enhanced Fading Cursor Logic --- */
const CURSOR_CONFIG = {
    friction: 0.5,
    trails: 20,
    size: 30,
    dampening: 0.2,
    tension: 0.98
};

class Node {
    constructor() {
        this.x = 0;
        this.y = 0;
        this.vx = 0;
        this.vy = 0;
    }
}

class TrailLine {
    constructor(spring, index) {
        this.spring = spring + 0.1 * Math.random() - 0.02;
        this.friction = CURSOR_CONFIG.friction + 0.01 * Math.random() - 0.002;
        // Varying blue/indigo hues for the "filament" look
        const hue = 210 + (index * 2);
        this.color = `hsla(${hue}, 80%, 60%, ${0.2 - (index * 0.01)})`;
        this.nodes = [];
        for (let i = 0; i < CURSOR_CONFIG.size; i++) {
            this.nodes.push(new Node());
        }
    }

    update(pos) {
        let e = this.spring;
        let t = this.nodes[0];
        t.vx += (pos.x - t.x) * e;
        t.vy += (pos.y - t.y) * e;
        for (let i = 0; i < this.nodes.length; i++) {
            t = this.nodes[i];
            if (i > 0) {
                const n = this.nodes[i - 1];
                t.vx += (n.x - t.x) * e;
                t.vy += (n.y - t.y) * e;
                t.vx += n.vx * CURSOR_CONFIG.dampening;
                t.vy += n.vy * CURSOR_CONFIG.dampening;
            }
            t.vx *= this.friction;
            t.vy *= this.friction;
            t.x += t.vx;
            t.y += t.vy;
            e *= CURSOR_CONFIG.tension;
        }
    }

    draw(ctx) {
        let n = this.nodes[0].x, i = this.nodes[0].y;
        ctx.beginPath();
        ctx.moveTo(n, i);
        ctx.strokeStyle = this.color;
        for (let a = 1; a < this.nodes.length - 2; a++) {
            const e = this.nodes[a], t = this.nodes[a + 1];
            n = 0.5 * (e.x + t.x);
            i = 0.5 * (e.y + t.y);
            ctx.quadraticCurveTo(e.x, e.y, n, i);
        }
        const last = this.nodes[this.nodes.length - 2], end = this.nodes[this.nodes.length - 1];
        ctx.quadraticCurveTo(last.x, last.y, end.x, end.y);
        ctx.stroke();
        ctx.closePath();
    }
}

class CursorController {
    constructor() {
        this.canvas = document.getElementById('cursor-trail');
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d');
        this.pos = { x: 0, y: 0 };
        this.lines = [];
        this.raf = null;

        this.init();
    }

    init() {
        this.resize();
        this.lines = Array.from({ length: CURSOR_CONFIG.trails }, (_, i) => new TrailLine(0.4 + (i / CURSOR_CONFIG.trails) * 0.025, i));

        window.addEventListener('resize', () => this.resize());
        window.addEventListener('mousemove', (e) => this.onMove(e));
        window.addEventListener('touchmove', (e) => this.onMove(e));

        this.render();
    }

    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    onMove(e) {
        if (e.touches) {
            this.pos.x = e.touches[0].pageX;
            this.pos.y = e.touches[0].pageY;
        } else {
            this.pos.x = e.clientX;
            this.pos.y = e.clientY;
        }
    }

    render() {
        this.ctx.globalCompositeOperation = 'source-over';
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.globalCompositeOperation = 'lighter';
        this.ctx.lineWidth = 1.5;

        this.lines.forEach(line => {
            line.update(this.pos);
            line.draw(this.ctx);
        });
        this.raf = requestAnimationFrame(() => this.render());
    }
}

/* --- App Logic --- */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Cursor
    new CursorController();

    // 2. Search Logic
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');
    const loadingIcon = document.getElementById('loading-icon');
    const searchIcon = document.getElementById('search-icon');
    const submitBtn = document.getElementById('submit-btn');

    const handleSearch = async (e) => {
        if (e) e.preventDefault();
        const query = searchInput.value.trim();
        if (!query) return;

        // UI State: Loading
        submitBtn.disabled = true;
        searchIcon.style.display = 'none';
        loadingIcon.style.display = 'block';

        // Trigger Analysis Pipeline
        // We will store the name in session storage and redirect to dashboard
        // Just like the legacy main.js did, but smoother.
        try {
            sessionStorage.setItem('companyName', query);

            // Optional: Call analyze API first to ensure it starts? 
            // Or just redirect to dashboard which handles it (as per legacy main.js logic).
            // Legacy main.js logic: if companyName in sessionStorage, dashboard starts analysis.

            // Simulate a short delay for effect?
            await new Promise(r => setTimeout(r, 800));

            window.location.href = '/dashboard?new_analysis=true';

        } catch (error) {
            console.error("Search failed:", error);
            submitBtn.disabled = false;
            searchIcon.style.display = 'block';
            loadingIcon.style.display = 'none';
        }
    };

    if (searchForm) {
        searchForm.addEventListener('submit', handleSearch);
    }

    // Quick Shortcuts
    document.querySelectorAll('.quick-link').forEach(link => {
        link.addEventListener('click', () => {
            searchInput.value = link.dataset.term;
            handleSearch();
        });
    });
});
