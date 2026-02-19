document.addEventListener('DOMContentLoaded', () => {
    const robot = document.getElementById('ditto-robot');
    const container = document.getElementById('robot-container');

    if (!robot || !container) return;

    // Movement Configuration
    const sensitivity = 20; // Lower is more sensitive (inverse)

    document.addEventListener('mousemove', (e) => {
        const x = e.clientX;
        const y = e.clientY;

        const rect = robot.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;

        // Calculate distance from center
        const diffX = x - centerX;
        const diffY = y - centerY;

        // Calculate rotation angles
        // Move head/body towards cursor:
        // Cursor Right -> Rotate Y Positive
        // Cursor Down -> Rotate X Negative (tilt forward)
        const rotateY = (diffX / window.innerWidth) * 40; // Max 20deg rotation
        const rotateX = -(diffY / window.innerHeight) * 40;

        // Parallax/Translation effect (Hand 'reaching' illusion)
        const translateX = (diffX / window.innerWidth) * 10;
        const translateY = (diffY / window.innerHeight) * 10;

        // Apply Transform
        // precise 3D transform for "looking" effect
        robot.style.transform = `
            perspective(1000px)
            rotateX(${rotateX}deg) 
            rotateY(${rotateY}deg)
            translateX(${translateX}px)
            translateY(${translateY}px)
            scale(1.05) /* slight pop */
        `;
    });

    // Reset on mouse leave
    document.addEventListener('mouseleave', () => {
        robot.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale(1)';
    });
});
