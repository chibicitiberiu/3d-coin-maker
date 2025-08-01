<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	// Props - image processing parameters
	export let grayscaleMethod: 'average' | 'luminance' | 'red' | 'green' | 'blue' | 'custom' = 'luminance';
	export let brightness = 0;
	export let contrast = 0;
	export let gamma = 1.0;
	export let invertColors = false;
	export let expanded = true;

	// Event dispatcher for parameter changes
	const dispatch = createEventDispatcher<{
		parametersChanged: {
			grayscaleMethod: typeof grayscaleMethod;
			brightness: number;
			contrast: number;
			gamma: number;
			invertColors: boolean;
			isDragFeedback?: boolean; // Flag to indicate this is drag feedback processing
		};
		cancelProcessing: void;
	}>();

	// Track dragging state for adaptive processing
	let isDragging = false;
	let dragTimeout: ReturnType<typeof setTimeout>;
	let dispatchTimeout: ReturnType<typeof setTimeout>;
	let dragFeedbackTimeout: ReturnType<typeof setTimeout>;
	
	// Handle drag start/end to optimize performance
	function handleDragStart() {
		isDragging = true;
		clearTimeout(dragTimeout);
		clearTimeout(dragFeedbackTimeout);
	}
	
	function handleDragEnd() {
		clearTimeout(dragTimeout);
		clearTimeout(dragFeedbackTimeout);
		dragTimeout = setTimeout(() => {
			isDragging = false;
			// Cancel any pending processing and trigger final update
			dispatch('cancelProcessing'); // Signal to cancel all pending work
			triggerDispatch(false); // Process final result with higher quality
		}, 50); // Small delay to ensure drag has fully ended
	}
	
	function triggerDispatch(isDragFeedback = false) {
		dispatch('parametersChanged', {
			grayscaleMethod,
			brightness,
			contrast,
			gamma,
			invertColors,
			isDragFeedback
		});
	}
	
	// Reactive statement to dispatch changes with different strategies for dragging vs not dragging
	$: if (typeof brightness === 'number' && typeof contrast === 'number' && typeof gamma === 'number') {
		clearTimeout(dispatchTimeout);
		clearTimeout(dragFeedbackTimeout);
		
		if (isDragging) {
			// During drag: immediate fast feedback with low-res processing
			clearTimeout(dragFeedbackTimeout);
			dragFeedbackTimeout = setTimeout(() => {
				triggerDispatch(true); // isDragFeedback = true - uses fast low-res processing
			}, 50); // Very fast response for immediate feedback
		} else {
			// Not dragging: use normal debouncing for final quality
			dispatchTimeout = setTimeout(() => {
				triggerDispatch(false); // isDragFeedback = false - uses full-res processing
			}, 500); // Longer debounce for final quality
		}
	}
</script>

<section class="image-processing">
	<button 
		type="button"
		class="collapsible-header" 
		aria-expanded={expanded}
		aria-controls="image-processing-content"
		on:click={() => expanded = !expanded}
		on:keydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); expanded = !expanded; } }}
	>
		<span class="collapse-icon" class:expanded>▶</span>
		Image Processing
	</button>
	<div id="image-processing-content" class:hidden={!expanded}>
	
	<div class="control-grid">
		<label for="grayscale-method">Grayscale Method</label>
		<select id="grayscale-method" bind:value={grayscaleMethod} on:change={() => triggerDispatch(true)}>
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
				on:mousedown={(e) => { 
					if (e.button === 1) { brightness = 0; e.preventDefault(); }
					else { handleDragStart(); }
				}}
				on:mouseup={handleDragEnd}
				on:touchstart={handleDragStart}
				on:touchend={handleDragEnd}
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
				on:mousedown={(e) => { 
					if (e.button === 1) { contrast = 0; e.preventDefault(); }
					else { handleDragStart(); }
				}}
				on:mouseup={handleDragEnd}
				on:touchstart={handleDragStart}
				on:touchend={handleDragEnd}
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
				on:mousedown={(e) => { 
					if (e.button === 1) { gamma = 1.0; e.preventDefault(); }
					else { handleDragStart(); }
				}}
				on:mouseup={handleDragEnd}
				on:touchstart={handleDragStart}
				on:touchend={handleDragEnd}
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
			on:change={() => triggerDispatch(true)}
		/>
	</div>
	</div>
</section>

<style>
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

	.number-input {
		width: 60px;
		padding: 0.125rem 0.25rem;
		font-size: 11pt;
		margin: 0;
		align-self: baseline;
		margin-top: 0.25rem;
	}

	.control-grid label {
		display: block;
		margin: 0;
		font-size: 11pt;
		color: var(--pico-color);
		align-self: baseline;
		padding-top: 0.25rem;
	}

	select {
		font-size: 11pt;
		padding: 0.25rem 0.4rem;
		margin: 0;
	}

	input[type="checkbox"] {
		margin: 0;
		justify-self: start;
		align-self: center;
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
	input[type="range"] {
		-webkit-appearance: none;
		appearance: none;
		height: 4px;
		background: var(--pico-muted-border-color);
		border-radius: 2px;
		outline: none;
	}

	input[type="range"]::-webkit-slider-thumb {
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

	input[type="range"]::-moz-range-thumb {
		width: 14px;
		height: 14px;
		border-radius: 50%;
		background: var(--pico-primary);
		cursor: pointer;
		border: 2px solid var(--pico-background-color);
		box-shadow: 0 0 0 1px var(--pico-muted-border-color);
	}

	input[type="range"]::-moz-range-track {
		height: 4px;
		background: var(--pico-muted-border-color);
		border-radius: 2px;
		border: none;
	}
</style>