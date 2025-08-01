<script lang="ts">
	import { browser } from '$app/environment';
	import { onDestroy, afterUpdate } from 'svelte';

	// Props - all the data the canvas needs to render
	export let processedImageData: ImageData | null = null;
	export let coinSize = 30; // diameter in mm
	export let coinThickness = 3; // in mm
	export let coinShape: 'circle' | 'square' | 'hexagon' | 'octagon' = 'circle';
	export let heightmapScale = 100; // percentage
	export let offsetX = 0; // percentage of coin size
	export let offsetY = 0; // percentage of coin size
	export let rotation = 0; // degrees
	export let pixelsPerMM = 4; // pixels per millimeter - controls zoom level
	export let activeTab: string = 'processed';

	// Canvas view state for pan/zoom
	let viewX = 0; // Pan offset X
	let viewY = 0; // Pan offset Y  
	let viewZoom = 1; // Zoom level
	let isDragging = false;
	let lastMouseX = 0;
	let lastMouseY = 0;

	let preparedCanvas: HTMLCanvasElement;
	let resizeObserver: ResizeObserver | null = null;
	let isCanvasInitialized = false;
	let lastProcessedImageData: ImageData | null = null;
	let lastCanvasWidth = 0;
	let lastCanvasHeight = 0;

	// UI constants - use design system
	const PRIMARY_COLOR = '#0172ad'; // TODO: Get from CSS custom property
	
	// Convert hex color to RGB values for transparency
	function hexToRgb(hex: string): {r: number, g: number, b: number} {
		const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
		return result ? {
			r: parseInt(result[1], 16),
			g: parseInt(result[2], 16),
			b: parseInt(result[3], 16)
		} : {r: 0, g: 0, b: 0};
	}
	
	const primaryRgb = hexToRgb(PRIMARY_COLOR);

	// Draw everything on the prepared canvas
	function drawPreparedCanvas() {
		if (!preparedCanvas) return;
		
		const ctx = preparedCanvas.getContext('2d');
		if (!ctx) return;
		
		// Check if canvas is actually visible and has dimensions
		const rect = preparedCanvas.getBoundingClientRect();
		if (!rect || rect.width === 0 || rect.height === 0) return;
		
		const canvasWidth = rect.width;
		const canvasHeight = rect.height;
		
		// Clear canvas
		ctx.clearRect(0, 0, canvasWidth, canvasHeight);
		
		// Fill with background color
		ctx.fillStyle = '#f8f9fa';
		ctx.fillRect(0, 0, canvasWidth, canvasHeight);
		
		// Apply transform for pan/zoom
		ctx.save();
		ctx.scale(viewZoom, viewZoom);
		ctx.translate(viewX, viewY);
		
		// Calculate world coordinates for center (0,0 in world space)
		const worldCenterX = canvasWidth / (2 * viewZoom) - viewX;
		const worldCenterY = canvasHeight / (2 * viewZoom) - viewY;
		
		// Draw infinite grid
		drawInfiniteGrid(ctx, canvasWidth, canvasHeight, worldCenterX, worldCenterY);
		
		// Draw processed image (if exists)
		if (processedImageData) {
			drawProcessedImage(ctx, worldCenterX, worldCenterY);
		}
		
		// Draw coin overlay
		drawCoinOverlay(ctx, worldCenterX, worldCenterY);
		
		ctx.restore();
		
		// Draw rulers on top (unscaled, always at canvas edges)
		drawDynamicRulers(ctx, canvasWidth, canvasHeight);
	}
	
	function drawInfiniteGrid(ctx: CanvasRenderingContext2D, canvasWidth: number, canvasHeight: number, worldCenterX: number, worldCenterY: number) {
		const gridSize = 10 * pixelsPerMM; // 10mm grid
		
		ctx.strokeStyle = 'rgba(0, 0, 0, 0.1)';
		ctx.lineWidth = 1 / viewZoom; // Keep line width constant regardless of zoom
		ctx.beginPath();
		
		// Calculate visible world bounds
		const worldLeft = -viewX;
		const worldRight = canvasWidth / viewZoom - viewX;
		const worldTop = -viewY;
		const worldBottom = canvasHeight / viewZoom - viewY;
		
		// Draw vertical lines
		const startCol = Math.floor(worldLeft / gridSize);
		const endCol = Math.ceil(worldRight / gridSize);
		
		for (let col = startCol; col <= endCol; col++) {
			const x = col * gridSize;
			ctx.moveTo(x, worldTop);
			ctx.lineTo(x, worldBottom);
		}
		
		// Draw horizontal lines
		const startRow = Math.floor(worldTop / gridSize);
		const endRow = Math.ceil(worldBottom / gridSize);
		
		for (let row = startRow; row <= endRow; row++) {
			const y = row * gridSize;
			ctx.moveTo(worldLeft, y);
			ctx.lineTo(worldRight, y);
		}
		
		ctx.stroke();
		
		// Draw center axes in dark gray
		ctx.strokeStyle = 'rgba(64, 64, 64, 0.7)';
		ctx.lineWidth = 2 / viewZoom;
		ctx.beginPath();
		// X-axis
		ctx.moveTo(worldLeft, 0);
		ctx.lineTo(worldRight, 0);
		// Y-axis  
		ctx.moveTo(0, worldTop);
		ctx.lineTo(0, worldBottom);
		ctx.stroke();
	}
	
	function drawDynamicRulers(ctx: CanvasRenderingContext2D, canvasWidth: number, canvasHeight: number) {
		const tickSize = 8;
		const smallTickSize = 4;
		
		// Calculate world position at screen edges
		const worldLeft = -viewX;
		const worldRight = canvasWidth / viewZoom - viewX;
		const worldTop = -viewY;  
		const worldBottom = canvasHeight / viewZoom - viewY;
		
		// Determine appropriate tick spacing based on zoom level
		// Target: 40-80 pixels between major ticks for good readability
		const targetPixelSpacing = 60;
		const currentPixelSpacing = 10 * pixelsPerMM * viewZoom; // Current 10mm spacing in pixels
		
		// Find the best tick spacing using log10 values: 1, 2, 5, 10, 20, 50, 100, etc.
		const baseSpacings = [1, 2, 5]; // Base values to multiply by powers of 10
		let bestSpacing = 10; // Default 10mm
		let bestPixelSpacing = currentPixelSpacing;
		
		// Try different powers of 10
		for (let power = -1; power <= 3; power++) {
			for (const base of baseSpacings) {
				const spacing = base * Math.pow(10, power);
				const pixelSpacing = spacing * pixelsPerMM * viewZoom;
				
				// Check if this spacing is better (closer to target)
				if (Math.abs(pixelSpacing - targetPixelSpacing) < Math.abs(bestPixelSpacing - targetPixelSpacing)) {
					bestSpacing = spacing;
					bestPixelSpacing = pixelSpacing;
				}
			}
		}
		
		const tickSpacing = bestSpacing * pixelsPerMM; // World units
		
		ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
		ctx.strokeStyle = 'rgba(0, 0, 0, 0.8)';
		ctx.font = '10px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
		ctx.lineWidth = 1;
		
		// Draw horizontal ruler (top edge)
		ctx.textAlign = 'center';
		ctx.textBaseline = 'top';
		ctx.beginPath();
		
		const startColH = Math.floor(worldLeft / tickSpacing);
		const endColH = Math.ceil(worldRight / tickSpacing);
		
		for (let col = startColH; col <= endColH; col++) {
			const worldX = col * tickSpacing;
			const screenX = (worldX + viewX) * viewZoom;
			
			if (screenX >= 0 && screenX <= canvasWidth) {
				const mm = col * bestSpacing;
				
				// Major tick and label
				ctx.moveTo(screenX, 0);
				ctx.lineTo(screenX, tickSize);
				
				// Show label - including "0mm" for origin
				if (mm === 0) {
					ctx.fillText('0mm', screenX, tickSize + 2);
				} else {
					ctx.fillText(`${mm}`, screenX, tickSize + 2);
				}
			}
		}
		
		// Draw vertical ruler (left edge)
		ctx.textAlign = 'left';
		ctx.textBaseline = 'middle';
		
		const startRowV = Math.floor(worldTop / tickSpacing);
		const endRowV = Math.ceil(worldBottom / tickSpacing);
		
		for (let row = startRowV; row <= endRowV; row++) {
			const worldY = row * tickSpacing;
			const screenY = (worldY + viewY) * viewZoom;
			
			if (screenY >= 0 && screenY <= canvasHeight) {
				const mm = -row * bestSpacing; // Negative because Y increases downward
				
				// Major tick and label
				ctx.moveTo(0, screenY);
				ctx.lineTo(tickSize, screenY);
				
				// Show label - including "0mm" for origin
				if (mm === 0) {
					ctx.fillText('0mm', tickSize + 2, screenY);
				} else {
					ctx.fillText(`${mm}`, tickSize + 2, screenY);
				}
			}
		}
		
		ctx.stroke();
	}
	
	function drawProcessedImage(ctx: CanvasRenderingContext2D, worldCenterX: number, worldCenterY: number) {
		if (!processedImageData) return;
		
		// Create temporary canvas for the processed image
		const tempCanvas = document.createElement('canvas');
		tempCanvas.width = processedImageData.width;
		tempCanvas.height = processedImageData.height;
		const tempCtx = tempCanvas.getContext('2d');
		if (!tempCtx) return;
		
		// Put processed image data on temporary canvas
		tempCtx.putImageData(processedImageData, 0, 0);
		
		// Apply same scaling logic as backend:
		// 1. Scale image so width = coin size (base scale)
		const imageWidth = processedImageData.width;
		const imageHeight = processedImageData.height;
		const baseScaleFactor = coinSize / imageWidth;
		
		// 2. Apply user scale percentage
		const finalScaleFactor = baseScaleFactor * (heightmapScale / 100);
		
		// 3. Calculate final image dimensions in world coordinates
		const finalImageWidth = imageWidth * finalScaleFactor * pixelsPerMM;
		const finalImageHeight = imageHeight * finalScaleFactor * pixelsPerMM;
		
		// Save context for transformations
		ctx.save();
		
		// 4. Apply offset (as percentage of coin size)
		const offsetXPixels = (offsetX / 100) * coinSize * pixelsPerMM;
		const offsetYPixels = (offsetY / 100) * coinSize * pixelsPerMM;
		ctx.translate(offsetXPixels, offsetYPixels);
		
		// 5. Apply rotation
		ctx.rotate((rotation * Math.PI) / 180);
		
		// 6. Draw the processed image with correct dimensions, centered at origin
		ctx.drawImage(tempCanvas, -finalImageWidth / 2, -finalImageHeight / 2, finalImageWidth, finalImageHeight);
		
		// Restore context
		ctx.restore();
	}
	
	function drawCoinOverlay(ctx: CanvasRenderingContext2D, worldCenterX: number, worldCenterY: number) {
		const coinRadius = (coinSize * pixelsPerMM) / 2;
		
		// Calculate visible world bounds for overlay
		const worldLeft = -viewX;
		const worldRight = (preparedCanvas?.getBoundingClientRect().width || 600) / viewZoom - viewX;
		const worldTop = -viewY;
		const worldBottom = (preparedCanvas?.getBoundingClientRect().height || 400) / viewZoom - viewY;
		
		// Create clipping path for coin shape
		ctx.save();
		ctx.beginPath();
		
		if (coinShape === 'circle') {
			ctx.arc(0, 0, coinRadius, 0, 2 * Math.PI);
		} else if (coinShape === 'square') {
			const size = coinSize * pixelsPerMM;
			ctx.rect(-size/2, -size/2, size, size);
		} else if (coinShape === 'hexagon') {
			for (let i = 0; i < 6; i++) {
				const angle = (i * Math.PI) / 3;
				const x = coinRadius * Math.cos(angle);
				const y = coinRadius * Math.sin(angle);
				if (i === 0) {
					ctx.moveTo(x, y);
				} else {
					ctx.lineTo(x, y);
				}
			}
			ctx.closePath();
		} else if (coinShape === 'octagon') {
			for (let i = 0; i < 8; i++) {
				const angle = (i * Math.PI) / 4;
				const x = coinRadius * Math.cos(angle);
				const y = coinRadius * Math.sin(angle);
				if (i === 0) {
					ctx.moveTo(x, y);
				} else {
					ctx.lineTo(x, y);
				}
			}
			ctx.closePath();
		}
		
		// Create inverted clipping path (everything OUTSIDE the coin shape)
		// Draw large rectangle covering entire visible area, with coin shape as a hole
		ctx.rect(worldLeft, worldTop, worldRight - worldLeft, worldBottom - worldTop);
		ctx.fillStyle = `rgba(${primaryRgb.r}, ${primaryRgb.g}, ${primaryRgb.b}, 0.3)`; // 30% transparent primary color overlay
		ctx.fill('evenodd'); // Use even-odd rule to create hole
		
		ctx.restore();
		
		// Draw coin shape outline with primary color
		ctx.strokeStyle = PRIMARY_COLOR;
		ctx.lineWidth = 3 / viewZoom; // Keep line width constant regardless of zoom
		ctx.setLineDash([]);
		ctx.beginPath();
		
		if (coinShape === 'circle') {
			ctx.arc(0, 0, coinRadius, 0, 2 * Math.PI);
		} else if (coinShape === 'square') {
			const size = coinSize * pixelsPerMM;
			ctx.rect(-size/2, -size/2, size, size);
		} else if (coinShape === 'hexagon') {
			for (let i = 0; i < 6; i++) {
				const angle = (i * Math.PI) / 3;
				const x = coinRadius * Math.cos(angle);
				const y = coinRadius * Math.sin(angle);
				if (i === 0) {
					ctx.moveTo(x, y);
				} else {
					ctx.lineTo(x, y);
				}
			}
			ctx.closePath();
		} else if (coinShape === 'octagon') {
			for (let i = 0; i < 8; i++) {
				const angle = (i * Math.PI) / 4;
				const x = coinRadius * Math.cos(angle);
				const y = coinRadius * Math.sin(angle);
				if (i === 0) {
					ctx.moveTo(x, y);
				} else {
					ctx.lineTo(x, y);
				}
			}
			ctx.closePath();
		}
		
		ctx.stroke();
	}

	// Canvas mouse interaction handlers
	function handleCanvasMouseDown(event: MouseEvent) {
		if (event.button === 0) { // Left click
			isDragging = true;
			lastMouseX = event.offsetX;
			lastMouseY = event.offsetY;
			preparedCanvas.style.cursor = 'grabbing';
		}
	}
	
	function handleCanvasMouseMove(event: MouseEvent) {
		if (isDragging) {
			const deltaX = event.offsetX - lastMouseX;
			const deltaY = event.offsetY - lastMouseY;
			
			// Update view position (pan)
			viewX += deltaX / viewZoom;
			viewY += deltaY / viewZoom;
			
			lastMouseX = event.offsetX;
			lastMouseY = event.offsetY;
			
			// Redraw canvas - this will also trigger reactive updates for status bar
			drawPreparedCanvas();
		} else {
			preparedCanvas.style.cursor = 'grab';
		}
	}
	
	function handleCanvasMouseUp(event: MouseEvent) {
		if (event.button === 0) { // Left click
			isDragging = false;
			preparedCanvas.style.cursor = 'grab';
		}
	}
	
	function handleCanvasWheel(event: WheelEvent) {
		event.preventDefault();
		
		const zoomFactor = 1.1;
		const rect = preparedCanvas.getBoundingClientRect();
		if (!rect) return;
		
		const mouseX = event.clientX - rect.left;
		const mouseY = event.clientY - rect.top;
		
		// Calculate world position under mouse before zoom
		const worldMouseX = mouseX / viewZoom - viewX;
		const worldMouseY = mouseY / viewZoom - viewY;
		
		// Update zoom
		if (event.deltaY > 0) {
			viewZoom = Math.max(0.1, viewZoom / zoomFactor); // Zoom out (min 0.1x)
		} else {
			viewZoom = Math.min(10, viewZoom * zoomFactor); // Zoom in (max 10x)
		}
		
		// Adjust view position to keep mouse position fixed
		viewX = mouseX / viewZoom - worldMouseX;
		viewY = mouseY / viewZoom - worldMouseY;
		
		// Redraw canvas
		drawPreparedCanvas();
	}
	
	// Reset view to center world origin (0,0) in canvas and default zoom
	export function resetCanvasView() {
		if (!preparedCanvas) return;
		
		const rect = preparedCanvas.getBoundingClientRect();
		if (!rect || rect.width === 0 || rect.height === 0) return;
		
		const canvasWidth = rect.width;
		const canvasHeight = rect.height;
		
		// Center world origin (0,0) by setting view position to half canvas size
		viewX = canvasWidth / 2;
		viewY = canvasHeight / 2;
		viewZoom = 1;
		drawPreparedCanvas();
	}

	// Expose view state for status bar
	export function getViewState() {
		return { viewX, viewY, viewZoom };
	}

	// Canvas should only redraw when:
	// 1. processedImageData changes (handled below)
	// 2. Canvas interactions (handled in event handlers)
	// 3. Tab switches to 'processed' (handled below)
	// NOT when parameters change - that should only trigger processing, not canvas redraw
	
	// Handle canvas resize to maintain full resolution
	$: if (preparedCanvas && browser && activeTab === 'processed') {
		// Clean up previous observer
		if (resizeObserver) {
			resizeObserver.disconnect();
		}
		
		resizeObserver = new ResizeObserver(() => {
			// Check if canvas exists and is visible before accessing
			if (!preparedCanvas) return;
			
			const rect = preparedCanvas.getBoundingClientRect();
			if (!rect || rect.width === 0 || rect.height === 0) return;
			
			// Prevent infinite resize loops by checking if size actually changed
			const newWidth = Math.round(rect.width);
			const newHeight = Math.round(rect.height);
			
			if (newWidth === lastCanvasWidth && newHeight === lastCanvasHeight) {
				return; // Canvas size unchanged, skip resize
			}
			lastCanvasWidth = newWidth;
			lastCanvasHeight = newHeight;
			
			const dpr = window.devicePixelRatio || 1;
			
			// Set internal resolution to match display size * device pixel ratio
			preparedCanvas.width = newWidth * dpr;
			preparedCanvas.height = newHeight * dpr;
			
			// Scale context to account for device pixel ratio
			const ctx = preparedCanvas.getContext('2d');
			if (ctx) {
				ctx.scale(dpr, dpr);
			}
			
			// Initialize view to center on first run
			if (!isCanvasInitialized) {
				viewX = newWidth / 2;
				viewY = newHeight / 2;
				viewZoom = 1;
				isCanvasInitialized = true;
			}
			
			// Redraw canvas
			drawPreparedCanvas();
		});
		
		resizeObserver.observe(preparedCanvas);
	} else if (resizeObserver && activeTab !== 'processed') {
		// Disconnect observer when not on processed tab
		resizeObserver.disconnect();
		resizeObserver = null;
	}
	
	// Cleanup on component destroy
	onDestroy(() => {
		if (resizeObserver) {
			resizeObserver.disconnect();
		}
	});

	// Use afterUpdate to check for processedImageData changes without reactive loops
	afterUpdate(() => {
		if (processedImageData !== lastProcessedImageData && preparedCanvas && browser && activeTab === 'processed') {
			lastProcessedImageData = processedImageData;
			drawPreparedCanvas();
		}
	});

	// Reactive statement to redraw canvas when display parameters change
	$: if (preparedCanvas && browser && activeTab === 'processed' && (
		coinShape || coinSize || heightmapScale || offsetX || offsetY || rotation || pixelsPerMM
	)) {
		// Redraw when any display parameter changes
		drawPreparedCanvas();
	}
