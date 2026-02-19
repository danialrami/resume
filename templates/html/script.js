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
    // Initialize loading screen
    initLoading();
    
    // Initialize audio elements
    initAudio();
    
    // Initialize Three.js scene
    initThreeJS();
    
    // Initialize scroll animations
    initScrollAnimations();
    
    // Initialize navigation
    initNavigation();
});

// Loading screen initialization
function initLoading() {
    const loadingScreen = document.querySelector('.loading-screen');
    const container = document.querySelector('.container');
    const loadingProgress = document.querySelector('.loading-progress');
    
    // Simulate loading progress
    let progress = 0;
    const loadingInterval = setInterval(() => {
        progress += Math.random() * 10;
        if (progress >= 100) {
            progress = 100;
            clearInterval(loadingInterval);
            
            // Hide loading screen after a short delay
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
    
    // Playback controls
    const playPauseButton = document.getElementById('play-pause');
    playPauseButton.addEventListener('click', togglePlayback);
    
    // Volume control
    const volumeControl = document.getElementById('volume');
    volumeControl.addEventListener('input', (e) => {
        if (audioContext && audioSource) {
            audioSource.gainNode.gain.value = e.target.value;
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
    
    const reader = new FileReader();
    reader.onload = (event) => {
        const arrayBuffer = event.target.result;
        
        // Initialize audio context if not already created
        if (!audioContext) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        
        // Stop any currently playing audio
        if (audioSource && audioSource.source) {
            audioSource.source.stop();
            isPlaying = false;
            updatePlayPauseButton();
        }
        
        // Decode audio data
        audioContext.decodeAudioData(arrayBuffer, (buffer) => {
            audioBuffer = buffer;
            
            // Update UI
            const playPauseButton = document.getElementById('play-pause');
            playPauseButton.disabled = false;
            
            // Auto-play the uploaded audio
            playAudio();
        }, (error) => {
            console.error('Error decoding audio data:', error);
        });
    };
    
    reader.readAsArrayBuffer(file);
}

// Play audio
function playAudio() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    
    // Create audio source
    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;
    
    // Create gain node for volume control
    const gainNode = audioContext.createGain();
    gainNode.gain.value = document.getElementById('volume').value;
    
    // Create analyser node
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 2048;
    
    // Connect nodes
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
    if (!audioBuffer) return;
    
    if (isPlaying) {
        // Pause audio
        if (audioSource && audioSource.source) {
            audioSource.source.stop();
            isPlaying = false;
        }
    } else {
        // Play audio
        playAudio();
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
            
            // Use gradient for bar color - UPDATED COLORS
            const gradient = frequencyCtx.createLinearGradient(0, height, 0, height - barHeight);
            gradient.addColorStop(0, '#78BEBA'); // Changed from #00E0E0 to LUFS teal
            gradient.addColorStop(1, '#D35233'); // Changed from #FF6600 to LUFS red
            
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
            const time = Date.now() * 0.001;
            const barHeight = Math.sin((i * 0.2) + time) * 0.25 + 0.3;
            const h = barHeight * height;
            
            // Use gradient for bar color - UPDATED COLORS
            const gradient = frequencyCtx.createLinearGradient(0, height, 0, height - h);
            gradient.addColorStop(0, '#78BEBA'); // Changed from #00E0E0 to LUFS teal
            gradient.addColorStop(1, '#D35233'); // Changed from #FF6600 to LUFS red
            
            frequencyCtx.fillStyle = gradient;
            frequencyCtx.fillRect(i * barWidth, height - h, barWidth - 1, h);
        }
    }
}

// Update waveform gradient in getGradient function
function getGradient(ctx, height) {
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, '#D35233'); // Changed from #FF6600 to LUFS red
    gradient.addColorStop(0.5, '#FFFFFF'); // Kept white for middle
    gradient.addColorStop(1, '#78BEBA'); // Changed from #00E0E0 to LUFS teal
    return gradient;
}

// Initialize Three.js scene
function initThreeJS() {
    const container = document.getElementById('three-container');
    
    // Create scene
    threeScene = new THREE.Scene();
    
    // Create camera
    threeCamera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
    threeCamera.position.z = 5;
    
    // Create renderer
    threeRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    threeRenderer.setSize(container.clientWidth, container.clientHeight);
    threeRenderer.setClearColor(0x000000, 0);
    container.appendChild(threeRenderer.domElement);
    
    // Add resize handler
    window.addEventListener('resize', () => {
        threeCamera.aspect = container.clientWidth / container.clientHeight;
        threeCamera.updateProjectionMatrix();
        threeRenderer.setSize(container.clientWidth, container.clientHeight);
        composer.setSize(container.clientWidth, container.clientHeight);
    });
    
    // Add controls
    threeControls = new THREE.OrbitControls(threeCamera, threeRenderer.domElement);
    threeControls.enableDamping = true;
    threeControls.dampingFactor = 0.05;
    threeControls.enableZoom = false;
    
    // Create point cloud
    createPointCloud();
    
    // Add ambient light
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    threeScene.add(ambientLight);
    
    // Add directional light
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(0, 1, 1);
    threeScene.add(directionalLight);
    
    // Set up post-processing
    setupPostProcessing();
}

// Create point cloud
function createPointCloud() {
    // Create geometry
    const geometry = new THREE.BufferGeometry();
    const particles = 5000;
    const positions = new Float32Array(particles * 3);
    const colors = new Float32Array(particles * 3);
    
    // Create cloud shape
    for (let i = 0; i < particles; i++) {
        // Generate point within cloud shape
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);
        const radius = 1 + Math.random() * 0.5;
        
        const x = radius * Math.sin(phi) * Math.cos(theta);
        const y = radius * Math.sin(phi) * Math.sin(theta);
        const z = radius * Math.cos(phi);
        
        positions[i * 3] = x;
        positions[i * 3 + 1] = y;
        positions[i * 3 + 2] = z;
        
        // Set color
        const color = new THREE.Color();
        color.setHSL(Math.random() * 0.2 + 0.5, 0.7, 0.5);
        
        colors[i * 3] = color.r;
        colors[i * 3 + 1] = color.g;
        colors[i * 3 + 2] = color.b;
    }
    
    // Set attributes
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    
    // Create material
    const material = new THREE.PointsMaterial({
        size: 0.05,
        vertexColors: true,
        transparent: true,
        opacity: 0.8,
        blending: THREE.AdditiveBlending
    });
    
    // Create point cloud
    pointCloud = new THREE.Points(geometry, material);
    threeScene.add(pointCloud);
}

// Set up post-processing effects
function setupPostProcessing() {
    const container = document.getElementById('three-container');
    
    // Create render pass
    const renderPass = new THREE.RenderPass(threeScene, threeCamera);
    
    // Create bloom pass
    const bloomPass = new THREE.UnrealBloomPass(
        new THREE.Vector2(container.clientWidth, container.clientHeight),
        1.5,  // strength
        0.4,  // radius
        0.85  // threshold
    );
    
    // Create effect composer
    composer = new THREE.EffectComposer(threeRenderer);
    composer.addPass(renderPass);
    composer.addPass(bloomPass);
}

// Update Three.js scene
function updateThreeScene() {
    if (!pointCloud) return;
    
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
            const ix = i / 3;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos(2 * Math.random() - 1);
            
            // Calculate pulsing effect
            const pulse = Math.sin(time + ix * 0.1) * 0.1 + 1;
            
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
            
            // Apply pulsing effect
            positions[i] = dirX * distance * pulse;
            positions[i + 1] = dirY * distance * pulse;
            positions[i + 2] = dirZ * distance * pulse;
        }
        
        // Update position attribute
        pointCloud.geometry.attributes.position.needsUpdate = true;
    }
    
    // Update controls
    threeControls.update();
}

