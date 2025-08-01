<script lang="ts">
	import { Eye, Loader2, Image, AlertTriangle } from 'lucide-svelte';
	import STLViewer from '$lib/STLViewer.svelte';
	import CanvasViewer from '$lib/CanvasViewer.svelte';
	import { 
		uploadedImageUrl,
		isProcessing as storeIsProcessing,
		processedImageData
	} from '$lib/stores/imageProcessingState';
	import {
		coinShape,
		coinSize,
		coinThickness,
		heightmapScale,
		offsetX,
		offsetY,
		rotation,
		pixelsPerMM
	} from '$lib/stores/coinParametersState';
	import {
		generatedSTLUrl,
		isGenerating as storeIsGenerating,
		stlGenerationError,
		generationProgress
	} from '$lib/stores/generationState';

	export let activeTab: string;
	export let originalImageElement: HTMLImageElement | undefined = undefined;
	export let canvasViewer: CanvasViewer | undefined = undefined;
	export let onImageLoad: () => void = () => {};
	export let onResetCanvasView: () => void = () => {};

	// Reactive store subscriptions
	$: currentUploadedImageUrl = $uploadedImageUrl;
	$: currentProcessedImageData = $processedImageData;
	$: currentIsProcessing = $storeIsProcessing;
	$: currentIsGenerating = $storeIsGenerating;
	$: currentGeneratedSTLUrl = $generatedSTLUrl;
	$: currentStlGenerationError = $stlGenerationError;
	$: currentGenerationProgress = $generationProgress;
</script>

<div class="tab-content">
	{#if activeTab === 'original'}
		<div class="image-viewer">
			{#if currentUploadedImageUrl}
				<img 
					bind:this={originalImageElement}
					src={currentUploadedImageUrl} 
					alt="" 
					class="uploaded-image"
					crossorigin="anonymous"
					on:load={onImageLoad}
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
					activeTab={activeTab}
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
						on:click={onResetCanvasView}
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

<style>
	.tab-content {
		flex: 1;
		padding: 0.25rem;
		overflow: hidden;
		background: var(--pico-card-background-color);
		display: flex;
		flex-direction: column;
	}

	.image-viewer,
	.prepared-image-viewer,
	.stl-viewer {
		flex: 1;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.uploaded-image {
		max-width: 100%;
		max-height: 100%;
		object-fit: contain;
		cursor: grab;
		user-select: none;
	}

	.uploaded-image:active {
		cursor: grabbing;
	}

	.placeholder-content {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		text-align: center;
		color: var(--pico-muted-color);
		padding: 2rem;
		flex: 1;
	}

	.placeholder-container {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.placeholder-content h3 {
		margin: 1rem 0 0.5rem;
		color: var(--pico-color);
	}

	.placeholder-content p {
		margin: 0;
		font-size: 0.875rem;
	}

	.placeholder-content small {
		color: var(--pico-muted-color);
		font-style: italic;
	}

	/* Progress bar styles */
	.progress-container {
		width: 100%;
		max-width: 300px;
		margin: 1rem 0;
	}

	.progress-bar {
		width: 100%;
		height: 8px;
		background: var(--pico-muted-background-color);
		border-radius: 4px;
		overflow: hidden;
		margin-bottom: 0.5rem;
	}

	.progress-fill {
		height: 100%;
		background: var(--pico-primary-background);
		transition: width 0.3s ease;
	}

	.progress-text {
		font-size: 0.875rem;
		color: var(--pico-color);
		margin: 0;
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
		background: none;
		border: 1px solid var(--pico-muted-border-color);
		color: var(--pico-muted-color);
		padding: 4px 8px;
		font-size: 11px;
		border-radius: 3px;
		cursor: pointer;
	}

	.reset-view-btn:hover {
		background: var(--pico-muted-background-color);
		color: var(--pico-color);
	}

	/* Error state styling */
	.error-content {
		color: var(--pico-del-color);
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

	/* Spinning animation */
	:global(.spin) {
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}
</style>