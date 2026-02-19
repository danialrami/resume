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

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', () => {
    initLoading();
    initAudio();
    initThreeJS();
    initScrollAnimations();
    initNavigation();
});

// Loading screen initialization
function initLoading() {
    const loadingScreen = document.querySelector('.loading-screen');
    const container = document.querySelector('.container');
    const loadingProgress = document.querySelector('.loading-progress');
    
    let progress = 0;
    const loadingInterval = setInterval(() => {
        progress += Math.random() * 10;
        if (progress >= 100) {
            progress = 100;
            clearInterval(loadingInterval);
            
            setTimeout(() => {
                loadingScreen.style.opacity = '0';
                container.style.opacity = '1';
                
                setTimeout(() => {
                    loadingScreen.style.display = 'none';
                    isLoaded = true;
                }, 500);
            }, 500);
        }
        loadingProgress.style.width = `${progress}%`;
    }, 200);
}

// Audio initialization
function initAudio() {
    waveformCanvas = document.getElementById('waveform');
    waveformCtx = waveformCanvas.getContext('2d');
    
    frequencyCanvas = document.getElementById('frequency');
    frequencyCtx = frequencyCanvas.getContext('2d');
    
    resizeCanvases();
    window.addEventListener('resize', resizeCanvases);
    
    const audioFileInput = document.getElementById('audio-file');
    audioFileInput.addEventListener('change', handleAudioUpload);
    
    const playPauseButton = document.getElementById('play-pause');
    playPauseButton.addEventListener('click', togglePlayback);
    
    const volumeControl = document.getElementById('volume');
    volumeControl.addEventListener('input', (e) => {
        if (audioContext && audioSource) {
            audioSource.gainNode.gain.value = e.target.value;
        }
    });
    
    createDefaultAudioData();
    animate();
}

// Resize canvas elements
function resizeCanvases() {
    waveformCanvas.width = window.innerWidth * 0.8;
    waveformCanvas.height = 150;
    
    frequencyCanvas.width = window.innerWidth * 0.8;
    frequencyCanvas.height = 150;
}

// Audio file upload
function handleAudioUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    audioFile = URL.createObjectURL(file);
    
    const reader = new FileReader();
    reader.onload = function(e) {
        audioContext.decodeAudioData(e.target.result, (buffer) => {
            audioBuffer = buffer;
        });
    };
    reader.readAsArrayBuffer(file);
}

// Toggle playback
function togglePlayback() {
    if (!audioContext) return;
    
    if (isPlaying) {
        audioSource.stop();
        isPlaying = false;
        document.getElementById('play-pause').innerHTML = '<i class="fas fa-play"></i>';
    } else {
        if (!audioBuffer) {
            // Use default audio data
            createDefaultAudioData();
            playAudio();
        } else {
            playAudio();
        }
    }
}

// Play audio
function playAudio() {
    if (!audioBuffer) return;
    
    if (audioSource) {
        audioSource.stop();
    }
    
    audioSource = audioContext.createBufferSource();
    audioSource.buffer = audioBuffer;
    audioSource.loop = true;
    audioSource.connect(analyser);
    analyser.connect(audioContext.destination);
    audioSource.start(0);
    
    isPlaying = true;
    document.getElementById('play-pause').innerHTML = '<i class="fas fa-pause"></i>';
}

// Create default audio data for visualization
function createDefaultAudioData() {
    if (!audioContext) return;
    
    const bufferSize = audioContext.sampleRate * 2;
    audioBuffer = audioContext.createBuffer(2, bufferSize, audioContext.sampleRate);
    
    for (let channel = 0; channel < 2; channel++) {
        const channelData = audioBuffer.getChannelData(channel);
        for (let i = 0; i < bufferSize; i++) {
            channelData[i] = Math.random() * 0.2;
        }
    }
}

// Animation loop
function animate() {
    requestAnimationFrame(animate);
    
    if (analyser) {
        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        analyser.getByteFrequencyData(dataArray);
        
        drawFrequency(dataArray);
        drawWaveform();
    }
}

// Draw frequency spectrum
function drawFrequency(dataArray) {
    if (!frequencyCtx || !analyser) return;
    
    frequencyCtx.clearRect(0, 0, frequencyCanvas.width, frequencyCanvas.height);
    
    const barWidth = (frequencyCanvas.width / dataArray.length) * 2.5;
    let barHeight;
    let x = 0;
    
    for (let i = 0; i < dataArray.length; i++) {
        barHeight = dataArray[i] / 2;
        
        const gradient = frequencyCtx.createLinearGradient(0, frequencyCanvas.height, 0, 0);
        gradient.addColorStop(0, '#78BEBA');
        gradient.addColorStop(1, '#D35233');
        
        frequencyCtx.fillStyle = gradient;
        
        if (i > 0) {
            x += barWidth + 1;
        }
        
        frequencyCtx.fillRect(x, frequencyCanvas.height - barHeight, barWidth, barHeight);
    }
}

