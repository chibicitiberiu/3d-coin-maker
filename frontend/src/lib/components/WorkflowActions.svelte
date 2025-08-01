<script lang="ts">
	import { Download, Loader2 } from 'lucide-svelte';
	import { browser } from '$app/environment';
	import { 
		generationState,
		generatedSTLUrl,
		isGenerating as storeIsGenerating,
		generationProgress,
		generationActions
	} from '$lib/stores/generationState';
	import { processedImageBlob } from '$lib/stores/imageProcessingState';
	import { coinParametersState } from '$lib/stores/coinParametersState';
	import { uiActions } from '$lib/stores/uiState';
	import { generationService } from '$lib/services/GenerationService';
	import type { CoinParameters } from '$lib/services/BackendService';

	// Reactive store subscriptions
	$: currentProcessedImageBlob = $processedImageBlob;
	$: currentIsGenerating = $storeIsGenerating;
	$: currentGeneratedSTLUrl = $generatedSTLUrl;
	$: currentGenerationProgress = $generationProgress;

	// Get coin parameters from store
	$: currentCoinParams = {
		shape: $coinParametersState.coinShape,
		diameter: $coinParametersState.coinSize,
		thickness: $coinParametersState.coinThickness,
		reliefDepth: $coinParametersState.reliefDepth,
		scale: $coinParametersState.heightmapScale,
		offsetX: $coinParametersState.offsetX,
		offsetY: $coinParametersState.offsetY,
		rotation: $coinParametersState.rotation
	} satisfies CoinParameters;

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
</script>

<div class="actions">
	<button 
		on:click={generateSTL}
		disabled={!currentProcessedImageBlob || currentIsGenerating}
	>
		{#if currentIsGenerating}
			<Loader2 size={14} class="u-spin" />
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

<style lang="scss">
	@use '$lib/styles/variables' as *;
	@use '$lib/styles/mixins' as *;

	.actions {
		@include flex-gap($spacing-normal);
		flex-wrap: wrap;
	}

	.actions button {
		flex: 1;
		min-width: 7.5rem; // 120px → rem
		@include flex-center;
		gap: $spacing-tight;
		font-size: $font-small;
		padding: $spacing-normal $spacing-large;
	}

</style>