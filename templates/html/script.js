// Global variables
let audioContext;
let audioSource;
let analyser;
let audioBuffer;
let isPlaying = false;
let audioFile;
let waveformCanvas, waveformCtx;
let frequencyCanvas, frequencyCtx;
let threeScene, threeCamera, threeRenderer, threeControls;
let pointCloud;
let composer;
let audioData = [];
let isLoaded = false;

// Hidden audio element for Web Audio API connection
let hiddenAudio = null;
let mediaSource = null;
let gainNode = null;

// Initialize our own AudioContext and analyser
function initAudioContext() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 2048;
        analyser.smoothingTimeConstant = 0.8;
        console.log('Created own AudioContext and analyser');
    }
    return audioContext;
}

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', () => {
    // Initialize audio elements
    initAudio();
    
    // Initialize Three.js scene
    initThreeJS();
    
    // Initialize scroll animations
    initScrollAnimations();
    
    // Initialize navigation
    initNavigation();
});

// Audio initialization
function initAudio() {
    // Get canvas elements
    waveformCanvas = document.getElementById('waveform');
    waveformCtx = waveformCanvas.getContext('2d');
    
    frequencyCanvas = document.getElementById('frequency');
    frequencyCtx = frequencyCanvas.getContext('2d');
    
    // Set canvas dimensions
    resizeCanvases();
    window.addEventListener('resize', resizeCanvases);
    
    // Audio file upload
    const audioFileInput = document.getElementById('audio-file');
    audioFileInput.addEventListener('change', handleAudioUpload);
    
    // Audio samples dropdown
    const audioSamplesSelect = document.getElementById('audio-samples-select');
    audioSamplesSelect.addEventListener('change', handleSampleSelection);
    
    // Playback controls
    const playPauseButton = document.getElementById('play-pause');
    playPauseButton.addEventListener('click', togglePlayback);
    
    // Volume control
    const volumeControl = document.getElementById('volume');
    const defaultVolume = 0.5;
    
    volumeControl.addEventListener('input', (e) => {
        const volume = parseFloat(e.target.value);
        if (hiddenAudio) {
            hiddenAudio.volume = volume;
        }
        if (gainNode) {
            gainNode.gain.value = volume;
        }
    });
    
    // Double-click to reset volume to default
    volumeControl.addEventListener('dblclick', (e) => {
        e.target.value = defaultVolume;
        if (hiddenAudio) {
            hiddenAudio.volume = defaultVolume;
        }
        if (gainNode) {
            gainNode.gain.value = defaultVolume;
        }
    });
    
    // Create default audio data for visualization when no audio is loaded
    createDefaultAudioData();
    
    // Start animation loop
    animate();
}

// Resize canvas elements
function resizeCanvases() {
    const container = document.querySelector('.visualization-container');
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    waveformCanvas.width = width;
    waveformCanvas.height = height;
    
    frequencyCanvas.width = width;
    frequencyCanvas.height = height;
}

// Handle audio file upload
function handleAudioUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    console.log('Uploading audio file:', file.name);
    
    // Stop any currently playing audio
    stopCurrentAudio();
    
    const reader = new FileReader();
    reader.onload = (event) => {
        const arrayBuffer = event.target.result;
        
        // Initialize audio context if not already created
        initAudioContext();
        
        // Resume audio context if suspended
        if (audioContext.state === 'suspended') {
            audioContext.resume();
        }
        
        // Decode audio data
        audioContext.decodeAudioData(arrayBuffer, (buffer) => {
            audioBuffer = buffer;
            console.log('Audio decoded successfully, duration:', buffer.duration, 'seconds');
            
            // Create gain node for volume control
            gainNode = audioContext.createGain();
            gainNode.gain.value = document.getElementById('volume').value;
            
            // Update UI
            const playPauseButton = document.getElementById('play-pause');
            playPauseButton.disabled = false;
            
            // Clear dropdown selection
            document.getElementById('audio-samples-select').value = '';
            
            // Auto-play the uploaded audio
            playAudioWebAPI();
        }, (error) => {
            console.error('Error decoding audio data:', error);
        });
    };
    
    reader.readAsArrayBuffer(file);
}

// Handle audio sample selection from dropdown
function handleSampleSelection(e) {
    const url = e.target.value;
    if (!url) return;
    
    console.log('Selected audio URL:', url);
    loadAudioFromURL(url);
}

