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

<style>
	/* Main App Layout */
	.app-layout {
		display: grid;
		grid-template-columns: 30% 70%;
		gap: 1rem;
		height: 100vh;
		padding: 1rem;
		box-sizing: border-box;
	}

	/* Left Panel - Controls */
	.controls-panel {
		display: flex;
		flex-direction: column;
		background: var(--pico-card-background-color);
		border: 1px solid var(--pico-card-border-color);
		border-radius: var(--pico-border-radius);
		overflow: hidden;
		height: fit-content;
		max-height: calc(100vh - 2rem);
	}

	.controls-header {
		background: var(--pico-primary-background);
		color: var(--pico-primary-inverse);
		padding: 0.75rem 1rem;
		border-bottom: 1px solid var(--pico-card-border-color);
	}

	.controls-header h2 {
		margin: 0;
		font-size: 1rem;
		font-weight: 600;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.controls-content {
		flex: 1;
		overflow-y: auto;
		padding: 0;
	}

	.controls-footer {
		border-top: 1px solid var(--pico-card-border-color);
		background: var(--pico-card-background-color);
		padding: 1rem;
	}

	/* Right Panel - Viewer */
	.viewer-panel {
		display: flex;
		flex-direction: column;
		background: var(--pico-card-background-color);
		border: 1px solid var(--pico-card-border-color);
		border-radius: var(--pico-border-radius);
		overflow: hidden;
		height: calc(100vh - 2rem);
	}

	/* Mobile Responsiveness */
	@media (max-width: 768px) {
		.app-layout {
			grid-template-columns: 1fr;
			grid-template-rows: auto 1fr;
			height: auto;
			gap: 0.5rem;
		}

		.controls-panel {
			height: auto;
			max-height: none;
			padding: 0.5rem;
			font-size: 0.8rem;
		}

		.viewer-panel {
			min-height: 400px;
		}
	}
</style>