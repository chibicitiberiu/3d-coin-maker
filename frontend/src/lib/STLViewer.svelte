<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import * as THREE from 'three';
	import { RotateCcw, RotateCw, ZoomIn, ZoomOut, Home } from 'lucide-svelte';

	export let stlUrl: string | null = null;

	let container: HTMLDivElement;
	let scene: THREE.Scene;
	let camera: THREE.PerspectiveCamera;
	let renderer: THREE.WebGLRenderer;
	let model: THREE.Mesh | null = null;
	let controls: any;
	let animationId: number;
	let isAutoRotating = false;

	// Initialize Three.js scene
	function initThreeJS() {
		if (!container || !browser) return;

		// Scene
		scene = new THREE.Scene();
		scene.background = new THREE.Color(0xf5f5f5);

		// Camera
		camera = new THREE.PerspectiveCamera(
			75,
			container.clientWidth / container.clientHeight,
			0.1,
			1000
		);
		camera.position.set(50, 50, 50);
		camera.lookAt(0, 0, 0); // Look at the center where model will be positioned

		// Renderer
		renderer = new THREE.WebGLRenderer({ antialias: true });
		renderer.setSize(container.clientWidth, container.clientHeight);
		renderer.setPixelRatio(window.devicePixelRatio);
		renderer.shadowMap.enabled = true;
		renderer.shadowMap.type = THREE.PCFSoftShadowMap;
		// Enhance rendering for better relief visibility
		renderer.toneMappingExposure = 1.2;
		renderer.outputColorSpace = THREE.SRGBColorSpace;
		container.appendChild(renderer.domElement);

		// Lighting
		setupLighting();

		// Grid
		const gridHelper = new THREE.GridHelper(100, 50, 0xcccccc, 0xeeeeee);
		scene.add(gridHelper);

		// Controls (basic mouse controls)
		setupMouseControls();

		// Start render loop
		animate();

		// Handle resize
		window.addEventListener('resize', onWindowResize);
	}

	function setupLighting() {
		// Ambient light - reduced to create more contrast for relief details
		const ambientLight = new THREE.AmbientLight(0x404040, 0.3);
		scene.add(ambientLight);

		// Main directional light from top-right - key light for relief shadows
		const mainLight = new THREE.DirectionalLight(0xffffff, 1.0);
		mainLight.position.set(60, 80, 40);
		mainLight.castShadow = true;
		mainLight.shadow.mapSize.width = 4096;
		mainLight.shadow.mapSize.height = 4096;
		mainLight.shadow.camera.near = 0.1;
		mainLight.shadow.camera.far = 200;
		mainLight.shadow.camera.left = -50;
		mainLight.shadow.camera.right = 50;
		mainLight.shadow.camera.top = 50;
		mainLight.shadow.camera.bottom = -50;
		scene.add(mainLight);

		// Secondary light from opposite side for fill lighting
		const fillLight = new THREE.DirectionalLight(0xffffff, 0.4);
		fillLight.position.set(-40, 30, -30);
		scene.add(fillLight);

		// Rim light from behind to highlight edges
		const rimLight = new THREE.DirectionalLight(0xffffff, 0.6);
		rimLight.position.set(-20, -20, -60);
		scene.add(rimLight);

		// Additional side lights to enhance relief visibility
		const sideLight1 = new THREE.DirectionalLight(0xffeedd, 0.4);
		sideLight1.position.set(80, 10, 0);
		scene.add(sideLight1);

		const sideLight2 = new THREE.DirectionalLight(0xddeeff, 0.4);
		sideLight2.position.set(-80, 10, 0);
		scene.add(sideLight2);

		// Point light from above for additional depth
		const pointLight = new THREE.PointLight(0xffffff, 0.5, 100);
		pointLight.position.set(0, 60, 0);
		pointLight.castShadow = true;
		scene.add(pointLight);
	}

	function setupMouseControls() {
		let isDragging = false;
		let previousMousePosition = { x: 0, y: 0 };

		renderer.domElement.addEventListener('mousedown', (event) => {
			isDragging = true;
			previousMousePosition = { x: event.clientX, y: event.clientY };
		});

		renderer.domElement.addEventListener('mousemove', (event) => {
			if (isDragging && model) {
				const deltaMove = {
					x: event.clientX - previousMousePosition.x,
					y: event.clientY - previousMousePosition.y
				};

				if (event.button === 0) {
					// Left mouse button - rotate
					model.rotation.y += deltaMove.x * 0.01;
					model.rotation.x += deltaMove.y * 0.01;
				}

				previousMousePosition = { x: event.clientX, y: event.clientY };
			}
		});

		renderer.domElement.addEventListener('mouseup', () => {
			isDragging = false;
		});

		renderer.domElement.addEventListener('wheel', (event) => {
			event.preventDefault();
			const scaleFactor = event.deltaY > 0 ? 1.1 : 0.9;
			camera.position.multiplyScalar(scaleFactor);
			camera.lookAt(0, 0, 0); // Maintain center focus
		});
	}

	async function loadSTL(url: string) {
		if (!scene) return;

		try {
			// Remove existing model
			if (model) {
				scene.remove(model);
				model = null;
			}

			// Load STL using fetch and parse manually
			const response = await fetch(url);
			const arrayBuffer = await response.arrayBuffer();
			
			// Simple STL parser for ASCII and binary formats
			const geometry = parseSTL(arrayBuffer);
			
			if (geometry) {
				// Create material with better relief rendering properties
				const material = new THREE.MeshPhongMaterial({
					color: 0xB8860B, // Gold/bronze color for coin
					shininess: 60,
					specular: 0x444444,
					// Enable flat shading to better show relief details
					flatShading: false,
					// Add slight metallic appearance
					reflectivity: 0.3
				});

				// Create mesh
				model = new THREE.Mesh(geometry, material);
				model.castShadow = true;
				model.receiveShadow = true;

				// Center the model
				const box = new THREE.Box3().setFromObject(model);
				const center = box.getCenter(new THREE.Vector3());
				model.position.sub(center);

				// Scale to fit in view
				const size = box.getSize(new THREE.Vector3());
				const maxDim = Math.max(size.x, size.y, size.z);
				const scale = 30 / maxDim;
				model.scale.setScalar(scale);

				scene.add(model);
				
				// Auto-position camera to center on the loaded model
				const scaledMaxDim = maxDim * scale;
				const optimalDistance = scaledMaxDim * 2.5; // Optimal viewing distance
				camera.position.set(optimalDistance, optimalDistance, optimalDistance);
				camera.lookAt(0, 0, 0);
			}
		} catch (error) {
			console.error('Error loading STL:', error);
		}
	}

	function parseSTL(buffer: ArrayBuffer): THREE.BufferGeometry | null {
		const dataView = new DataView(buffer);
		
		// Check if binary STL (first 80 bytes are header, then 4 bytes for triangle count)
		if (buffer.byteLength > 84) {
			const triangleCount = dataView.getUint32(80, true);
			
			// Binary STL: 80 header + 4 count + (50 bytes per triangle * count)
			if (buffer.byteLength === 84 + triangleCount * 50) {
				return parseBinarySTL(dataView, triangleCount);
			}
		}

		// Try ASCII STL
		try {
			const text = new TextDecoder().decode(buffer);
			if (text.toLowerCase().includes('solid')) {
				return parseASCIISTL(text);
			}
		} catch (e) {
			// If decode fails, it's probably binary
		}

		return null;
	}

	function parseBinarySTL(dataView: DataView, triangleCount: number): THREE.BufferGeometry {
		const geometry = new THREE.BufferGeometry();
		const vertices: number[] = [];
		const normals: number[] = [];

		let offset = 84; // Skip header and triangle count

		for (let i = 0; i < triangleCount; i++) {
			// Normal vector (3 floats)
			const nx = dataView.getFloat32(offset, true);
			const ny = dataView.getFloat32(offset + 4, true);
			const nz = dataView.getFloat32(offset + 8, true);
			offset += 12;

			// Three vertices (9 floats total)
			for (let j = 0; j < 3; j++) {
				const x = dataView.getFloat32(offset, true);
				const y = dataView.getFloat32(offset + 4, true);
				const z = dataView.getFloat32(offset + 8, true);
				offset += 12;

				vertices.push(x, y, z);
				normals.push(nx, ny, nz);
			}

			offset += 2; // Skip attribute byte count
		}

		geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
		geometry.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
		
		return geometry;
	}

	function parseASCIISTL(text: string): THREE.BufferGeometry {
		const geometry = new THREE.BufferGeometry();
		const vertices: number[] = [];
		const normals: number[] = [];

		const lines = text.split('\n');
		let currentNormal = [0, 0, 0];

		for (const line of lines) {
			const trimmed = line.trim();
			
			if (trimmed.startsWith('facet normal')) {
				const parts = trimmed.split(/\s+/);
				currentNormal = [parseFloat(parts[2]), parseFloat(parts[3]), parseFloat(parts[4])];
			} else if (trimmed.startsWith('vertex')) {
				const parts = trimmed.split(/\s+/);
				vertices.push(parseFloat(parts[1]), parseFloat(parts[2]), parseFloat(parts[3]));
				normals.push(currentNormal[0], currentNormal[1], currentNormal[2]);
			}
		}

		geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
		geometry.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
		
		return geometry;
	}

	function animate() {
		animationId = requestAnimationFrame(animate);

		if (isAutoRotating && model) {
			model.rotation.y += 0.01;
		}

		renderer.render(scene, camera);
	}

	function onWindowResize() {
		if (!container || !camera || !renderer) return;

		camera.aspect = container.clientWidth / container.clientHeight;
		camera.updateProjectionMatrix();
		renderer.setSize(container.clientWidth, container.clientHeight);
	}

	function resetView() {
		if (!camera || !model) return;
		
		// Calculate optimal camera distance based on model size
		const box = new THREE.Box3().setFromObject(model);
		const size = box.getSize(new THREE.Vector3());
		const maxDim = Math.max(size.x, size.y, size.z);
		const distance = maxDim * 2; // Adjust multiplier as needed
		
		camera.position.set(distance, distance, distance);
		camera.lookAt(0, 0, 0); // Always look at center where model is positioned
		model.rotation.set(0, 0, 0);
	}

	function zoomIn() {
		camera.position.multiplyScalar(0.8);
		camera.lookAt(0, 0, 0); // Maintain center focus
	}

	function zoomOut() {
		camera.position.multiplyScalar(1.25);
		camera.lookAt(0, 0, 0); // Maintain center focus
	}

	function rotateLeft() {
		if (model) model.rotation.y -= 0.1;
	}

	function rotateRight() {
		if (model) model.rotation.y += 0.1;
	}

	function toggleAutoRotate() {
		isAutoRotating = !isAutoRotating;
	}

	// Reactive loading
	$: if (stlUrl && scene) {
		loadSTL(stlUrl);
	}

	onMount(() => {
		if (browser) {
			initThreeJS();
		}
	});

	onDestroy(() => {
		if (browser) {
			if (animationId) {
				cancelAnimationFrame(animationId);
			}
			if (renderer) {
				renderer.dispose();
			}
			window.removeEventListener('resize', onWindowResize);
		}
	});
