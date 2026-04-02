// Enhanced Three.js effects for Daniel Ramirez's interactive resume
// This file extends the basic Three.js implementation in script.js

// Global variables for Three.js effects
let cloudModel;
let particles;
let waveMesh;
let halftoneEffect;
let drippingParticles = [];
let clock;
let noiseShader;

// Initialize enhanced Three.js effects
function initEnhancedThreeEffects() {
    // Initialize clock for animations
    clock = new THREE.Clock();
    
    // Create cloud model
    createCloudModel();
    
    // Create wave distortion effect
    createWaveDistortion();
    
    // Create halftone dot effect
    createHalftoneEffect();
    
    // Create dripping paint effect
    createDrippingEffect();
    
    // Add noise shader
    addNoiseShader();
}

// Update cloud material color
function createCloudModel() {
    // Create cloud geometry
    const cloudGeometry = new THREE.SphereGeometry(1.2, 32, 32);
    
    // Create cloud material - UPDATED COLOR
    const cloudMaterial = new THREE.MeshStandardMaterial({
        color: 0xe2e3d8, // Changed to LUFS light key
        roughness: 0.7,
        metalness: 0.1,
        emissive: 0xe2e3d8, // Changed to LUFS light key
        emissiveIntensity: 0.2
    });
    
    // Create cloud mesh
    cloudModel = new THREE.Mesh(cloudGeometry, cloudMaterial);
    cloudModel.position.set(0, 0, -2);
    cloudModel.scale.set(1, 0.9, 0.8);
    threeScene.add(cloudModel);
    
    // Add eyes to cloud
    const eyeGeometry = new THREE.SphereGeometry(0.2, 16, 16);
    const eyeMaterial = new THREE.MeshBasicMaterial({ color: 0x111111 }); // Changed to LUFS black key
    
    const leftEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
    leftEye.position.set(-0.4, 0.1, 0.9);
    cloudModel.add(leftEye);
    
    const rightEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
    rightEye.position.set(0.4, 0.1, 0.9);
    cloudModel.add(rightEye);
}

// Update wave distortion effect colors
function createWaveDistortion() {
    // Create plane geometry
    const waveGeometry = new THREE.PlaneGeometry(10, 10, 128, 128);
    
    // Create wave material with custom shader - UPDATED COLORS
    const waveMaterial = new THREE.ShaderMaterial({
        uniforms: {
            time: { value: 0 },
            amplitude: { value: 0.1 },
            frequency: { value: 0.5 },
            color1: { value: new THREE.Color(0x78BEBA) }, // Changed from 0x00E0E0 to LUFS teal
            color2: { value: new THREE.Color(0xD35233) }  // Changed from 0xFF6600 to LUFS red
        },
        vertexShader: `
            uniform float time;
            uniform float amplitude;
            uniform float frequency;
            
            varying vec2 vUv;
            varying float vElevation;
            
            void main() {
                vUv = uv;
                
                float elevation = sin(position.x * frequency + time) * 
                                 sin(position.y * frequency + time) * amplitude;
                
                vElevation = elevation;
                
                vec3 newPosition = position;
                newPosition.z += elevation;
                
                gl_Position = projectionMatrix * modelViewMatrix * vec4(newPosition, 1.0);
            }
        `,
        fragmentShader: `
            uniform vec3 color1;
            uniform vec3 color2;
            
            varying vec2 vUv;
            varying float vElevation;
            
            void main() {
                float mixStrength = (vElevation + 0.1) * 5.0;
                vec3 color = mix(color1, color2, mixStrength);
                
                gl_FragColor = vec4(color, 0.7);
            }
        `,
        transparent: true,
        side: THREE.DoubleSide
    });
    
    // Create wave mesh
    waveMesh = new THREE.Mesh(waveGeometry, waveMaterial);
    waveMesh.rotation.x = -Math.PI / 2;
    waveMesh.position.y = -2;
    waveMesh.visible = false; // Initially hidden
    threeScene.add(waveMesh);
}

