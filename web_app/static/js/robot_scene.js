// Three.js Scene for FinCore Robot
const container = document.getElementById('canvas-container');

// Scene Setup
const scene = new THREE.Scene();
// Fog to blend into background
scene.fog = new THREE.FogExp2(0x050510, 0.002);

const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });

renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
container.appendChild(renderer.domElement);

// Lights
const ambientLight = new THREE.AmbientLight(0x404040, 2);
scene.add(ambientLight);

const pointLight = new THREE.PointLight(0x00f2ea, 2, 100);
pointLight.position.set(10, 10, 10);
scene.add(pointLight);

const pointLight2 = new THREE.PointLight(0xff0055, 2, 100);
pointLight2.position.set(-10, -10, 10);
scene.add(pointLight2);

// Robot Head (Procedural Group)
const robotGroup = new THREE.Group();
scene.add(robotGroup);

// Main Sphere (Head)
const geometry = new THREE.IcosahedronGeometry(2, 1); // Low poly look
const material = new THREE.MeshStandardMaterial({
    color: 0x111111,
    roughness: 0.2,
    metalness: 0.9,
    wireframe: false,
    flatShading: true
});
const head = new THREE.Mesh(geometry, material);
robotGroup.add(head);

// Wireframe Overlay
const wireGeo = new THREE.IcosahedronGeometry(2.1, 1);
const wireMat = new THREE.MeshBasicMaterial({ color: 0x00f2ea, wireframe: true, transparent: true, opacity: 0.1 });
const wire = new THREE.Mesh(wireGeo, wireMat);
robotGroup.add(wire);

// Eyes (Glowing)
const eyeGeo = new THREE.SphereGeometry(0.2, 16, 16);
const eyeMat = new THREE.MeshBasicMaterial({ color: 0x00f2ea });

const leftEye = new THREE.Mesh(eyeGeo, eyeMat);
leftEye.position.set(-0.8, 0.5, 1.8);
robotGroup.add(leftEye);

const rightEye = new THREE.Mesh(eyeGeo, eyeMat);
rightEye.position.set(0.8, 0.5, 1.8);
robotGroup.add(rightEye);

camera.position.z = 8;

// Mouse Interaction
let mouseX = 0;
let mouseY = 0;

document.addEventListener('mousemove', (event) => {
    mouseX = (event.clientX / window.innerWidth) * 2 - 1;
    mouseY = -(event.clientY / window.innerHeight) * 2 + 1;
});

// Animation Loop
const clock = new THREE.Clock();

function animate() {
    requestAnimationFrame(animate);

    const time = clock.getElapsedTime();

    // Idle Animation (Breathing/Floating)
    robotGroup.position.y = Math.sin(time) * 0.2;
    wire.rotation.y += 0.002;

    // Follow Mouse
    // Smooth LookAt
    const targetX = mouseX * 2;
    const targetY = mouseY * 2;

    robotGroup.rotation.y += 0.05 * (targetX - robotGroup.rotation.y);
    robotGroup.rotation.x += 0.05 * (targetY - robotGroup.rotation.x);

    renderer.render(scene, camera);
}

// Resize Handler
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

animate();
