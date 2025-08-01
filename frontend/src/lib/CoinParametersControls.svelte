<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	// Props - coin parameters
	export let coinShape: 'circle' | 'square' | 'hexagon' | 'octagon' = 'circle';
	export let coinSize = 30; // diameter in mm
	export let coinThickness = 3; // in mm
	export let reliefDepth = 1; // in mm
	export let expanded = true;

	// Event dispatcher for parameter changes
	const dispatch = createEventDispatcher<{
		parametersChanged: {
			coinShape: typeof coinShape;
			coinSize: number;
			coinThickness: number;
			reliefDepth: number;
		};
	}>();

	// Validate relief depth against thickness
	$: if (reliefDepth >= coinThickness) {
		reliefDepth = Math.max(0.1, coinThickness - 0.1);
	}

	// Debounced dispatch to reduce excessive updates during slider dragging
	let dispatchTimeout: ReturnType<typeof setTimeout>;
	let dragTimeout: ReturnType<typeof setTimeout>;
	let isDragging = false;
	
	// Immediate dispatch for dropdowns and immediate feedback
	function triggerImmediateDispatch() {
		clearTimeout(dispatchTimeout);
		dispatch('parametersChanged', {
			coinShape,
			coinSize,
			coinThickness,
			reliefDepth
		});
	}
	
	// Handle drag start/end for responsive slider feedback
	function handleDragStart() {
		isDragging = true;
		clearTimeout(dragTimeout);
	}
	
	function handleDragEnd() {
		clearTimeout(dragTimeout);
		dragTimeout = setTimeout(() => {
			isDragging = false;
			triggerImmediateDispatch(); // Final update after drag
		}, 50);
	}
	
	// Reactive statement to dispatch changes with debouncing
	$: if (coinShape && typeof coinSize === 'number' && typeof coinThickness === 'number' && typeof reliefDepth === 'number') {
		clearTimeout(dispatchTimeout);
		
		if (isDragging) {
			// During drag: immediate feedback for responsive sliders
			dispatchTimeout = setTimeout(triggerImmediateDispatch, 50);
		} else {
			// Not dragging: normal debounce
			dispatchTimeout = setTimeout(triggerImmediateDispatch, 150);
		}
	}
</script>

<section class="coin-parameters">
	<button 
		type="button"
		class="collapsible-header" 
		aria-expanded={expanded}
		aria-controls="coin-parameters-content"
		on:click={() => expanded = !expanded}
		on:keydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); expanded = !expanded; } }}
	>
		<span class="collapse-icon" class:expanded>▶</span>
		Coin Parameters
	</button>
	<div id="coin-parameters-content" class:u-hidden={!expanded}>
	
	<div class="control-grid">
		<label for="coin-shape">Shape</label>
		<select id="coin-shape" bind:value={coinShape} on:change={triggerImmediateDispatch}>
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
				on:mousedown={(e) => { 
					if (e.button === 1) { coinSize = 30; e.preventDefault(); }
					else { handleDragStart(); }
				}}
				on:mouseup={handleDragEnd}
				on:touchstart={handleDragStart}
				on:touchend={handleDragEnd}
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
				on:mousedown={(e) => { 
					if (e.button === 1) { coinThickness = 3; e.preventDefault(); }
					else { handleDragStart(); }
				}}
				on:mouseup={handleDragEnd}
				on:touchstart={handleDragStart}
				on:touchend={handleDragEnd}
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
				on:mousedown={(e) => { 
					if (e.button === 1) { reliefDepth = 1; e.preventDefault(); }
					else { handleDragStart(); }
				}}
				on:mouseup={handleDragEnd}
				on:touchstart={handleDragStart}
				on:touchend={handleDragEnd}
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

<style lang="scss">
	@use '$lib/styles/variables' as *;
	@use '$lib/styles/mixins' as *;

	.control-grid {
		@include control-grid;
	}

	.range-control {
		@include range-control;
	}

	.number-input {
		@include control-input;
	}

	.control-grid label {
		display: block;
		margin: 0;
		font-size: $font-small;
		color: var(--pico-color);
		align-self: baseline;
		padding-top: $spacing-tight;
	}

	.control-note {
		@include control-note;
	}

	select {
		font-size: $font-small;
		padding: $spacing-tight 0.4rem; // Keep 0.4rem for PicoCSS consistency
		margin: 0;
	}


	// Collapsible sections - use our mixin
	.collapsible-header {
		@include collapsible-header;
		
		&:focus {
			@include focus-outline;
		}
	}

	.collapse-icon {
		@include collapse-icon;
	}

	// Custom range styling - use our global mixin
	input[type="range"] {
		@include custom-range-slider;
	}
</style>