// Update halftone effect colors
function createHalftoneEffect() {
    // Create particles for halftone effect
    const halftoneGeometry = new THREE.BufferGeometry();
    const halftoneCount = 2000;
    const positions = new Float32Array(halftoneCount * 3);
    const sizes = new Float32Array(halftoneCount);
    
    // Create grid of dots
    const gridSize = Math.sqrt(halftoneCount);
    const spacing = 4 / gridSize;
    
    for (let i = 0; i < halftoneCount; i++) {
        const x = (i % gridSize) * spacing - 2;
        const y = Math.floor(i / gridSize) * spacing - 2;
        const z = -5;
        
        positions[i * 3] = x;
        positions[i * 3 + 1] = y;
        positions[i * 3 + 2] = z;
        
        sizes[i] = 0.05;
    }
    
    halftoneGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    halftoneGeometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
    
    // Create shader material for halftone dots - UPDATED COLOR
    const halftoneShader = new THREE.ShaderMaterial({
        uniforms: {
            color: { value: new THREE.Color(0x78BEBA) }, // Changed from 0x00E0E0 to LUFS teal
            pointTexture: { value: new THREE.TextureLoader().load('https://threejs.org/examples/textures/sprites/circle.png') },
            time: { value: 0 },
            audioLevel: { value: 0 }
        },
        vertexShader: `
            attribute float size;
            
            uniform float time;
            uniform float audioLevel;
            
            varying vec3 vColor;
            
            void main() {
                vColor = vec3(0.47, 0.75, 0.73); // Updated to match 78BEBA (LUFS teal)
                
                // Calculate dot size based on position and audio
                float distanceFromCenter = length(position.xy);
                float sizeFactor = sin(distanceFromCenter * 2.0 - time) * 0.5 + 0.5;
                sizeFactor = sizeFactor * (1.0 + audioLevel * 2.0);
                
                vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
                gl_PointSize = size * sizeFactor * (300.0 / -mvPosition.z);
                gl_Position = projectionMatrix * mvPosition;
            }
        `,
        fragmentShader: `
            uniform vec3 color;
            uniform sampler2D pointTexture;
            
            varying vec3 vColor;
            
            void main() {
                gl_FragColor = vec4(vColor, 1.0) * texture2D(pointTexture, gl_PointCoord);
                
                if (gl_FragColor.a < 0.3) discard;
            }
        `,
        transparent: true,
        depthWrite: false
    });
    
    // Create points
    halftoneEffect = new THREE.Points(halftoneGeometry, halftoneShader);
    halftoneEffect.visible = false; // Initially hidden
    threeScene.add(halftoneEffect);
}

// Create dripping paint effect
function createDrippingEffect() {
    // Create dripping particles
    for (let i = 0; i < 100; i++) {
        createDrip();
    }
}

// Update dripping paint effect colors
function createDrip() {
    // Random position
    const x = (Math.random() - 0.5) * 6;
    const y = 3;
    const z = (Math.random() - 0.5) * 6 - 2;
    
    // Random drip properties
    const size = Math.random() * 0.1 + 0.05;
    const speed = Math.random() * 0.02 + 0.01;
    const length = Math.random() * 0.5 + 0.2;
    
    // Create drip geometry
    const dripGeometry = new THREE.CylinderGeometry(size, size, length, 8);
    dripGeometry.translate(0, -length / 2, 0);
    
    // Create drip material with random color between LUFS colors - UPDATED COLORS
    const colorMix = Math.random();
    let color;
    
    // Randomly select between the four brand colors
    const colorChoice = Math.floor(Math.random() * 4);
    switch(colorChoice) {
        case 0:
            color = new THREE.Color(0x78BEBA); // LUFS teal
            break;
        case 1:
            color = new THREE.Color(0xD35233); // LUFS red
            break;
        case 2:
            color = new THREE.Color(0xE7B225); // LUFS yellow
            break;
        case 3:
            color = new THREE.Color(0x2C5AA0); // LUFS blue
            break;
    }
    
    const dripMaterial = new THREE.MeshBasicMaterial({
        color: color,
        transparent: true,
        opacity: 0.7
    });
    
    // Create drip mesh
    const drip = new THREE.Mesh(dripGeometry, dripMaterial);
    drip.position.set(x, y, z);
    
    // Add custom properties
    drip.userData = {
        speed: speed,
        originalY: y,
        maxDistance: Math.random() * 5 + 3
    };
    
    // Add to scene and array
    threeScene.add(drip);
    drippingParticles.push(drip);
}

// Add noise shader to scene
function addNoiseShader() {
    // Create noise pass
    const noisePass = new THREE.ShaderPass({
        uniforms: {
            tDiffuse: { value: null },
            amount: { value: 0.08 },
            time: { value: 0 }
        },
        vertexShader: `
            varying vec2 vUv;
            
            void main() {
                vUv = uv;
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
        `,
        fragmentShader: `
            uniform sampler2D tDiffuse;
            uniform float amount;
            uniform float time;
            
            varying vec2 vUv;
            
            float random(vec2 co) {
                return fract(sin(dot(co.xy, vec2(12.9898, 78.233))) * 43758.5453);
            }
            
            void main() {
                vec4 color = texture2D(tDiffuse, vUv);
                
                vec2 uvNoise = vUv;
                uvNoise.y *= random(vec2(uvNoise.y, time));
                
                color.rgb += random(uvNoise) * amount;
                
                gl_FragColor = color;
            }
        `
    });
    
    // Add noise pass to composer
    composer.addPass(noisePass);
    
    // Store shader for updating
    noiseShader = noisePass;
}

