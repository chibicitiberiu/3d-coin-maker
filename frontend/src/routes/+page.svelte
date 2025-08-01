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
	<title>3D Coin Maker - Generate 3D Printable Coins</title>
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

<style lang="scss">
	@use '$lib/styles/variables' as *;
	@use '$lib/styles/mixins' as *;

	/* All styles have been migrated to individual components */
	/* This page now only contains the main layout structure using slots */
</style>
