// Cursor Trail Effect with Fading Lines
document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('cursor-trail');
    const ctx = canvas.getContext('2d');

    // Set canvas size
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    // Resize canvas on window resize
    window.addEventListener('resize', () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });

    // Trail configuration
    const trail = [];
    const maxTrailLength = 30;
    const lineWidth = 2;

    // Mouse position
    let mouseX = 0;
    let mouseY = 0;

    // Custom cursor dot
    const cursorDot = document.createElement('div');
    cursorDot.style.cssText = `
        position: fixed;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: linear-gradient(135deg, #00f2ea, #7c3aed);
        pointer-events: none;
        z-index: 10000;
        box-shadow: 0 0 20px rgba(0, 242, 234, 0.6);
        transform: translate(-50%, -50%);
    `;
    document.body.appendChild(cursorDot);

    // Track mouse movement
    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;

        // Update cursor dot position
        cursorDot.style.left = mouseX + 'px';
        cursorDot.style.top = mouseY + 'px';

        // Add point to trail
        trail.push({
            x: mouseX,
            y: mouseY,
            age: 0
        });

        // Limit trail length
        if (trail.length > maxTrailLength) {
            trail.shift();
        }
    });

    // Animation loop
    function animate() {
        // Clear canvas (transparent background for trail effect)
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Update and draw trail
        for (let i = 0; i < trail.length; i++) {
            const point = trail[i];
            point.age++;

            if (i > 0) {
                const prevPoint = trail[i - 1];

                // Calculate opacity based on age
                const opacity = 1 - (point.age / maxTrailLength);

                // Create gradient for line
                const gradient = ctx.createLinearGradient(
                    prevPoint.x, prevPoint.y,
                    point.x, point.y
                );

                gradient.addColorStop(0, `rgba(0, 242, 234, ${opacity * 0.8})`);
                gradient.addColorStop(0.5, `rgba(124, 58, 237, ${opacity * 0.6})`);
                gradient.addColorStop(1, `rgba(0, 170, 255, ${opacity * 0.4})`);

                // Draw line
                ctx.beginPath();
                ctx.moveTo(prevPoint.x, prevPoint.y);
                ctx.lineTo(point.x, point.y);
                ctx.strokeStyle = gradient;
                ctx.lineWidth = lineWidth * opacity;
                ctx.lineCap = 'round';
                ctx.stroke();

                // Add glow effect
                ctx.shadowBlur = 15 * opacity;
                ctx.shadowColor = 'rgba(0, 242, 234, 0.5)';
            }
        }

        // Remove old points
        trail.forEach((point, index) => {
            if (point.age > maxTrailLength) {
                trail.splice(index, 1);
            }
        });

        requestAnimationFrame(animate);
    }

    animate();

    // Hide cursor dot when mouse leaves window
    document.addEventListener('mouseleave', () => {
        cursorDot.style.opacity = '0';
    });

    document.addEventListener('mouseenter', () => {
        cursorDot.style.opacity = '1';
    });
});