</script>

<div class="prepared-canvas-container">
	<!-- Canvas with integrated rulers -->
	<canvas 
		bind:this={preparedCanvas}
		class="prepared-canvas"
		on:mousedown={handleCanvasMouseDown}
		on:mousemove={handleCanvasMouseMove}  
		on:mouseup={handleCanvasMouseUp}
		on:wheel={handleCanvasWheel}
		on:contextmenu={(e) => e.preventDefault()}
	></canvas>
</div>

<style lang="scss">
	@use '$lib/styles/variables' as *;
	@use '$lib/styles/mixins' as *;
	
	// Canvas color custom properties - for JavaScript access
	:root {
		--canvas-background: #{$light-gray-bg};
		--canvas-grid-line: #{$grid-line};
		--canvas-axis-line: #{$axis-line};
		--canvas-primary: #{$primary-blue};
	}

	.prepared-canvas-container {
		@include css-containment($gpu-accelerate: true);
		position: relative;
		width: 100%;
		flex: 1;
		@include flex-center;
		overflow: hidden;
	}
	
	.prepared-canvas {
		width: 100%;
		height: 100%;
		cursor: grab;
		display: block;
		position: relative;
		border: $border-thin solid var(--pico-muted-border-color);
		border-radius: var(--pico-border-radius);
		background: $light-gray-bg;
		z-index: 1;
		margin-left: $margin-canvas; // Use design system variable
		margin-top: $margin-canvas; // Use design system variable
		
		&:focus-visible {
			@include focus-outline;
		}
	}
	
	.prepared-canvas:active {
		cursor: grabbing;
	}
</style>