// Load audio from URL using native Audio element with our AudioContext for visualizations
function loadAudioFromURL(url) {
    console.log('Loading audio from URL:', url);
    
    // Initialize our own AudioContext and analyser
    initAudioContext();
    
    // Resume audio context if suspended (required after user interaction)
    if (audioContext.state === 'suspended') {
        audioContext.resume();
    }
    
    // Stop any currently playing audio
    stopCurrentAudio();
    
    // Create hidden audio element
    hiddenAudio = new Audio();
    hiddenAudio.src = url;
    hiddenAudio.preload = 'auto';
    hiddenAudio.volume = document.getElementById('volume').value;
    
    // Create MediaElementSource to connect to our analyser
    mediaSource = audioContext.createMediaElementSource(hiddenAudio);
    
    // Create gain node for volume control
    gainNode = audioContext.createGain();
    gainNode.gain.value = document.getElementById('volume').value;
    
    // Connect: mediaSource -> analyser -> gain -> destination
    mediaSource.connect(analyser);
    analyser.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    // Event listeners
    hiddenAudio.addEventListener('loadedmetadata', function() {
        console.log('Audio loaded successfully, duration:', hiddenAudio.duration, 'seconds');
        
        // Update UI
        const playPauseButton = document.getElementById('play-pause');
        playPauseButton.disabled = false;
        
        // Clear file input
        document.getElementById('audio-file').value = '';
        
        // Auto-play the audio
        hiddenAudio.play();
        isPlaying = true;
        updatePlayPauseButton();
    });
    
    hiddenAudio.addEventListener('play', function() {
        console.log('=== Audio started playing ===');
        console.log('analyser exists:', !!analyser);
        console.log('audioContext state:', audioContext.state);
        isPlaying = true;
        updatePlayPauseButton();
    });
    
    hiddenAudio.addEventListener('pause', function() {
        if (!hiddenAudio.ended) {
            console.log('Audio paused');
            isPlaying = false;
            updatePlayPauseButton();
        }
    });
    
    hiddenAudio.addEventListener('ended', function() {
        console.log('Audio ended');
        isPlaying = false;
        updatePlayPauseButton();
    });
    
    hiddenAudio.addEventListener('error', function(e) {
        console.error('Error loading audio:', e);
        alert('Error loading audio sample. Please try again.');
        const select = document.getElementById('audio-samples-select');
        if (select) select.value = '';
    });
}

// Stop current audio
function stopCurrentAudio() {
    if (hiddenAudio) {
        hiddenAudio.pause();
        hiddenAudio.src = '';
        hiddenAudio = null;
    }
    
    // Disconnect media source
    if (mediaSource) {
        try { mediaSource.disconnect(); } catch(e) {}
        mediaSource = null;
    }
    
    isPlaying = false;
}

// Play audio using Web Audio API (for uploaded files)
function playAudioWebAPI() {
    if (!audioContext || !audioBuffer) return;
    
    // Resume audio context if suspended
    if (audioContext.state === 'suspended') {
        audioContext.resume();
    }
    
    // Create audio source
    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;
    
    // Create analyser node
    if (!analyser) {
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 2048;
        analyser.smoothingTimeConstant = 0.8;
    }
    
    // Connect: source -> analyser -> gain -> destination
    source.connect(analyser);
    analyser.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    // Store source and gain node
    audioSource = {
        source: source,
        gainNode: gainNode
    };
    
    // Start playback
    source.start(0);
    isPlaying = true;
    updatePlayPauseButton();
    
    // Handle when audio ends
    source.onended = () => {
        isPlaying = false;
        updatePlayPauseButton();
    };
}

// Toggle audio playback
function togglePlayback() {
    if (!hiddenAudio && !audioBuffer) return;
    
    if (hiddenAudio && hiddenAudio.src) {
        if (hiddenAudio.paused) {
            hiddenAudio.play();
        } else {
            hiddenAudio.pause();
        }
    } else if (audioBuffer) {
        // Fallback to Web Audio API for uploaded files
        if (isPlaying) {
            if (audioSource && audioSource.source) {
                audioSource.source.stop();
                isPlaying = false;
            }
        } else {
            playAudioWebAPI();
        }
    }
    
    updatePlayPauseButton();
}

// Update play/pause button icon
function updatePlayPauseButton() {
    const playPauseButton = document.getElementById('play-pause');
    const icon = playPauseButton.querySelector('i');
    
    if (isPlaying) {
        icon.className = 'fas fa-pause';
    } else {
        icon.className = 'fas fa-play';
    }
}

// Create default audio data for visualization when no audio is loaded
function createDefaultAudioData() {
    audioData = [];
    
    // Generate sine wave data
    for (let i = 0; i < 100; i++) {
        audioData.push(Math.sin(i * 0.1) * 0.5 + 0.5);
    }
}

// Animation loop
function animate() {
    requestAnimationFrame(animate);
    
    // Draw audio visualizations
    drawWaveform();
    drawFrequency();
    
    // Update Three.js scene
    updateThreeScene();
    
    // Render Three.js scene
    if (threeRenderer && threeScene && threeCamera) {
        composer.render();
    }
}

