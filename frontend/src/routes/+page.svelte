<script lang="ts">
	import { Upload, Settings, Eye, Download, Loader2, Image, AlertTriangle } from 'lucide-svelte';
	import { processImage, imageDataToBlob, type ImageProcessingParams } from '$lib/imageProcessor';
	import { browser } from '$app/environment';
	import { onDestroy } from 'svelte';
	import STLViewer from '$lib/STLViewer.svelte';
	import { api, type CoinParameters } from '$lib/api';
	
	let activeTab: 'original' | 'processed' | 'result' = 'processed';
	let uploadedFile: File | null = null;
	let uploadedImageUrl: string | null = null;
	let processedImageUrl: string | null = null;
	let generatedSTLUrl: string | null = null;
	let isUploading = false;
	let isProcessing = false;
	let isGenerating = false;
	let fileInput: HTMLInputElement;
	let originalImageElement: HTMLImageElement;
	let preparedCanvas: HTMLCanvasElement;
	
	// Canvas view state for pan/zoom
	let viewX = 0; // Pan offset X
	let viewY = 0; // Pan offset Y  
	let viewZoom = 1; // Zoom level
	let isDragging = false;
	let lastMouseX = 0;
	let lastMouseY = 0;
	
	// API-related state
	let generationId: string | null = null;
	let currentTaskId: string | null = null;
	let processingTaskId: string | null = null;
	let generationTaskId: string | null = null;
	
	// Error state management
	let stlGenerationError: string | null = null;

	// Client-side processing state
	let processedImageData: ImageData | null = null;
	let processedImageBlob: Blob | null = null;
	
	// Image processing parameters
	let grayscaleMethod: 'average' | 'luminance' | 'red' | 'green' | 'blue' | 'custom' = 'luminance';
	let brightness = 0;
	let contrast = 0;
	let gamma = 1.0;
	let invertColors = false;
	
	// UI constants
	const PRIMARY_COLOR = '#0172ad';
	
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
	
	// Dynamic offset range based on image scale
	// To move image completely outside coin: need coin_radius + image_radius
	// coin_radius = 50%, image_radius = (heightmapScale / 2)%
	$: offsetRange = Math.ceil(50 + (heightmapScale / 2));
	
	// Note: Offset values are not clamped - text input allows any value
	// Sliders are limited to practical range but text input allows precision values
	
	// Coin parameters
	let coinShape: 'circle' | 'square' | 'hexagon' | 'octagon' = 'circle';
	let coinSize = 30; // diameter in mm
	let coinThickness = 3; // in mm
	let reliefDepth = 1; // in mm
	
	// Heightmap positioning
	let heightmapScale = 100; // percentage
	let offsetX = 0; // percentage of coin size
	let offsetY = 0; // percentage of coin size
	let rotation = 0; // degrees
	
	// View scaling
	let pixelsPerMM = 4; // pixels per millimeter - controls zoom level

	// Collapsible sections state
	let imageProcessingExpanded = true;
	let coinParametersExpanded = true;
	let heightmapPositioningExpanded = true;
	
	const ACCEPTED_TYPES = ['image/png', 'image/jpeg', 'image/gif', 'image/bmp', 'image/tiff'];
	const MAX_SIZE = 50 * 1024 * 1024; // 50MB

	function handleFileSelect(event: Event) {
		const target = event.target as HTMLInputElement;
		if (target.files && target.files[0]) {
			processFile(target.files[0]);
		}
	}

	function handleDrop(event: DragEvent) {
		event.preventDefault();
		if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
			processFile(event.dataTransfer.files[0]);
		}
	}

	let isDragOver = false;

	function handleDragOver(event: DragEvent) {
		event.preventDefault();
		isDragOver = true;
	}

	function handleDragLeave(event: DragEvent) {
		event.preventDefault();
		isDragOver = false;
	}

	async function processFile(file: File) {
		if (!ACCEPTED_TYPES.includes(file.type)) {
			alert('Please upload a valid image file (PNG, JPEG, GIF, BMP, TIFF)');
			return;
		}

		if (file.size > MAX_SIZE) {
			alert('File size must be less than 50MB');
			return;
		}

		console.log('processFile: Starting to process file', file.name, file.size);
		isUploading = true;
		
		try {
			// Create object URL for preview
			if (uploadedImageUrl) {
				URL.revokeObjectURL(uploadedImageUrl);
			}
			uploadedImageUrl = URL.createObjectURL(file);
			uploadedFile = file;
			console.log('processFile: Created image URL', uploadedImageUrl);
			
			// Reset processing state
			processedImageData = null;
			processedImageBlob = null;
			processedImageUrl = null;
			generatedSTLUrl = null;
			generationId = null;
			
			console.log('processFile: Image uploaded successfully');
			
			// Force trigger image processing after a short delay to ensure the image element is ready
			setTimeout(() => {
				console.log('processFile: Checking originalImageElement after delay', originalImageElement);
				if (originalImageElement && originalImageElement.complete && originalImageElement.naturalWidth > 0) {
					console.log('processFile: Image already loaded, processing immediately');
					updatePreview();
				} else if (originalImageElement) {
					console.log('processFile: Image not loaded yet, waiting for load event');
				} else {
					console.log('processFile: originalImageElement is null, trying to process anyway');
					// Try to trigger processing even without the image element reference
					updatePreview();
				}
			}, 100);
			
		} catch (error) {
			alert('Error loading file: ' + (error instanceof Error ? error.message : 'Unknown error'));
			console.error(error);
		} finally {
			isUploading = false;
		}
	}

	function triggerFileSelect() {
		fileInput.click();
	}

	async function updatePreview() {
		if (!uploadedImageUrl || !browser) {
			console.log('updatePreview: Missing requirements', { uploadedImageUrl: !!uploadedImageUrl, browser });
			return;
		}
		
		if (isProcessing) {
			console.log('updatePreview: Already processing, skipping');
			return;
		}
		
		isProcessing = true;
		console.log('updatePreview: Starting image processing');
		
		try {
			// Create a temporary image element for processing (not bound to DOM)
			const imageElement = document.createElement('img');
			imageElement.crossOrigin = 'anonymous';
			
			// Wait for image to load
			await new Promise<void>((resolve, reject) => {
				imageElement.onload = () => {
					console.log('updatePreview: Image loaded for processing');
					resolve();
				};
				imageElement.onerror = (error) => {
					console.error('updatePreview: Image failed to load', error);
					reject(new Error('Image failed to load'));
				};
				imageElement.src = uploadedImageUrl!;
			});
			
			const params: ImageProcessingParams = {
				grayscaleMethod,
				brightness,
				contrast,
				gamma,
				invertColors
			};
			
			console.log('updatePreview: Processing with params', params);
			
			// Process image client-side using Photon
			processedImageData = await processImage(imageElement, params);
			
			if (processedImageData) {
				console.log('updatePreview: Image processed successfully');
				
				// Convert to blob for STL generation (still needed for backend)
				processedImageBlob = await imageDataToBlob(processedImageData);
				console.log('updatePreview: Created processed image blob for STL generation');
			} else {
				throw new Error('Failed to process image');
			}
			
		} catch (error) {
			console.error('Error processing image:', error);
			alert('Error processing image: ' + (error instanceof Error ? error.message : 'Unknown error'));
		} finally {
			isProcessing = false;
			// Update canvas after processing
			if (preparedCanvas && processedImageData) {
				drawPreparedCanvas();
			}
		}
	}

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
	function resetCanvasView() {
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

	async function generateSTL() {
		if (!processedImageBlob || !browser) return;
		
		isGenerating = true;
		
		// Clear any previous state to start fresh
		stlGenerationError = null;
		generatedSTLUrl = null;
		generationId = null; // Force creation of new generation ID

		try {
			// Always create a new generation for each STL generation
			// Create a File object from the processed image blob
			const processedFile = new File([processedImageBlob], 'processed_image.png', {
				type: 'image/png'
			});
			
			// Upload the processed image (this will create a new generation_id)
			const uploadResult = await api.uploadImage(processedFile);
			generationId = uploadResult.generation_id;
			console.log('Created new generation ID:', generationId);
			
			const coinParams: CoinParameters = {
				shape: coinShape,
				diameter: coinSize,
				thickness: coinThickness,
				reliefDepth: reliefDepth,
				scale: heightmapScale,
				offsetX: offsetX,
				offsetY: offsetY,
				rotation: rotation
			};
			
			// Start STL generation
			const generateResult = await api.generateSTL(generationId, coinParams);
			generationTaskId = generateResult.task_id;
			console.log('STL generation started:', {
				generationId,
				taskId: generateResult.task_id
			});
			
			// Poll for completion
			const finalStatus = await pollTaskCompletion(generateResult.task_id, 'generation');
			
			// Get the STL download URL with timestamp for cache busting
			const timestamp = finalStatus?.stl_timestamp;
			generatedSTLUrl = api.getSTLDownloadUrl(generationId, timestamp);
			
		} catch (error) {
			console.error('Error generating STL:', error);
			// Store the exact error message from backend without generic wrapping
			stlGenerationError = error instanceof Error ? error.message : String(error);
			console.log('Setting stlGenerationError to:', stlGenerationError);
		} finally {
			isGenerating = false;
			// Always switch to result tab, whether success or failure
			activeTab = 'result';
		}
	}

	// Poll for task completion
	async function pollTaskCompletion(taskId: string, taskType: string): Promise<any> {
		const maxAttempts = 120; // 2 minutes with 1s intervals
		let attempts = 0;
		
		while (attempts < maxAttempts) {
			try {
				const status = await api.getGenerationStatus(generationId!, taskId);
				console.log(`Poll attempt ${attempts + 1}:`, {
					generationId: generationId!,
					taskId,
					status: status.status,
					error: status.error
				});
				
				if (status.status === 'SUCCESS') {
					console.log('Task completed successfully');
					return status;
				} else if (status.status === 'FAILURE') {
					console.log('Task failed, throwing error:', status.error);
					// Create a custom error that preserves the backend error message
					const backendError = new Error(status.error || `${taskType} failed`);
					backendError.name = 'BackendError';
					throw backendError;
				}
				
				// Wait 1 second before next poll (STL generation is fast now)
				await new Promise(resolve => setTimeout(resolve, 1000));
				attempts++;
			} catch (error) {
				// If this is a backend error (FAILURE status), don't retry - propagate immediately
				if (error instanceof Error && error.name === 'BackendError') {
					throw error;
				}
				// For other errors (network issues, API errors), retry until max attempts
				if (attempts === maxAttempts - 1) {
					throw error;
				}
				await new Promise(resolve => setTimeout(resolve, 1000));
				attempts++;
			}
		}
		
		throw new Error(`${taskType} timed out`);
	}

	async function downloadSTL() {
		if (!generationId) return;
		
		try {
			const blob = await api.downloadSTL(generationId);
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `coin_${generationId}.stl`;
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			URL.revokeObjectURL(url);
		} catch (error) {
			console.error('Error downloading STL:', error);
			alert('Error downloading STL: ' + (error instanceof Error ? error.message : 'Unknown error'));
		}
	}

	// Validate relief depth against thickness
	$: if (reliefDepth >= coinThickness) {
		reliefDepth = Math.max(0.1, coinThickness - 0.1);
	}

	// Handle image load event
	function handleImageLoad() {
		console.log('handleImageLoad: Image loaded, triggering initial processing');
		console.log('handleImageLoad: isProcessing =', isProcessing);
		console.log('handleImageLoad: originalImageElement =', originalImageElement);
		if (!isProcessing) {
			updatePreview();
		}
	}

	// Auto-update preview when parameters change (debounced)
	let updateTimeout: ReturnType<typeof setTimeout>;
	let lastParams = { grayscaleMethod: '', brightness: NaN, contrast: NaN, gamma: NaN, invertColors: false };
	
	$: currentParams = { grayscaleMethod, brightness, contrast, gamma, invertColors };
	$: if (uploadedImageUrl && browser && !isProcessing) {
		// Only update if parameters have actually changed
		const paramsChanged = Object.keys(currentParams).some(key => 
			lastParams[key as keyof typeof lastParams] !== currentParams[key as keyof typeof currentParams]
		);
		
		if (paramsChanged) {
			lastParams = { ...currentParams };
			clearTimeout(updateTimeout);
			updateTimeout = setTimeout(() => {
				updatePreview();
			}, 300);
		}
	}
	
	// Redraw canvas when positioning/scaling parameters change
	$: if (preparedCanvas && browser && activeTab === 'processed' && (coinSize || heightmapScale || offsetX || offsetY || rotation || coinShape || pixelsPerMM)) {
		drawPreparedCanvas();
	}
	
	// Handle canvas resize to maintain full resolution
	let resizeObserver: ResizeObserver | null = null;
	let isCanvasInitialized = false;
	
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
			
			const dpr = window.devicePixelRatio || 1;
			
			// Set internal resolution to match display size * device pixel ratio
			preparedCanvas.width = rect.width * dpr;
			preparedCanvas.height = rect.height * dpr;
			
			// Scale context to account for device pixel ratio
			const ctx = preparedCanvas.getContext('2d');
			if (ctx) {
				ctx.scale(dpr, dpr);
			}
			
			// Initialize view to center on first run
			if (!isCanvasInitialized) {
				viewX = rect.width / 2;
				viewY = rect.height / 2;
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

	// Calculate ruler marks based on coin size
	function generateRulerMarks(containerSize: number, coinSizeMM: number): Array<{position: number, label: string, major: boolean}> {
		const marks: Array<{position: number, label: string, major: boolean}> = [];
		
		// The canvas starts at 30px offset from ruler origin
		const rulerOffset = 30;
		const canvasSize = containerSize - rulerOffset; // Actual canvas size
		const canvasCenterInRuler = rulerOffset + canvasSize / 2;
		
		// Generate marks every 10mm (major) and 5mm (minor) for better spacing
		const maxRangeMM = Math.floor(canvasSize / pixelsPerMM / 2);
		
		for (let mm = -maxRangeMM; mm <= maxRangeMM; mm += 5) {
			const position = canvasCenterInRuler + (mm * pixelsPerMM);
			if (position >= rulerOffset && position <= containerSize) {
				const isMajor = mm % 10 === 0;
				const label = isMajor ? `${mm}mm` : '';
				marks.push({ position, label, major: isMajor });
			}
		}
		
		return marks;
	}

	// Update rulers when coin parameters change  
	// Ruler containers: horizontal spans canvas(600) + left ruler(30) = 630px
	// Vertical spans canvas(400) + top ruler(30) = 430px
</script>

<svelte:head>
	<title>Coin Maker - Generate 3D Printable Coins</title>
</svelte:head>

<div class="app-layout">
	<!-- Left Panel - Controls (30%) -->
	<aside class="controls-panel">
		<header class="controls-header">
			<h2><Settings size={18} /> Controls</h2>
		</header>
		<div 
			class="controls-content"
			class:drag-over={isDragOver}
			role="application"
			aria-label="File drop zone"
			on:drop={(e) => { handleDrop(e); isDragOver = false; }}
			on:dragover={handleDragOver}
			on:dragleave={handleDragLeave}
		>
		
		<section class="upload-section">
			<div class="control-grid">
				<label><Upload size={14} /> Upload Image</label>
				<div class="upload-control">
					<input
						type="file"
						bind:this={fileInput}
						on:change={handleFileSelect}
						accept=".png,.jpg,.jpeg,.gif,.bmp,.tiff"
						style="display: none;"
					/>
					<button 
						class="upload-btn secondary"
						on:click={triggerFileSelect}
						disabled={isUploading}
					>
						{#if isUploading}
							<Loader2 size={12} class="spin" />
						{:else}
							Browse
						{/if}
					</button>
					{#if uploadedFile}
						<div class="upload-status">
							<Image size={10} />
							<span>{uploadedFile.name} ({Math.round(uploadedFile.size / 1024)} KB)</span>
						</div>
					{/if}
				</div>
			</div>
		</section>

		<section class="image-processing">
			<button 
				type="button"
				class="collapsible-header" 
				aria-expanded={imageProcessingExpanded}
				aria-controls="image-processing-content"
				on:click={() => imageProcessingExpanded = !imageProcessingExpanded}
				on:keydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); imageProcessingExpanded = !imageProcessingExpanded; } }}
			>
				<span class="collapse-icon" class:expanded={imageProcessingExpanded}>▶</span>
				Image Processing
			</button>
			<div id="image-processing-content" class:hidden={!imageProcessingExpanded}>
			
			<div class="control-grid">
				<label for="grayscale-method">Grayscale Method</label>
				<select id="grayscale-method" bind:value={grayscaleMethod}>
					<option value="average">RGB Average</option>
					<option value="luminance">Luminance</option>
					<option value="red">Red Channel</option>
					<option value="green">Green Channel</option>
					<option value="blue">Blue Channel</option>
					<option value="custom">Custom Weights</option>
				</select>
			</div>

			<div class="control-grid">
				<label for="brightness">Brightness</label>
				<div class="range-control">
					<input 
						type="range" 
						id="brightness"
						min="-100" 
						max="100" 
						bind:value={brightness}
						on:mousedown={(e) => { if (e.button === 1) { brightness = 0; e.preventDefault(); } }}
					/>
					<input 
						type="number" 
						min="-100" 
						max="100" 
						bind:value={brightness}
						class="number-input"
					/>
				</div>
			</div>

			<div class="control-grid">
				<label for="contrast">Contrast</label>
				<div class="range-control">
					<input 
						type="range" 
						id="contrast"
						min="-100" 
						max="100" 
						bind:value={contrast}
						on:mousedown={(e) => { if (e.button === 1) { contrast = 0; e.preventDefault(); } }}
					/>
					<input 
						type="number" 
						min="-100" 
						max="100" 
						bind:value={contrast}
						class="number-input"
					/>
				</div>
			</div>

			<div class="control-grid">
				<label for="gamma">Gamma</label>
				<div class="range-control">
					<input 
						type="range" 
						id="gamma"
						min="0.1" 
						max="3.0" 
						step="0.1"
						bind:value={gamma}
						on:mousedown={(e) => { if (e.button === 1) { gamma = 1.0; e.preventDefault(); } }}
					/>
					<input 
						type="number" 
						min="0.1" 
						max="3.0" 
						step="0.1"
						bind:value={gamma}
						class="number-input"
					/>
				</div>
			</div>

			<div class="control-grid">
				<label for="invert-colors">Invert Colors</label>
				<input 
					id="invert-colors"
					type="checkbox" 
					bind:checked={invertColors}
				/>
			</div>
			</div>
		</section>

		<section class="coin-parameters">
			<button 
				type="button"
				class="collapsible-header" 
				aria-expanded={coinParametersExpanded}
				aria-controls="coin-parameters-content"
				on:click={() => coinParametersExpanded = !coinParametersExpanded}
				on:keydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); coinParametersExpanded = !coinParametersExpanded; } }}
			>
				<span class="collapse-icon" class:expanded={coinParametersExpanded}>▶</span>
				Coin Parameters
			</button>
			<div id="coin-parameters-content" class:hidden={!coinParametersExpanded}>
			
			<div class="control-grid">
				<label for="coin-shape">Shape</label>
				<select id="coin-shape" bind:value={coinShape}>
					<option value="circle">Circle</option>
					<option value="square">Square</option>
					<option value="hexagon">Hexagon</option>
					<option value="octagon">Octagon</option>
				</select>
			</div>

			<div class="control-grid">
				<label for="coin-size">Size (mm)</label>
				<div class="range-control">
					<input 
						type="range" 
						id="coin-size"
						min="10" 
						max="100" 
						bind:value={coinSize}
					/>
					<input 
						type="number" 
						min="0.01" 
						step="0.01"
						bind:value={coinSize}
						class="number-input"
					/>
				</div>
			</div>

			<div class="control-grid">
				<label for="coin-thickness">Thickness (mm)</label>
				<div class="range-control">
					<input 
						type="range" 
						id="coin-thickness"
						min="1" 
						max="10" 
						bind:value={coinThickness}
					/>
					<input 
						type="number" 
						min="0.01" 
						step="0.01"
						bind:value={coinThickness}
						class="number-input"
					/>
				</div>
			</div>

			<div class="control-grid">
				<label for="relief-depth">Relief Depth (mm)</label>
				<div class="range-control">
					<input 
						type="range" 
						id="relief-depth"
						min="0.1" 
						max={coinThickness} 
						step="0.1"
						bind:value={reliefDepth}
					/>
					<input 
						type="number" 
						min="0.01" 
						step="0.01"
						bind:value={reliefDepth}
						class="number-input"
					/>
				</div>
			</div>
			<div class="control-note">
				<small>Maximum height of raised/recessed areas</small>
			</div>
			</div>
		</section>

		<section class="positioning">
			<button 
				type="button"
				class="collapsible-header" 
				aria-expanded={heightmapPositioningExpanded}
				aria-controls="heightmap-positioning-content"
				on:click={() => heightmapPositioningExpanded = !heightmapPositioningExpanded}
				on:keydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); heightmapPositioningExpanded = !heightmapPositioningExpanded; } }}
			>
				<span class="collapse-icon" class:expanded={heightmapPositioningExpanded}>▶</span>
				Heightmap Positioning
			</button>
			<div id="heightmap-positioning-content" class:hidden={!heightmapPositioningExpanded}>
			
			<div class="control-grid">
				<label for="heightmap-scale">Scale (%)</label>
				<div class="range-control">
					<input 
						type="range" 
						id="heightmap-scale"
						min="10" 
						max="500" 
						bind:value={heightmapScale}
						on:mousedown={(e) => { if (e.button === 1) { heightmapScale = 100; e.preventDefault(); } }}
					/>
					<input 
						type="number" 
						min="0.00001" 
						step="0.00001"
						bind:value={heightmapScale}
						class="number-input"
					/>
				</div>
			</div>
			<div class="control-note">
				<small>Size and position of heightmap relative to coin size</small>
			</div>

			<div class="control-grid">
				<label for="offset-x">Offset X (%)</label>
				<div class="range-control">
					<input 
						type="range" 
						id="offset-x"
						min={-offsetRange} 
						max={offsetRange} 
						bind:value={offsetX}
						on:mousedown={(e) => { if (e.button === 1) { offsetX = 0; e.preventDefault(); } }}
					/>
					<input 
						type="number" 
						step="0.01"
						bind:value={offsetX}
						class="number-input"
					/>
				</div>
			</div>

			<div class="control-grid">
				<label for="offset-y">Offset Y (%)</label>
				<div class="range-control">
					<input 
						type="range" 
						id="offset-y"
						min={-offsetRange} 
						max={offsetRange} 
						bind:value={offsetY}
						on:mousedown={(e) => { if (e.button === 1) { offsetY = 0; e.preventDefault(); } }}
					/>
					<input 
						type="number" 
						step="0.01"
						bind:value={offsetY}
						class="number-input"
					/>
				</div>
			</div>

			<div class="control-grid">
				<label for="rotation">Rotation (°)</label>
				<div class="rotation-control">
					<input 
						type="range" 
						id="rotation"
						min="-360" 
						max="360" 
						bind:value={rotation}
						class="rotation-slider"
						on:mousedown={(e) => { if (e.button === 1) { rotation = 0; e.preventDefault(); } }}
					/>
					<div class="rotation-visual">
						<div class="rotation-indicator" style="transform: rotate({rotation}deg)"></div>
					</div>
					<input 
						type="number" 
						step="0.01"
						bind:value={rotation}
						class="number-input"
					/>
				</div>
			</div>
			</div>
		</section>
		</div>
		<footer class="controls-footer">
			<div class="actions">
				<button 
					on:click={generateSTL}
					disabled={!processedImageBlob || isGenerating}
				>
					{#if isGenerating}
						<Loader2 size={14} class="spin" />
						Generating...
					{:else}
						Generate STL
					{/if}
				</button>
				<button 
					class="outline" 
					disabled={!generatedSTLUrl}
					on:click={downloadSTL}
				>
					<Download size={14} />
					Download STL
				</button>
			</div>
		</footer>
	</aside>

	<!-- Right Panel - Viewer (70%) -->
	<main class="viewer-panel">
		<nav class="tabs">
			<button 
				class="tab" 
				class:active={activeTab === 'original'}
				on:click={() => activeTab = 'original'}
			>
				Original Image
			</button>
			<button 
				class="tab" 
				class:active={activeTab === 'processed'}
				on:click={() => activeTab = 'processed'}
			>
				Prepared Image
			</button>
			<button 
				class="tab" 
				class:active={activeTab === 'result'}
				on:click={() => activeTab = 'result'}
			>
				Final Result
			</button>
		</nav>

		<div class="tab-content">
			{#if activeTab === 'original'}
				<div class="image-viewer">
					{#if uploadedImageUrl}
						<img 
							bind:this={originalImageElement}
							src={uploadedImageUrl} 
							alt="" 
							class="uploaded-image"
							crossorigin="anonymous"
							on:load={handleImageLoad}
						/>
					{:else}
						<div class="placeholder-content">
							<Eye size={48} />
							<h3>Original Image</h3>
							<p>Upload an image to see it here with zoom and pan controls</p>
						</div>
					{/if}
				</div>
			{:else if activeTab === 'processed'}
				<div class="prepared-image-viewer">
					{#if processedImageData || isProcessing}
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
						
						<!-- Status bar under canvas -->
						<div class="canvas-status-bar">
							<div class="status-info">
								<span class="coin-dimensions">
									{coinSize}mm × {coinThickness}mm {coinShape}
								</span>
								<span class="zoom-info">
									Zoom: {viewZoom.toFixed(1)}x
								</span>
								<span class="position-info">
									Pan: {Math.round(viewX)}, {Math.round(viewY)}
								</span>
							</div>
							<button 
								type="button" 
								class="reset-view-btn"
								on:click={resetCanvasView}
								title="Reset view to center"
							>
								⌂ Reset View
							</button>
						</div>
					{:else if isProcessing}
						<div class="placeholder-container">
							<div class="placeholder-content">
								<Loader2 size={48} class="spin" />
								<h3>Processing Image</h3>
								<p>Applying image processing parameters...</p>
							</div>
						</div>
					{:else}
						<div class="placeholder-container">
							<div class="placeholder-content">
								<Eye size={48} />
								<h3>Prepared Image</h3>
								<p>Upload an image and adjust parameters to see the prepared result</p>
							</div>
						</div>
					{/if}
				</div>
			{:else}
				<div class="stl-viewer">
					{#if generatedSTLUrl}
						<STLViewer stlUrl={generatedSTLUrl} />
					{:else if isGenerating}
						<div class="placeholder-content">
							<Loader2 size={48} class="spin" />
							<h3>Generating STL</h3>
							<p>Creating your 3D coin model...</p>
						</div>
					{:else if stlGenerationError}
						<div class="placeholder-content error-content">
							<AlertTriangle size={48} class="error-icon" />
							<h3>STL Generation Failed</h3>
							<p class="error-message">{stlGenerationError}</p>
							<small>Check the parameters and try again, or refresh the page if the issue persists</small>
						</div>
					{:else}
						<div class="placeholder-content">
							<Eye size={48} />
							<h3>3D STL Viewer</h3>
							<p>Process an image and generate an STL to see your 3D coin model here</p>
							<small>Interactive 3D controls: drag to rotate, scroll to zoom</small>
						</div>
					{/if}
				</div>
			{/if}
		</div>
	</main>
</div>

<style>
	.app-layout {
		display: grid;
		grid-template-columns: 28% 72%;
		gap: 0.75rem;
		height: calc(100vh - 80px);
		min-height: 500px;
		max-width: 100%;
		margin: 0;
		padding: 0;
	}

	.controls-panel {
		background: var(--pico-card-background-color);
		border: 1px solid var(--pico-muted-border-color);
		border-radius: var(--pico-border-radius);
		font-size: 12pt;
		display: flex;
		flex-direction: column;
		height: 100%;
		max-height: 100%;
		overflow: hidden;
	}

	.controls-header {
		padding: 0.75rem 0.75rem 0.5rem 0.75rem;
		border-bottom: 1px solid var(--pico-muted-border-color);
		flex-shrink: 0;
	}

	.controls-content {
		padding: 0.75rem;
		overflow-y: auto;
		flex: 1;
		min-height: 0;
		transition: background-color 0.2s;
	}

	.controls-footer {
		padding: 0.5rem 0.75rem 0.75rem 0.75rem;
		border-top: 1px solid var(--pico-muted-border-color);
		flex-shrink: 0;
	}

	.controls-panel h2 {
		margin: 0;
		display: flex;
		align-items: center;
		gap: 0.375rem;
		font-size: 1rem;
		color: var(--pico-color);
	}

	.controls-panel section {
		margin-bottom: 1rem;
	}



	.uploaded-image {
		max-width: 100%;
		max-height: 100%;
		object-fit: contain;
		border-radius: var(--pico-border-radius);
	}

	:global(.spin) {
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}


	.control-grid {
		display: grid;
		grid-template-columns: 1fr 1.5fr;
		gap: 0.5rem;
		align-items: baseline;
		margin-bottom: 0.4rem;
	}

	.range-control {
		display: flex;
		gap: 0.5rem;
		align-items: center;
	}

	.range-control input[type="range"] {
		flex: 1;
		margin: 0;
		align-self: baseline;
		margin-top: 0.25rem;
		height: 16px;
	}

	.upload-control {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.upload-btn {
		padding: 0.2rem 0.4rem;
		font-size: 10pt;
		min-width: 55px;
		margin: 0;
	}

	.upload-status {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		font-size: 9pt;
		color: var(--pico-muted-color);
		flex: 1;
		min-width: 0;
	}

	.upload-status span {
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}


	.control-note {
		grid-column: 1 / -1;
		margin-top: -0.25rem;
		margin-bottom: 0.25rem;
	}

	.controls-panel select {
		font-size: 11pt;
		padding: 0.25rem 0.4rem;
		margin: 0;
	}

	.controls-panel input[type="checkbox"] {
		margin: 0;
		justify-self: start;
		align-self: center;
	}

	/* Drop zone styling for content area */
	.controls-content.drag-over {
		background-color: var(--pico-primary-background);
	}

	/* Hidden content utility */
	.hidden {
		display: none;
	}

	/* Collapsible sections */
	.collapsible-header {
		background: none;
		border: none;
		padding: 0;
		margin: 0;
		font: inherit;
		color: inherit;
		cursor: pointer;
		display: flex;
		align-items: center;
		gap: 0.375rem;
		user-select: none;
		transition: color 0.2s;
		width: 100%;
		text-align: left;
		font-size: 1rem;
		font-weight: 600;
	}

	.collapsible-header:hover {
		color: var(--pico-primary);
	}

	.collapsible-header:focus {
		outline: 2px solid var(--pico-primary);
		outline-offset: 2px;
	}

	.collapse-icon {
		font-size: 10pt;
		transition: transform 0.2s;
		display: inline-block;
		width: 12px;
	}

	.collapse-icon.expanded {
		transform: rotate(90deg);
	}

	/* Custom slider styling */
	.controls-panel input[type="range"] {
		-webkit-appearance: none;
		appearance: none;
		height: 4px;
		background: var(--pico-muted-border-color);
		border-radius: 2px;
		outline: none;
	}

	.controls-panel input[type="range"]::-webkit-slider-thumb {
		-webkit-appearance: none;
		appearance: none;
		width: 14px;
		height: 14px;
		border-radius: 50%;
		background: var(--pico-primary);
		cursor: pointer;
		border: 2px solid var(--pico-background-color);
		box-shadow: 0 0 0 1px var(--pico-muted-border-color);
	}

	.controls-panel input[type="range"]::-moz-range-thumb {
		width: 14px;
		height: 14px;
		border-radius: 50%;
		background: var(--pico-primary);
		cursor: pointer;
		border: 2px solid var(--pico-background-color);
		box-shadow: 0 0 0 1px var(--pico-muted-border-color);
	}

	.controls-panel input[type="range"]::-moz-range-track {
		height: 4px;
		background: var(--pico-muted-border-color);
		border-radius: 2px;
		border: none;
	}

	/* Prepared Image Viewer with Status Bar */
	.prepared-image-viewer {
		height: 100%;
		display: flex;
		flex-direction: column;
		background: var(--pico-background-color);
		border-radius: var(--pico-border-radius);
	}

	.prepared-canvas-container {
		position: relative;
		width: 100%;
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		overflow: hidden;
	}
	
	.prepared-canvas {
		width: 100%;
		height: 100%;
		cursor: grab;
		display: block;
	}
	
	.prepared-canvas:active {
		cursor: grabbing;
	}



	.prepared-canvas {
		position: relative;
		border: 1px solid var(--pico-muted-border-color);
		border-radius: var(--pico-border-radius);
		background: #f8f9fa;
		z-index: 1;
		margin-left: 30px;
		margin-top: 30px;
	}


	.control-grid label {
		display: block;
		margin: 0;
		font-size: 11pt;
		color: var(--pico-color);
		align-self: baseline;
		padding-top: 0.25rem;
	}


	.number-input {
		width: 60px;
		padding: 0.125rem 0.25rem;
		font-size: 11pt;
		margin: 0;
		align-self: baseline;
		margin-top: 0.25rem;
	}




	.rotation-control {
		display: flex;
		align-items: center;
		gap: 0.375rem;
	}

	.rotation-control .rotation-slider {
		flex: 1;
		margin: 0;
	}

	.rotation-slider {
		flex: 1;
		margin-bottom: 0 !important;
	}

	.rotation-visual {
		width: 32px;
		height: 32px;
		border: 2px solid var(--pico-muted-border-color);
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		position: relative;
	}

	.rotation-indicator {
		width: 16px;
		height: 2px;
		background: var(--pico-primary-500);
		transform-origin: center;
		transition: transform 0.1s ease;
	}



	.actions {
		display: flex;
		flex-direction: row;
		gap: 0.5rem;
	}

	.actions button {
		font-size: 10pt;
		padding: 0.375rem 0.5rem;
		color: var(--pico-color);
		flex: 1;
		min-width: 0;
	}

	.actions button:not([disabled]) {
		color: var(--pico-color);
	}

	.actions button[disabled] {
		color: var(--pico-muted-color);
	}

	.viewer-panel {
		background: var(--pico-card-background-color);
		border: 1px solid var(--pico-muted-border-color);
		border-radius: var(--pico-border-radius);
		overflow: hidden;
		display: flex;
		flex-direction: column;
		font-size: 0.85rem;
	}

	.tabs {
		display: flex;
		background: var(--pico-background-color);
		border-bottom: 1px solid var(--pico-muted-border-color);
	}

	.tab {
		flex: 1;
		background: transparent !important;
		border: none;
		padding: 0.5rem;
		cursor: pointer;
		transition: all 0.2s;
		border-bottom: 3px solid transparent;
		font-size: 0.8rem;
		color: var(--pico-color) !important;
		--pico-primary-inverse: var(--pico-color);
	}

	.tab:hover {
		background: var(--pico-muted-background-color) !important;
		color: var(--pico-color) !important;
		--pico-primary-inverse: var(--pico-color);
	}

	/* Force override Pico CSS button styling for tabs */
	.tabs button.tab {
		color: var(--pico-color) !important;
		background-color: transparent !important;
		border-color: transparent !important;
	}

	.tabs button.tab:hover {
		color: var(--pico-color) !important;
		background-color: var(--pico-muted-background-color) !important;
		border-color: transparent !important;
	}

	.tabs button.tab.active {
		color: var(--pico-color) !important;
		background-color: var(--pico-card-background-color) !important;
		border-color: transparent !important;
	}

	.tab.active {
		background: var(--pico-card-background-color) !important;
		border-bottom-color: var(--pico-primary-500);
		font-weight: 600;
		color: var(--pico-color) !important;
		--pico-primary-inverse: var(--pico-color);
	}

	.tab-content {
		flex: 1;
		padding: 0.25rem;
		overflow: hidden;
	}

	.image-viewer,
	.stl-viewer {
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--pico-background-color);
		border-radius: var(--pico-border-radius);
	}

	.placeholder-content {
		text-align: center;
		color: var(--pico-muted-color);
		font-size: 0.85rem;
	}

	.placeholder-content h3 {
		margin: 0.5rem 0 0.25rem;
		font-size: 1rem;
		color: var(--pico-color);
	}

	.placeholder-content p {
		margin: 0.25rem 0;
		font-size: 0.8rem;
		color: var(--pico-muted-color);
	}

	/* Error state styling */
	.error-content {
		border: 1px solid #f56565;
		background-color: #fed7d7;
		border-radius: var(--pico-border-radius);
		padding: 1rem;
	}

	.error-icon {
		color: #f56565;
		margin-bottom: 0.5rem;
	}

	.error-content h3 {
		color: #c53030;
		margin: 0.5rem 0 0.25rem;
	}

	.error-message {
		color: #742a2a;
		font-weight: 500;
		margin: 0.5rem 0;
		white-space: pre-wrap;
		word-break: break-word;
	}

	.error-content small {
		color: #a0a0a0;
		font-style: italic;
	}

	/* Mobile Responsiveness */
	@media (max-width: 768px) {
		.app-layout {
			grid-template-columns: 1fr;
			grid-template-rows: auto 1fr;
			height: auto;
			gap: 0.5rem;
		}

		.controls-panel {
			height: auto;
			max-height: none;
			padding: 0.5rem;
			font-size: 0.8rem;
		}

		.viewer-panel {
			min-height: 400px;
		}

		.tab-content {
			padding: 0.25rem;
		}
	}

	/* Canvas status bar */
	.canvas-status-bar {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 8px 12px;
		background: var(--pico-muted-background-color);
		border-top: 1px solid var(--pico-muted-border-color);
		font-size: 12px;
		color: var(--pico-muted-color);
		min-height: 36px;
	}

	.status-info {
		display: flex;
		gap: 16px;
		align-items: center;
	}

	.coin-dimensions {
		font-weight: 600;
		color: var(--pico-color);
	}

	.zoom-info, .position-info {
		font-family: monospace;
		font-size: 11px;
	}

	.reset-view-btn {
		background: var(--pico-primary);
		color: white;
		border: none;
		border-radius: 4px;
		padding: 4px 8px;
		margin: 0;
		display: flex;
		align-items: center;
		gap: 4px;
		cursor: pointer;
		font-size: 11px;
		transition: background-color 0.2s;
		white-space: nowrap;
	}

	.reset-view-btn:hover {
		background: var(--pico-primary-hover);
	}

	/* Placeholder container to fill height and center content */
	.placeholder-container {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
	}
</style>