</script>

<div class="stl-viewer-container">
	<div bind:this={container} class="viewer-canvas"></div>
	
	<div class="viewer-controls">
		<button class="control-btn" on:click={resetView} title="Reset View">
			<Home size={16} />
		</button>
		<button class="control-btn" on:click={zoomIn} title="Zoom In">
			<ZoomIn size={16} />
		</button>
		<button class="control-btn" on:click={zoomOut} title="Zoom Out">
			<ZoomOut size={16} />
		</button>
		<button class="control-btn" on:click={rotateLeft} title="Rotate Left">
			<RotateCcw size={16} />
		</button>
		<button class="control-btn" on:click={rotateRight} title="Rotate Right">
			<RotateCw size={16} />
		</button>
		<button 
			class="control-btn" 
			class:active={isAutoRotating}
			on:click={toggleAutoRotate} 
			title="Auto Rotate"
		>
			Auto
		</button>
	</div>
</div>

<style lang="scss">
	@use '$lib/styles/variables' as *;
	@use '$lib/styles/mixins' as *;

	.stl-viewer-container {
		@include css-containment($gpu-accelerate: true);
		position: relative;
		width: 100%;
		height: 100%;
		min-height: 25rem; // 400px → rem
	}

	.viewer-canvas {
		width: 100%;
		height: 100%;
		border-radius: var(--pico-border-radius);
		overflow: hidden;
	}

	.viewer-controls {
		position: absolute;
		bottom: $spacing-medium;
		right: $spacing-medium;
		@include flex-gap($spacing-small);
		background: $semi-white;
		backdrop-filter: blur($backdrop-blur);
		padding: $spacing-small;
		border-radius: var(--pico-border-radius);
		border: 1px solid var(--pico-muted-border-color);
	}

	.control-btn {
		background: transparent;
		border: 1px solid var(--pico-muted-border-color);
		border-radius: var(--pico-border-radius);
		padding: $spacing-small;
		cursor: pointer;
		transition: all $transition-normal;
		display: flex;
		align-items: center;
		justify-content: center;
		width: $button-size;
		height: $button-size;
		color: var(--pico-muted-color); // Use muted color for better contrast
		
		// Ensure SVG icons inherit color
		:global(svg) {
			color: inherit;
		}
	}

	.control-btn:hover {
		background: var(--pico-primary-100);
		border-color: var(--pico-primary-300);
		color: var(--pico-primary);
	}

	.control-btn.active {
		background: var(--pico-primary);
		color: white;
		border-color: var(--pico-primary);
	}
</style>