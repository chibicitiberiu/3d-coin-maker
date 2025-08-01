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
		width: $number-input-width;
		padding: $spacing-micro $spacing-tight;
		font-size: $font-small;
		margin: 0;
		align-self: baseline;
		margin-top: $spacing-tight;
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
		grid-column: 1 / -1;
		margin-top: -$spacing-tight;
		margin-bottom: $spacing-tight;
		margin-left: $spacing-tight; // Match control-grid left margin
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


	// Hidden content utility
	.hidden {
		display: none;
	}

	// Collapsible sections - use our mixin
	.collapsible-header {
		@include collapsible-header;
		
		&:focus {
			@include focus-outline;
		}
	}

	.collapse-icon {
		font-size: $font-micro;
		transition: transform $transition-normal $easing-standard;
		display: inline-block;
		width: 0.75rem; // 12px → rem
		
		&.expanded {
			transform: rotate(90deg);
		}
	}

	// Custom range styling - use our global mixin
	input[type="range"] {
		@include custom-range-slider;
	}
</style>