// Draw waveform
function drawWaveform() {
    if (!waveformCtx || !analyser) return;
    
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    analyser.getByteTimeDomainData(dataArray);
    
    waveformCtx.clearRect(0, 0, waveformCanvas.width, waveformCanvas.height);
    
    waveformCtx.lineWidth = 2;
    const gradient = waveformCtx.createLinearGradient(0, 0, waveformCanvas.width, 0);
    gradient.addColorStop(0, '#78BEBA');
    gradient.addColorStop(0.5, '#E7B225');
    gradient.addColorStop(1, '#D35233');
    waveformCtx.strokeStyle = gradient;
    
    waveformCtx.beginPath();
    
    const sliceWidth = waveformCanvas.width * 1.0 / bufferLength;
    let x = 0;
    
    for (let i = 0; i < bufferLength; i++) {
        const barHeight = dataArray[i] / 2;
        
        if (i === 0) {
            waveformCtx.moveTo(x, waveformCanvas.height / 2);
        } else {
            waveformCtx.lineTo(x, waveformCanvas.height / 2 + (barHeight - 128) * 0.7);
        }
        
        x += sliceWidth;
    }
    
    waveformCtx.lineTo(waveformCanvas.width, waveformCanvas.height / 2);
    waveformCtx.stroke();
}

// Three.js initialization
function initThreeJS() {
    const container = document.getElementById('three-container');
    
    threeScene = new THREE.Scene();
    threeScene.fog = new THREE.Fog(0x111111, 10, 50);
    
    threeCamera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    threeCamera.position.z = 25;
    
    threeRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    threeRenderer.setSize(window.innerWidth, window.innerHeight);
    threeRenderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(threeRenderer.domElement);
    
    threeControls = new THREE.OrbitControls(threeCamera, threeRenderer.domElement);
    threeControls.enableDamping = true;
    threeControls.dampingFactor = 0.05;
    
    // Point cloud setup
    createPointCloud();
    
    // Effect composer setup
    composer = new THREE.EffectComposer(threeRenderer);
    composer.addPass(new THREE.RenderPass(threeScene, threeCamera));
    
    const bloomPass = new THREE.UnrealBloomPass(new THREE.Vector2(window.innerWidth, window.innerHeight), 1.5, 0.4, 0.85);
    bloomPass.threshold = 0;
    bloomPass.strength = 1.5;
    bloomPass.radius = 0.5;
    
    composer.addPass(bloomPass);
    
    window.addEventListener('resize', onWindowResize);
}

// Create point cloud
function createPointCloud() {
    const geometry = new THREE.BufferGeometry();
    const vertices = [];
    
    for (let i = 0; i < 5000; i++) {
        const x = (Math.random() - 0.5) * 40;
        const y = (Math.random() - 0.5) * 20;
        const z = (Math.random() - 0.5) * 40;
        
        vertices.push(x, y, z);
    }
    
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    
    const colors = [];
    for (let i = 0; i < vertices.length / 3; i++) {
        const color = new THREE.Color();
        color.setHSL(Math.random() * 0.2, 0.7, 0.5);
        colors.push(color.r, color.g, color.b);
    }
    
    geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    
    const material = new THREE.PointsMaterial({ size: 0.5, vertexColors: true });
    pointCloud = new THREE.Points(geometry, material);
    threeScene.add(pointCloud);
}

// Window resize handler
function onWindowResize() {
    if (!threeCamera || !threeRenderer) return;
    
    threeCamera.aspect = window.innerWidth / window.innerHeight;
    threeCamera.updateProjectionMatrix();
    threeRenderer.setSize(window.innerWidth, window.innerHeight);
    composer.setSize(window.innerWidth, window.innerHeight);
}

// Animation loop for Three.js
function animateThree() {
    requestAnimationFrame(animateThree);
    
    if (pointCloud) {
        pointCloud.rotation.y += 0.002;
        
        if (analyser) {
            const dataArray = new Uint8Array(analyser.frequencyBinCount);
            analyser.getByteFrequencyData(dataArray);
            
            const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
            const scale = 1 + (average / 255) * 0.3;
            
            pointCloud.scale.set(scale, scale, scale);
        }
    }
    
    threeControls.update();
    composer.render();
}

// Start Three.js animation
animateThree();

// Navigation initialization
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-links a');
    const sections = document.querySelectorAll('section');
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            const targetId = link.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);
            
            if (targetSection) {
                window.scrollTo({
                    top: targetSection.offsetTop - 100,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Active link tracking
    const observerOptions = {
        root: null,
        rootMargin: '-50%',
        threshold: 0
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const id = entry.target.getAttribute('id');
                navLinks.forEach(link => {
                    link.classList.remove('active');
                    if (link.getAttribute('href') === `#${id}`) {
                        link.classList.add('active');
                    }
                });
            }
        });
    }, observerOptions);
    
    sections.forEach(section => {
        observer.observe(section);
    });
}

// Scroll animations
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    document.querySelectorAll('.section').forEach(section => {
        section.style.opacity = '0';
        section.style.transform = 'translateY(20px)';
        section.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
        observer.observe(section);
    });
}