// Initialize scroll animations
function initScrollAnimations() {
    const sections = document.querySelectorAll('.section');
    
    // Intersection Observer for section animations
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, { threshold: 0.1 });
    
    // Observe each section
    sections.forEach(section => {
        observer.observe(section);
    });
}

// Initialize navigation
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-links a');
    
    // Add click event listeners to navigation links
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Get target section
            const targetId = link.getAttribute('href');
            const targetSection = document.querySelector(targetId);
            
            // Scroll to target section
            if (targetSection) {
                targetSection.scrollIntoView({ behavior: 'smooth' });
            }
            
            // Update active link
            navLinks.forEach(navLink => {
                navLink.classList.remove('active');
            });
            link.classList.add('active');
        });
    });
    
    // Update active link on scroll
    window.addEventListener('scroll', () => {
        let currentSection = '';
        
        document.querySelectorAll('.section').forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            
            if (window.pageYOffset >= sectionTop - 200) {
                currentSection = '#' + section.getAttribute('id');
            }
        });
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === currentSection) {
                link.classList.add('active');
            }
        });
    });
}

// Add interactive effects to skill items
document.addEventListener('DOMContentLoaded', () => {
    const skillItems = document.querySelectorAll('.skill-item');
    
    skillItems.forEach(item => {
        item.addEventListener('mouseenter', () => {
            // Add hover effect
            item.style.transform = 'translateY(-10px)';
            item.style.boxShadow = '0 15px 30px rgba(0, 224, 224, 0.3)';
            
            // Play sound effect if audio context exists
            if (audioContext) {
                playSkillSound(item.getAttribute('data-sound'));
            }
        });
        
        item.addEventListener('mouseleave', () => {
            // Remove hover effect
            item.style.transform = '';
            item.style.boxShadow = '';
        });
    });
});