// Draw waveform visualization
function drawWaveform() {
    const width = waveformCanvas.width;
    const height = waveformCanvas.height;
    
    // Clear canvas
    waveformCtx.clearRect(0, 0, width, height);
    
    // Set line style
    waveformCtx.lineWidth = 2;
    waveformCtx.strokeStyle = getGradient(waveformCtx, height);
    
    // Begin path
    waveformCtx.beginPath();
    
    if (analyser && isPlaying) {
        // Get time domain data
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        analyser.getByteTimeDomainData(dataArray);
        
        // Debug: check if we have actual audio data
        const avg = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
        console.log('Waveform data - avg:', avg.toFixed(2));
        
        // Calculate step size
        const sliceWidth = width / bufferLength;
        
        // Draw waveform
        for (let i = 0; i < bufferLength; i++) {
            const x = i * sliceWidth;
            const v = dataArray[i] / 128.0;
            const y = v * height / 2;
            
            if (i === 0) {
                waveformCtx.moveTo(x, y);
            } else {
                waveformCtx.lineTo(x, y);
            }
        }
    } else {
        // Draw default waveform
        const sliceWidth = width / audioData.length;
        
        for (let i = 0; i < audioData.length; i++) {
            const x = i * sliceWidth;
            const y = audioData[i] * height;
            
            if (i === 0) {
                waveformCtx.moveTo(x, y);
            } else {
                waveformCtx.lineTo(x, y);
            }
            
            // Update default audio data for animation
            audioData[i] = Math.sin((i * 0.1) + (Date.now() * 0.001)) * 0.25 + 0.5;
        }
    }
    
    // Stroke path
    waveformCtx.stroke();
}

// Update frequency bar colors in drawFrequency function
function drawFrequency() {
    const width = frequencyCanvas.width;
    const height = frequencyCanvas.height;
    
    // Clear canvas
    frequencyCtx.clearRect(0, 0, width, height);
    
    if (analyser && isPlaying) {
        // Get frequency data
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        analyser.getByteFrequencyData(dataArray);
        
        // Calculate bar width
        const barWidth = width / bufferLength * 2.5;
        let barHeight;
        let x = 0;
        
        // Draw frequency bars
        for (let i = 0; i < bufferLength; i++) {
            barHeight = dataArray[i] / 255 * height;
            
            // Use gradient for bar color
            const gradient = frequencyCtx.createLinearGradient(0, height, 0, height - barHeight);
            gradient.addColorStop(0, '#78BEBA'); // LUFS teal
            gradient.addColorStop(1, '#D35233'); // LUFS red
            
            frequencyCtx.fillStyle = gradient;
            frequencyCtx.fillRect(x, height - barHeight, barWidth, barHeight);
            
            x += barWidth + 1;
        }
    } else {
        // Draw default frequency bars
        const barCount = 64;
        const barWidth = width / barCount;
        
        for (let i = 0; i < barCount; i++) {
            // Generate animated bar height
            const barHeight = Math.sin((i * 0.2) + (Date.now() * 0.003)) * 15 + 25;
            
            // Use gradient for bar color
            const gradient = frequencyCtx.createLinearGradient(0, height, 0, height - barHeight);
            gradient.addColorStop(0, '#78BEBA');
            gradient.addColorStop(1, '#D35233');
            
            frequencyCtx.fillStyle = gradient;
            frequencyCtx.fillRect(i * barWidth, height - barHeight, barWidth - 1, barHeight);
        }
    }
}

// Get gradient for waveform
function getGradient(ctx, height) {
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, '#78BEBA'); // Start with teal
    gradient.addColorStop(0.5, '#E7B225'); // Middle with yellow
    gradient.addColorStop(1, '#D35233'); // End with red
    return gradient;
}

// Scroll animations
function initScrollAnimations() {
    const sections = document.querySelectorAll('.section');
    
    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        },
        {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        }
    );
    
    sections.forEach((section) => observer.observe(section));
}

