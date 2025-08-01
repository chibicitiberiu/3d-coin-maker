<script lang="ts">
	import { browser } from '$app/environment';
	import CanvasViewer from '$lib/CanvasViewer.svelte';
	import ImageUpload from '$lib/ImageUpload.svelte';
	import ImageProcessingControls from '$lib/ImageProcessingControls.svelte';
	import CoinParametersControls from '$lib/CoinParametersControls.svelte';
	import HeightmapPositioningControls from '$lib/HeightmapPositioningControls.svelte';
	import TabControl from '$lib/TabControl.svelte';
	import MainLayout from '$lib/components/MainLayout.svelte';
	import WorkflowActions from '$lib/components/WorkflowActions.svelte';
	import TabContentViewer from '$lib/components/TabContentViewer.svelte';

	// Import stores and services
	import {
		generatedSTLUrl,
		isGenerating as storeIsGenerating,
		stlGenerationError,
		generationProgress,
		generationActions
	} from '$lib/stores/generationState';
	import {
		uploadedFile,
		uploadedImageUrl,
		isProcessing as storeIsProcessing,
		processedImageData,
		processedImageBlob,
		grayscaleMethod,
		brightness,
		contrast,
		gamma,
		invertColors,
		imageProcessingActions
	} from '$lib/stores/imageProcessingState';
	import {
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
		activeTab,
		imageProcessingExpanded,
		coinParametersExpanded,
		heightmapPositioningExpanded,
		uiActions
	} from '$lib/stores/uiState';
	import { generationService } from '$lib/services/GenerationService';
	import { imageProcessingService } from '$lib/services/ImageProcessingService';
	import { createEventHandlersService, type EventHandlersService } from '$lib/services/EventHandlersService';
	import { coordinateService } from '$lib/services/CoordinateService';
	
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
	// Event handlers moved to EventHandlersService

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

	// Generate and download functions moved to WorkflowActions component
	
	// Create event handlers service
	let eventHandlers: EventHandlersService;
	$: eventHandlers = createEventHandlersService(
		updatePreview,
		updatePreviewAdaptive,
		(value: boolean) => { isDragProcessing = value; }
	);

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

	// Ruler calculation moved to CoordinateService
</script>

<svelte:head>
	<title>Coin Maker - Generate 3D Printable Coins</title>
</svelte:head>

<MainLayout>
	<svelte:fragment slot="controls">
		<ImageUpload
			bind:this={imageUpload}
			on:fileProcessed={eventHandlers.handleFileProcessed}
			on:error={eventHandlers.handleUploadError}
		/>

		<ImageProcessingControls
			grayscaleMethod={$grayscaleMethod}
			brightness={$brightness}
			contrast={$contrast}
			gamma={$gamma}
			invertColors={$invertColors}
			bind:expanded={$imageProcessingExpanded}
			on:parametersChanged={eventHandlers.handleImageProcessingChanged}
			on:cancelProcessing={handleCancelProcessing}
		/>

		<CoinParametersControls
			coinShape={$coinShape}
			coinSize={$coinSize}
			coinThickness={$coinThickness}
			reliefDepth={$reliefDepth}
			bind:expanded={$coinParametersExpanded}
			on:parametersChanged={eventHandlers.handleCoinParametersChanged}
		/>

		<HeightmapPositioningControls
			heightmapScale={$heightmapScale}
			offsetX={$offsetX}
			offsetY={$offsetY}
			rotation={$rotation}
			bind:expanded={$heightmapPositioningExpanded}
			on:parametersChanged={eventHandlers.handleHeightmapPositioningChanged}
		/>
	</svelte:fragment>

	<svelte:fragment slot="actions">
		<WorkflowActions />
	</svelte:fragment>

	<svelte:fragment slot="viewer">
		<TabControl 
			activeTab={currentActiveTab}
			{tabs}
			on:tabChanged={eventHandlers.handleTabChanged}
		/>

		<TabContentViewer 
			activeTab={currentActiveTab}
			bind:originalImageElement
			bind:canvasViewer
			onImageLoad={handleImageLoad}
			onResetCanvasView={resetCanvasView}
		/>
	</svelte:fragment>
</MainLayout>

<style>
	/* Layout styles moved to MainLayout component */




	/* Controls panel styles moved to individual components */



	/* Uploaded image styles moved to TabContentViewer */

	/* Spin animation moved to components that use it */


	/* Control grid and range styles moved to control components */

	/* Upload styling moved to ImageUpload component */


	/* Control note, select, checkbox, and hidden utility styles moved to components */

	/* Collapsible section styles moved to control components */

	/* All control styling moved to individual components */




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



	/* Actions styles moved to WorkflowActions component */



	/* Tab content styles moved to TabContentViewer component */


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
	/* Mobile responsive styles moved to MainLayout component */

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
