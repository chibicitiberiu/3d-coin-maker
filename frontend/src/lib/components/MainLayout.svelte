<script lang="ts">
	import { Settings } from 'lucide-svelte';
</script>

<div class="app-layout">
	<!-- Left Panel - Controls (30%) -->
	<aside class="controls-panel">
		<header class="controls-header">
			<h2><Settings size={18} /> Controls</h2>
		</header>
		<div class="controls-content">
			<slot name="controls" />
		</div>
		<footer class="controls-footer">
			<slot name="actions" />
		</footer>
	</aside>

	<!-- Right Panel - Viewer (70%) -->
	<main class="viewer-panel">
		<slot name="viewer" />
	</main>
</div>

<style lang="scss">
	@use '$lib/styles/variables' as *;
	@use '$lib/styles/mixins' as *;

	// Main App Layout
	.app-layout {
		display: grid;
		grid-template-columns: $app-grid-columns; // 30% 70%
		gap: $spacing-large;
		height: var(--content-height); // Subtract header height + margin
		padding: $spacing-large;
		box-sizing: border-box;
	}

	// Left Panel - Controls
	.controls-panel {
		@include flex-column;
		background: var(--pico-card-background-color);
		border: $border-thin solid var(--pico-card-border-color);
		border-radius: var(--pico-border-radius);
		overflow: hidden;
		height: fit-content;
		max-height: var(--panel-max-height); // Header + padding + margin
	}

	.controls-header {
		background: var(--pico-primary-background);
		color: var(--pico-primary-inverse);
		padding: $spacing-medium $spacing-large;
		border-bottom: $border-thin solid var(--pico-card-border-color);

		h2 {
			margin: 0;
			font-size: $font-normal;
			font-weight: $weight-semibold;
			@include flex-gap($spacing-normal);
		}
	}

	.controls-content {
		flex: 1;
		overflow-y: auto;
		padding: 0 $spacing-normal; // Smaller horizontal margins for controls
	}

	.controls-footer {
		border-top: $border-thin solid var(--pico-card-border-color);
		background: var(--pico-card-background-color);
		padding: $spacing-large;
	}

	// Right Panel - Viewer
	.viewer-panel {
		@include flex-column;
		background: var(--pico-card-background-color);
		border: $border-thin solid var(--pico-card-border-color);
		border-radius: var(--pico-border-radius);
		overflow: hidden;
		height: var(--panel-max-height); // Header + padding + margin
	}

	// Mobile Responsiveness
	@include mobile-only {
		.app-layout {
			grid-template-columns: 1fr;
			grid-template-rows: auto 1fr;
			height: auto;
			gap: $spacing-normal;
		}

		.controls-panel {
			height: auto;
			max-height: none;
			padding: $spacing-normal;
			font-size: $font-small;
		}

		.viewer-panel {
			min-height: 25rem; // 400px → rem
		}
	}
</style>