// Navigation
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-links a');
    
    navLinks.forEach((link) => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href');
            const targetSection = document.querySelector(targetId);
            
            if (targetSection) {
                targetSection.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Update active nav link on scroll
    window.addEventListener('scroll', () => {
        let current = '';
        const sections = document.querySelectorAll('section');
        
        sections.forEach((section) => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            
            if (scrollY >= sectionTop - 200) {
                current = section.getAttribute('id');
            }
        });
        
        navLinks.forEach((link) => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    });
}

// Three.js scene initialization
function initThreeJS() {
    // Get the container
    const container = document.getElementById('three-container');
    if (!container) return;
    
    // Scene setup
    threeScene = new THREE.Scene();
    threeScene.background = new THREE.Color(0x111111);
    
    // Camera setup
    threeCamera = new THREE.PerspectiveCamera(
        75,
        container.clientWidth / container.clientHeight,
        0.1,
        1000
    );
    threeCamera.position.z = 30;
    
    // Renderer setup
    threeRenderer = new THREE.WebGLRenderer({ antialias: true });
    threeRenderer.setSize(container.clientWidth, container.clientHeight);
    threeRenderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(threeRenderer.domElement);
    
    // Controls setup
    threeControls = new THREE.OrbitControls(threeCamera, threeRenderer.domElement);
    threeControls.enableDamping = true;
    threeControls.dampingFactor = 0.05;
    threeControls.enableZoom = false;
    
    // Create point cloud
    createPointCloud();
    
    // Setup post-processing
    setupPostProcessing();
    
    // Handle resize
    window.addEventListener('resize', () => {
        threeCamera.aspect = container.clientWidth / container.clientHeight;
        threeCamera.updateProjectionMatrix();
        threeRenderer.setSize(container.clientWidth, container.clientHeight);
    });
}

// Create point cloud
function createPointCloud() {
    const geometry = new THREE.BufferGeometry();
    const count = 2000;
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);
    
    for (let i = 0; i < count; i++) {
        const i3 = i * 3;
        const radius = 10 + Math.random() * 10;
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);
        
        positions[i3] = radius * Math.sin(phi) * Math.cos(theta);
        positions[i3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
        positions[i3 + 2] = radius * Math.cos(phi);
        
        // Color based on position
        colors[i3] = 0.47 + Math.random() * 0.1;
        colors[i3 + 1] = 0.75 + Math.random() * 0.1;
        colors[i3 + 2] = 0.73 + Math.random() * 0.1;
    }
    
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    
    const material = new THREE.PointsMaterial({
        size: 0.1,
        vertexColors: true,
        transparent: true,
        opacity: 0.8
    });
    
    pointCloud = new THREE.Points(geometry, material);
    threeScene.add(pointCloud);
}

// Setup post-processing
function setupPostProcessing() {
    composer = new THREE.EffectComposer(threeRenderer);
    
    const renderPass = new THREE.RenderPass(threeScene, threeCamera);
    composer.addPass(renderPass);
    
    const bloomPass = new THREE.UnrealBloomPass(
        new THREE.Vector2(container.clientWidth, container.clientHeight),
        1.5,
        0.4,
        0.85
    );
    composer.addPass(bloomPass);
}

// Update Three.js scene
function updateThreeScene() {
    if (!threeScene || !pointCloud) return;
    
    // Rotate point cloud
    pointCloud.rotation.y += 0.002;
    pointCloud.rotation.x += 0.001;
    
    // Update point positions based on audio
    const positions = pointCloud.geometry.attributes.position.array;
    const colors = pointCloud.geometry.attributes.color.array;
    
    if (analyser && isPlaying) {
        // Get frequency data
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        analyser.getByteFrequencyData(dataArray);
        
        // Update point positions based on audio data
        for (let i = 0; i < positions.length; i += 3) {
            const index = Math.floor(i / 3) % bufferLength;
            const value = dataArray[index] / 255;
            
            // Original position
            const originalX = positions[i];
            const originalY = positions[i + 1];
            const originalZ = positions[i + 2];
            
            // Calculate distance from center
            const distance = Math.sqrt(
                originalX * originalX +
                originalY * originalY +
                originalZ * originalZ
            );
            
            // Normalize direction vector
            const dirX = originalX / distance;
            const dirY = originalY / distance;
            const dirZ = originalZ / distance;
            
            // Apply audio-reactive displacement
            const displacement = value * 0.5;
            positions[i] = originalX * (1 + displacement * 0.2);
            positions[i + 1] = originalY * (1 + displacement * 0.2);
            positions[i + 2] = originalZ * (1 + displacement * 0.2);
            
            // Update color based on audio
            const color = new THREE.Color();
            color.setHSL(0.5 + value * 0.2, 0.7, 0.5 + value * 0.5);
            
            colors[i] = color.r;
            colors[i + 1] = color.g;
            colors[i + 2] = color.b;
        }
        
        // Update attributes
        pointCloud.geometry.attributes.position.needsUpdate = true;
        pointCloud.geometry.attributes.color.needsUpdate = true;
    } else {
        // Animate point cloud without audio
        const time = Date.now() * 0.001;
        
        for (let i = 0; i < positions.length; i += 3) {
            const index = Math.floor(i / 3);
            const wave = Math.sin(time + index * 0.01) * 0.1;
            
            positions[i] *= (1 + wave * 0.01);
            positions[i + 1] *= (1 + wave * 0.01);
            positions[i + 2] *= (1 + wave * 0.01);
        }
        
        pointCloud.geometry.attributes.position.needsUpdate = true;
    }
    
    // Update controls
    if (threeControls) {
        threeControls.update();
    }
}