// Update enhanced Three.js effects
function updateEnhancedThreeEffects() {
    // Get elapsed time
    const elapsedTime = clock.getElapsedTime();
    
    // Get audio level if available
    let audioLevel = 0;
    if (analyser && isPlaying) {
        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        analyser.getByteFrequencyData(dataArray);
        
        // Calculate average level
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
            sum += dataArray[i];
        }
        audioLevel = sum / (dataArray.length * 255);
    } else {
        // Use sine wave for demo when no audio
        audioLevel = (Math.sin(elapsedTime * 2) * 0.25 + 0.25);
    }
    
    // Update cloud model
    if (cloudModel) {
        cloudModel.rotation.y = elapsedTime * 0.2;
        cloudModel.scale.x = 1 + audioLevel * 0.2;
        cloudModel.scale.y = 0.9 + audioLevel * 0.2;
        cloudModel.scale.z = 0.8 + audioLevel * 0.2;
    }
    
    // Update wave distortion
    if (waveMesh && waveMesh.material.uniforms) {
        waveMesh.material.uniforms.time.value = elapsedTime;
        waveMesh.material.uniforms.amplitude.value = 0.1 + audioLevel * 0.5;
        waveMesh.material.uniforms.frequency.value = 0.5 + audioLevel * 2;
    }
    
    // Update halftone effect
    if (halftoneEffect && halftoneEffect.material.uniforms) {
        halftoneEffect.material.uniforms.time.value = elapsedTime;
        halftoneEffect.material.uniforms.audioLevel.value = audioLevel;
        
        // Rotate halftone effect
        halftoneEffect.rotation.z = elapsedTime * 0.1;
    }
    
    // Update dripping particles
    for (let i = 0; i < drippingParticles.length; i++) {
        const drip = drippingParticles[i];
        
        // Move drip down
        drip.position.y -= drip.userData.speed * (1 + audioLevel * 2);
        
        // Stretch drip based on speed and audio
        const scale = 1 + (drip.userData.originalY - drip.position.y) * 0.1 * (1 + audioLevel);
        drip.scale.y = scale;
        
        // Reset drip if it's gone too far
        if (drip.position.y < drip.userData.originalY - drip.userData.maxDistance) {
            drip.position.y = drip.userData.originalY;
            drip.scale.y = 1;
            
            // Randomize x and z position
            drip.position.x = (Math.random() - 0.5) * 6;
            drip.position.z = (Math.random() - 0.5) * 6 - 2;
        }
    }
    
    // Update noise shader
    if (noiseShader && noiseShader.uniforms) {
        noiseShader.uniforms.time.value = elapsedTime;
        noiseShader.uniforms.amount.value = 0.03 + audioLevel * 0.1;
    }
}

// Show different effects based on current section
function updateEffectsForSection(sectionId) {
    // Hide all effects first
    if (cloudModel) cloudModel.visible = false;
    if (waveMesh) waveMesh.visible = false;
    if (halftoneEffect) halftoneEffect.visible = false;
    
    // Show appropriate effects based on section
    switch (sectionId) {
        case 'about':
            // Show cloud model in about section
            if (cloudModel) cloudModel.visible = true;
            break;
            
        case 'skills':
            // Show halftone effect in skills section
            if (halftoneEffect) halftoneEffect.visible = true;
            break;
            
        case 'experience':
            // Show wave distortion in experience section
            if (waveMesh) waveMesh.visible = true;
            break;
            
        case 'education':
            // Show cloud model in education section
            if (cloudModel) cloudModel.visible = true;
            break;
            
        case 'projects':
            // Show halftone effect in projects section
            if (halftoneEffect) halftoneEffect.visible = true;
            break;
            
        case 'contact':
            // Show wave distortion in contact section
            if (waveMesh) waveMesh.visible = true;
            break;
            
        default:
            // Default to showing cloud model
            if (cloudModel) cloudModel.visible = true;
    }
}

// Initialize section-specific effects
function initSectionEffects() {
    // Get all sections
    const sections = document.querySelectorAll('.section');
    
    // Create intersection observer
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Get section ID
                const sectionId = entry.target.id;
                
                // Update effects for this section
                updateEffectsForSection(sectionId);
            }
        });
    }, { threshold: 0.5 });
    
    // Observe each section
    sections.forEach(section => {
        observer.observe(section);
    });
}

// Initialize all enhanced effects
document.addEventListener('DOMContentLoaded', () => {
    // Wait for Three.js scene to be initialized in main script
    const checkThreeInit = setInterval(() => {
        if (threeScene && threeRenderer && threeCamera && composer) {
            clearInterval(checkThreeInit);
            
            // Initialize enhanced effects
            initEnhancedThreeEffects();
            
            // Initialize section-specific effects
            initSectionEffects();
            
            // Add enhanced update to animation loop
            const originalAnimate = window.animate;
            window.animate = function() {
                // Call original animate function
                originalAnimate();
                
                // Update enhanced effects
                updateEnhancedThreeEffects();
            };
        }
    }, 100);
});