// Play sound effect for skill items
// function playSkillSound(soundType) {
//     if (!audioContext) {
//         audioContext = new (window.AudioContext || window.webkitAudioContext)();
//     }
//     
//     // Create oscillator
//     const oscillator = audioContext.createOscillator();
//     const gainNode = audioContext.createGain();
//     
//     // Set oscillator type and frequency based on sound type
//     switch (soundType) {
//         case 'wwise':
//             oscillator.type = 'sine';
//             oscillator.frequency.setValueAtTime(440, audioContext.currentTime);
//             break;
//         case 'daw':
//             oscillator.type = 'triangle';
//             oscillator.frequency.setValueAtTime(330, audioContext.currentTime);
//             break;
//         case 'maxmsp':
//             oscillator.type = 'square';
//             oscillator.frequency.setValueAtTime(523, audioContext.currentTime);
//             break;
//         case 'modular':
//             oscillator.type = 'sawtooth';
//             oscillator.frequency.setValueAtTime(277, audioContext.currentTime);
//             break;
//         case 'gameengine':
//             oscillator.type = 'sine';
//             oscillator.frequency.setValueAtTime(587, audioContext.currentTime);
//             break;
//         case 'python':
//             oscillator.type = 'triangle';
//             oscillator.frequency.setValueAtTime(392, audioContext.currentTime);
//             break;
//         case 'node':
//             oscillator.type = 'square';
//             oscillator.frequency.setValueAtTime(349, audioContext.currentTime);
//             break;
//         case 'tools':
//             oscillator.type = 'sawtooth';
//             oscillator.frequency.setValueAtTime(466, audioContext.currentTime);
//             break;
//         default:
//             oscillator.type = 'sine';
//             oscillator.frequency.setValueAtTime(440, audioContext.currentTime);
//     }
//     
//     // Set gain (volume)
//     gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
//     gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
//     
//     // Connect nodes
//     oscillator.connect(gainNode);
//     gainNode.connect(audioContext.destination);
//     
//     // Start and stop oscillator
//     oscillator.start();
//     oscillator.stop(audioContext.currentTime + 0.5);
// }

document.addEventListener('DOMContentLoaded', function() {
    // Update copyright year in footer
    const yearSpan = document.getElementById('current-year');
    if (yearSpan) {
      yearSpan.textContent = new Date().getFullYear();
    }
  });

  // Function to scroll the navigation to show the active section
function scrollNavToActiveItem() {
    // Get the active nav link
    const activeLink = document.querySelector('.nav-links a.active');
    
    if (activeLink) {
      // Get the nav links container
      const navLinksContainer = document.querySelector('.nav-links');
      
      // Get the position of the active link relative to the container
      const activeLinkPosition = activeLink.parentElement.offsetLeft;
      
      // Calculate the center position to scroll to
      // This will center the active item in the viewport
      const scrollPosition = activeLinkPosition - (navLinksContainer.offsetWidth / 2) + (activeLink.offsetWidth / 2);
      
      // Scroll smoothly to the position
      navLinksContainer.scrollTo({
        left: Math.max(0, scrollPosition),
        behavior: 'smooth'
      });
    }
  }
  
  // Call this function whenever a section becomes active
  document.addEventListener('DOMContentLoaded', function() {
    // Initial scroll to active item on page load
    scrollNavToActiveItem();
    
    // Create an observer for section visibility
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          // Get the id of the visible section
          const sectionId = entry.target.id;
          
          // Update active class on nav links
          document.querySelectorAll('.nav-links a').forEach(link => {
            if (link.getAttribute('href') === '#' + sectionId) {
              link.classList.add('active');
            } else {
              link.classList.remove('active');
            }
          });
          
          // Scroll nav to show the active item
          scrollNavToActiveItem();
        }
      });
    }, { threshold: 0.5 }); // Section is considered active when 50% visible
    
    // Observe all sections
    document.querySelectorAll('.section').forEach(section => {
      observer.observe(section);
    });
    
    // Add click event listeners to nav links
    document.querySelectorAll('.nav-links a').forEach(link => {
      link.addEventListener('click', function(e) {
        // Smooth scroll already handled by CSS (scroll-behavior: smooth)
        
        // Update active class
        document.querySelectorAll('.nav-links a').forEach(navLink => {
          navLink.classList.remove('active');
        });
        this.classList.add('active');
        
        // Scroll nav to show the active item
        setTimeout(scrollNavToActiveItem, 100);
      });
    });
  });