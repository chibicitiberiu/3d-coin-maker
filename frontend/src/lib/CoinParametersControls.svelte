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
	<div id="coin-parameters-content" class:hidden={!expanded}>
	
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

	.control-note {
		grid-column: 1 / -1;
		margin-top: -0.25rem;
		margin-bottom: 0.25rem;
	}

	select {
		font-size: 11pt;
		padding: 0.25rem 0.4rem;
		margin: 0;
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