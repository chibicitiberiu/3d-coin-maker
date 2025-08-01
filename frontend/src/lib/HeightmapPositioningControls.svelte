<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	// Props - heightmap positioning parameters
	export let heightmapScale = 100; // percentage
	export let offsetX = 0; // percentage of coin size
	export let offsetY = 0; // percentage of coin size
	export let rotation = 0; // degrees
	export let expanded = true;

	// Dynamic offset range based on image scale
	// To move image completely outside coin: need coin_radius + image_radius
	// coin_radius = 50%, image_radius = (heightmapScale / 2)%
	$: offsetRange = Math.ceil(50 + (heightmapScale / 2));

	// Event dispatcher for parameter changes
	const dispatch = createEventDispatcher<{
		parametersChanged: {
			heightmapScale: number;
			offsetX: number;
			offsetY: number;
			rotation: number;
		};
	}>();

	// Simple debounced dispatch for parameter changes
	let dispatchTimeout: ReturnType<typeof setTimeout>;
	
	function triggerDispatch() {
		clearTimeout(dispatchTimeout);
		dispatchTimeout = setTimeout(() => {
			dispatch('parametersChanged', {
				heightmapScale,
				offsetX,
				offsetY,
				rotation
			});
		}, 100); // Short debounce for responsive canvas updates
	}

	// Reactive statement to dispatch changes when parameters change
	$: if (typeof heightmapScale === 'number' && typeof offsetX === 'number' && typeof offsetY === 'number' && typeof rotation === 'number') {
		triggerDispatch();
	}
</script>

<section class="positioning">
	<button 
		type="button"
		class="collapsible-header" 
		aria-expanded={expanded}
		aria-controls="heightmap-positioning-content"
		on:click={() => expanded = !expanded}
		on:keydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); expanded = !expanded; } }}
	>
		<span class="collapse-icon" class:expanded>▶</span>
		Heightmap Positioning
	</button>
	<div id="heightmap-positioning-content" class:hidden={!expanded}>
	
	<div class="control-grid">
		<label for="heightmap-scale">Scale (%)</label>
		<div class="range-control">
			<input 
				type="range" 
				id="heightmap-scale"
				min="10" 
				max="500" 
				bind:value={heightmapScale}
				on:mousedown={(e) => { 
					if (e.button === 1) { heightmapScale = 100; e.preventDefault(); }
				}}
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
				on:mousedown={(e) => { 
					if (e.button === 1) { offsetX = 0; e.preventDefault(); }
				}}
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
				on:mousedown={(e) => { 
					if (e.button === 1) { offsetY = 0; e.preventDefault(); }
				}}
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
				on:mousedown={(e) => { 
					if (e.button === 1) { rotation = 0; e.preventDefault(); }
				}}
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