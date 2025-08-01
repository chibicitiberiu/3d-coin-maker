<script lang="ts">
	import { Upload, Settings, Eye, Download, Loader2, Image, AlertTriangle } from 'lucide-svelte';
	import { browser } from '$app/environment';
	import { onDestroy } from 'svelte';
	import STLViewer from '$lib/STLViewer.svelte';
	import CanvasViewer from '$lib/CanvasViewer.svelte';
	import ImageUpload from '$lib/ImageUpload.svelte';
	import ImageProcessingControls from '$lib/ImageProcessingControls.svelte';
	import CoinParametersControls from '$lib/CoinParametersControls.svelte';
	import HeightmapPositioningControls from '$lib/HeightmapPositioningControls.svelte';
	import TabControl from '$lib/TabControl.svelte';

	// Import stores and services
	import {
		generationState,
		generatedSTLUrl,
		isGenerating as storeIsGenerating,
		stlGenerationError,
		generationProgress,
		generationActions
	} from '$lib/stores/generationState';
	import {
		imageProcessingState,
		uploadedFile,
		uploadedImageUrl,
		isProcessing as storeIsProcessing,
		processedImageData,
		processedImageBlob,
		processedImageUrl,
		grayscaleMethod,
		brightness,
		contrast,
		gamma,
		invertColors,
		imageProcessingActions
	} from '$lib/stores/imageProcessingState';
	import {
		coinParametersState,
		coinShape,
		coinSize,
		coinThickness,
		reliefDepth,
		heightmapScale,
		offsetX,
		offsetY,
		rotation,
		pixelsPerMM,
		coinParametersActions
	} from '$lib/stores/coinParametersState';
	import {
		uiState,
		activeTab,
		imageProcessingExpanded,
		coinParametersExpanded,
		heightmapPositioningExpanded,
		uiActions
	} from '$lib/stores/uiState';
	import { generationService } from '$lib/services/GenerationService';
	import { imageProcessingService } from '$lib/services/ImageProcessingService';
	import type { CoinParameters } from '$lib/services/BackendService';
	
	// Component references
	let originalImageElement: HTMLImageElement;
	let canvasViewer: CanvasViewer;
	let imageUpload: ImageUpload;
	
	// Reactive store subscriptions for local use
	$: currentUploadedFile = $uploadedFile;
	$: currentUploadedImageUrl = $uploadedImageUrl;
	$: currentProcessedImageData = $processedImageData;
	$: currentProcessedImageBlob = $processedImageBlob;
	$: currentIsProcessing = $storeIsProcessing;
	$: currentIsGenerating = $storeIsGenerating;
	$: currentGeneratedSTLUrl = $generatedSTLUrl;
	$: currentStlGenerationError = $stlGenerationError;
	$: currentGenerationProgress = $generationProgress;
	$: currentActiveTab = $activeTab;

	// Current parameters for reactive statements
	$: currentParams = {
		grayscaleMethod: $grayscaleMethod,
		brightness: $brightness,
		contrast: $contrast,
		gamma: $gamma,
		invertColors: $invertColors
	};

	// Coin parameters for reactive statements
	$: currentCoinParams = {
		shape: $coinShape,
		diameter: $coinSize,
		thickness: $coinThickness,
		reliefDepth: $reliefDepth,
		scale: $heightmapScale,
		offsetX: $offsetX,
		offsetY: $offsetY,
		rotation: $rotation
	};

	// Tab definitions
	$: tabs = [
		{ id: 'original', label: 'Original Image' },
		{ id: 'processed', label: 'Prepared Image' },
		{ id: 'result', label: 'Final Result' }
	];
	
	
	
	
	
	
	// Handle file upload from ImageUpload component
	function handleFileProcessed(event: CustomEvent<{ file: File; imageUrl: string }>) {
		const { file, imageUrl } = event.detail;
		
		// Reset state through store actions
		imageProcessingActions.setUploadedFile(file, imageUrl);
		imageProcessingActions.resetProcessingState();
		generationActions.reset();
		
		console.log('File processed successfully:', file.name);
		
		// The reactive statement will automatically trigger processing for the new image
	}

	// Handle upload errors from ImageUpload component
	function handleUploadError(event: CustomEvent<{ message: string }>) {
		alert(event.detail.message);
	}

	// Handle image processing parameter changes
	function handleImageProcessingChanged(event: CustomEvent<{
		grayscaleMethod: 'average' | 'luminance' | 'red' | 'green' | 'blue' | 'custom';
		brightness: number;
		contrast: number;
		gamma: number;
		invertColors: boolean;
		isDragFeedback?: boolean;
	}>) {
		const { grayscaleMethod: newGrayscaleMethod, brightness: newBrightness, contrast: newContrast, gamma: newGamma, invertColors: newInvertColors, isDragFeedback } = event.detail;
		imageProcessingActions.updateParams({
			grayscaleMethod: newGrayscaleMethod,
			brightness: newBrightness,
			contrast: newContrast,
			gamma: newGamma,
			invertColors: newInvertColors
		});
		
		// Use adaptive processing for drag feedback, normal processing otherwise
		if (isDragFeedback) {
			isDragProcessing = true;
			updatePreviewAdaptive().finally(() => {
				// Short delay before allowing regular processing again
				setTimeout(() => {
					isDragProcessing = false;
				}, 100);
			});
		} else {
			isDragProcessing = false;
			updatePreview();
		}
	}

	// Handle coin parameter changes
	function handleCoinParametersChanged(event: CustomEvent<{
		coinShape: 'circle' | 'square' | 'hexagon' | 'octagon';
		coinSize: number;
		coinThickness: number;
		reliefDepth: number;
	}>) {
		const { coinShape: newCoinShape, coinSize: newCoinSize, coinThickness: newCoinThickness, reliefDepth: newReliefDepth } = event.detail;
		coinParametersActions.updateCoinParameters({
			coinShape: newCoinShape,
			coinSize: newCoinSize,
			coinThickness: newCoinThickness,
			reliefDepth: newReliefDepth
		});
	}

	// Handle heightmap positioning parameter changes
	function handleHeightmapPositioningChanged(event: CustomEvent<{
		heightmapScale: number;
		offsetX: number;
		offsetY: number;
		rotation: number;
	}>) {
		const { heightmapScale: newHeightmapScale, offsetX: newOffsetX, offsetY: newOffsetY, rotation: newRotation } = event.detail;
		coinParametersActions.updateHeightmapPositioning({
			heightmapScale: newHeightmapScale,
			offsetX: newOffsetX,
			offsetY: newOffsetY,
			rotation: newRotation
		});
		
		// These parameters only affect canvas display, not image processing
		// CanvasViewer will automatically redraw when its props change
	}

	// Handle tab changes
	function handleTabChanged(event: CustomEvent<{ tabId: string }>) {
		uiActions.setActiveTab(event.detail.tabId as 'original' | 'processed' | 'result');
	}

	// Handle cancel processing request from controls
	function handleCancelProcessing() {
		console.log('Canceling all pending processing');
		imageProcessingService.cancel();
	}

	async function updatePreview() {
		if (!currentUploadedImageUrl || !browser) {
			console.log('updatePreview: Missing requirements', { uploadedImageUrl: !!currentUploadedImageUrl, browser });
			return;
		}
		
		if (currentIsProcessing) {
			console.log('updatePreview: Already processing, skipping');
			return;
		}
		
		console.log('updatePreview: Starting image processing via service');
		
		try {
			const result = await imageProcessingService.processImage(
				currentUploadedImageUrl,
				currentParams,
				(progress) => {
					console.log(`Processing ${progress.step}: ${progress.progress}% - ${progress.message}`);
				}
			);
			
			if (!result.success && result.error) {
				throw new Error(result.error);
			}
			
			console.log('updatePreview: Image processed successfully via service');
			
		} catch (error) {
			// Don't show alerts for cancelled requests - this is expected behavior
			if (error instanceof Error && (error.message === 'Request cancelled' || error.message === 'Processing cancelled')) {
				console.log('Image processing was cancelled (expected behavior)');
				return;
			}
			console.error('Error processing image:', error);
			alert('Error processing image: ' + (error instanceof Error ? error.message : 'Unknown error'));
		}
	}


	// Reset view function for the canvas component
	function resetCanvasView() {
		if (canvasViewer) {
			canvasViewer.resetCanvasView();
		}
	}

	async function updatePreviewAdaptive() {
		if (!currentUploadedImageUrl || !browser) {
			console.log('updatePreviewAdaptive: Missing requirements', { uploadedImageUrl: !!currentUploadedImageUrl, browser });
			return;
		}
		
		try {
			console.log('updatePreviewAdaptive: Starting adaptive image processing via service');
			
			const result = await imageProcessingService.processImageAdaptive(
				currentUploadedImageUrl,
				{
					grayscaleMethod: $grayscaleMethod,
					brightness: $brightness,
					contrast: $contrast,
					gamma: $gamma,
					invertColors: $invertColors
				},
				(progress) => {
					console.log(`Processing ${progress.step}: ${progress.progress}% - ${progress.message}`);
				}
			);
			
			if (!result.success && result.error) {
				// Only throw for real errors, not throttling messages
				if (!result.error.startsWith('Throttled:')) {
					throw new Error(result.error);
				}
			}
			
			console.log('updatePreviewAdaptive: Image processed successfully via adaptive service');
			
		} catch (error) {
			// Don't show alerts for cancelled requests or throttling - this is expected behavior
			if (error instanceof Error && (
				error.message === 'Request cancelled' || 
				error.message === 'Processing cancelled' ||
				error.message.startsWith('Throttled:')
			)) {
				console.log('Adaptive processing was cancelled or throttled (expected behavior)');
				return;
			}
			console.error('Error processing image (adaptive):', error);
			// Don't show alert for adaptive processing errors - they're handled gracefully
		}
	}

	async function generateSTL() {
		if (!currentProcessedImageBlob || !browser) return;
		
		// Switch to result tab immediately when generation starts
		uiActions.setActiveTab('result');
		
		console.log('generateSTL: Starting STL generation via service');
		
		try {
			const result = await generationService.generateSTL(
				currentProcessedImageBlob,
				currentCoinParams,
				(progress) => {
					console.log(`Generation ${progress.step}: ${progress.progress}% - ${progress.message}`);
					// Store progress in state for UI updates
					generationActions.setGenerationProgress(progress);
				}
			);
			
			if (!result.success && result.error) {
				throw new Error(result.error);
			}
			
			console.log('generateSTL: STL generation completed via service');
			
		} catch (error) {
			console.error('Error generating STL:', error);
			alert('Error generating STL: ' + (error instanceof Error ? error.message : 'Unknown error'));
		} finally {
			// Always switch to result tab, whether success or failure
			uiActions.setActiveTab('result');
		}
	}

	async function downloadSTL() {
		const currentGenerationId = $generationState.generationId;
		if (!currentGenerationId) return;
		
		try {
			await generationService.downloadSTL(currentGenerationId);
		} catch (error) {
			console.error('Error downloading STL:', error);
			alert('Error downloading STL: ' + (error instanceof Error ? error.message : 'Unknown error'));
		}
	}

	// Relief depth validation moved to CoinParametersControls component

	// Handle image load event
	function handleImageLoad() {
		console.log('handleImageLoad: Image loaded, reactive statement will handle processing if needed');
		// The reactive statement will handle processing automatically
	}

	// Auto-update preview when parameters change (debounced)
	let updateTimeout: ReturnType<typeof setTimeout>;
	let lastParams = { grayscaleMethod: '', brightness: NaN, contrast: NaN, gamma: NaN, invertColors: false };
	let lastImageUrl = '';
	let isDragProcessing = false; // Track if we're in drag feedback mode
	
	// Reactive statement for handling parameter changes with debouncing
	$: if (currentUploadedImageUrl && browser && !currentIsProcessing && !isDragProcessing) {
		// Check if this is a new image
		const isNewImage = currentUploadedImageUrl !== lastImageUrl;
		
		// Only update if parameters have actually changed OR it's a new image
		const paramsChanged = Object.keys(currentParams).some(key => 
			lastParams[key as keyof typeof lastParams] !== currentParams[key as keyof typeof currentParams]
		);
		
		if (paramsChanged || isNewImage) {
			lastParams = { ...currentParams };
			lastImageUrl = currentUploadedImageUrl;
			
			clearTimeout(updateTimeout);
			updateTimeout = setTimeout(() => {
				updatePreview();
			}, isNewImage ? 0 : 300); // No delay for new images, 300ms delay for parameter changes (more responsive)
		}
	}
	
	// Canvas rendering is now handled by CanvasViewer component

	// Calculate ruler marks based on coin size
	function generateRulerMarks(containerSize: number, coinSizeMM: number): Array<{position: number, label: string, major: boolean}> {
		const marks: Array<{position: number, label: string, major: boolean}> = [];
		
		// The canvas starts at 30px offset from ruler origin
		const rulerOffset = 30;
		const canvasSize = containerSize - rulerOffset; // Actual canvas size
		const canvasCenterInRuler = rulerOffset + canvasSize / 2;
		
		// Generate marks every 10mm (major) and 5mm (minor) for better spacing
		const maxRangeMM = Math.floor(canvasSize / $pixelsPerMM / 2);
		
		for (let mm = -maxRangeMM; mm <= maxRangeMM; mm += 5) {
			const position = canvasCenterInRuler + (mm * $pixelsPerMM);
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
		<div class="controls-content">
		
		<ImageUpload
			bind:this={imageUpload}
			on:fileProcessed={handleFileProcessed}
			on:error={handleUploadError}
		/>

		<ImageProcessingControls
			grayscaleMethod={$grayscaleMethod}
			brightness={$brightness}
			contrast={$contrast}
			gamma={$gamma}
			invertColors={$invertColors}
			bind:expanded={$imageProcessingExpanded}
			on:parametersChanged={handleImageProcessingChanged}
			on:cancelProcessing={handleCancelProcessing}
		/>

		<CoinParametersControls
			coinShape={$coinShape}
			coinSize={$coinSize}
			coinThickness={$coinThickness}
			reliefDepth={$reliefDepth}
			bind:expanded={$coinParametersExpanded}
			on:parametersChanged={handleCoinParametersChanged}
		/>

		<HeightmapPositioningControls
			heightmapScale={$heightmapScale}
			offsetX={$offsetX}
			offsetY={$offsetY}
			rotation={$rotation}
			bind:expanded={$heightmapPositioningExpanded}
			on:parametersChanged={handleHeightmapPositioningChanged}
		/>
		</div>
		<footer class="controls-footer">
			<div class="actions">
				<button 
					on:click={generateSTL}
					disabled={!currentProcessedImageBlob || currentIsGenerating}
				>
					{#if currentIsGenerating}
						<Loader2 size={14} class="spin" />
						Generating...
					{:else}
						Generate STL
					{/if}
				</button>
				<button 
					class="outline" 
					disabled={!currentGeneratedSTLUrl}
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
		<TabControl 
			activeTab={currentActiveTab}
			{tabs}
			on:tabChanged={handleTabChanged}
		/>

		<div class="tab-content">
			{#if currentActiveTab === 'original'}
				<div class="image-viewer">
					{#if currentUploadedImageUrl}
						<img 
							bind:this={originalImageElement}
							src={currentUploadedImageUrl} 
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
			{:else if currentActiveTab === 'processed'}
				<div class="prepared-image-viewer">
					{#if currentProcessedImageData || currentIsProcessing}
						<CanvasViewer
							bind:this={canvasViewer}
							processedImageData={currentProcessedImageData}
							coinSize={$coinSize}
							coinThickness={$coinThickness}
							coinShape={$coinShape}
							heightmapScale={$heightmapScale}
							offsetX={$offsetX}
							offsetY={$offsetY}
							rotation={$rotation}
							pixelsPerMM={$pixelsPerMM}
							activeTab={currentActiveTab}
						/>
						
						<!-- Status bar under canvas -->
						<div class="canvas-status-bar">
							<div class="status-info">
								<span class="coin-dimensions">
									{$coinSize}mm × {$coinThickness}mm {$coinShape}
								</span>
								{#if canvasViewer}
									{@const viewState = canvasViewer.getViewState()}
									<span class="zoom-info">
										Zoom: {viewState.viewZoom.toFixed(1)}x
									</span>
									<span class="position-info">
										Pan: {Math.round(viewState.viewX)}, {Math.round(viewState.viewY)}
									</span>
								{/if}
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
					{:else if currentIsProcessing}
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
					{#if currentGeneratedSTLUrl}
						<STLViewer stlUrl={currentGeneratedSTLUrl} />
					{:else if currentIsGenerating}
						<div class="placeholder-content">
							<Loader2 size={48} class="spin" />
							<h3>Generating STL</h3>
							{#if currentGenerationProgress}
								<div class="progress-container">
									<div class="progress-bar">
										<div 
											class="progress-fill" 
											style="width: {currentGenerationProgress.progress}%"
										></div>
									</div>
									<p class="progress-text">
										{Math.round(currentGenerationProgress.progress)}% - {currentGenerationProgress.message}
									</p>
								</div>
							{:else}
								<p>Creating your 3D coin model...</p>
							{/if}
						</div>
					{:else if currentStlGenerationError}
						<div class="placeholder-content error-content">
							<AlertTriangle size={48} class="error-icon" />
							<h3>STL Generation Failed</h3>
							<p class="error-message">{currentStlGenerationError}</p>
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

	/* Upload styling moved to ImageUpload component */


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

	/* Drop zone styling moved to ImageUpload component */

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

	/* Canvas styling moved to CanvasViewer component */


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

	/* Progress bar styling */
	.progress-container {
		margin: 1rem auto;
		max-width: 300px;
		width: 100%;
	}

	.progress-bar {
		width: 100%;
		height: 8px;
		background-color: var(--pico-muted-border-color);
		border-radius: 4px;
		overflow: hidden;
		margin-bottom: 0.5rem;
	}

	.progress-fill {
		height: 100%;
		background: var(--pico-primary);
		border-radius: 4px;
		transition: width 0.3s ease;
		min-width: 0;
	}

	.progress-text {
		font-size: 0.75rem;
		color: var(--pico-color);
		margin: 0;
		text-align: center;
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
