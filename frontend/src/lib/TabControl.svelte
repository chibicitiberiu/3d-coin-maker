<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	// Props
	export let activeTab: string;
	export let tabs: Array<{ id: string; label: string; disabled?: boolean }>;

	// Event dispatcher
	const dispatch = createEventDispatcher<{
		tabChanged: { tabId: string };
	}>();

	function handleTabClick(tabId: string, disabled?: boolean) {
		if (disabled) return;
		dispatch('tabChanged', { tabId });
	}
</script>

<nav class="tabs">
	{#each tabs as tab}
		<button 
			class="tab" 
			class:active={activeTab === tab.id}
			class:disabled={tab.disabled}
			disabled={tab.disabled}
			on:click={() => handleTabClick(tab.id, tab.disabled)}
			aria-selected={activeTab === tab.id}
			role="tab"
		>
			{tab.label}
		</button>
	{/each}
</nav>

<style lang="scss">
	@use '$lib/styles/variables' as *;
	@use '$lib/styles/mixins' as *;

	.tabs {
		display: flex;
		background: var(--pico-background-color);
		border-bottom: $border-thin solid var(--pico-muted-border-color);
	}

	.tab {
		flex: 1;
		background: transparent !important;
		border: none;
		padding: $spacing-normal;
		cursor: pointer;
		transition: all $transition-normal $easing-standard;
		border-bottom: 3px solid transparent;
		font-size: $font-small;
		color: var(--pico-color) !important;
		--pico-primary-inverse: var(--pico-color);
	}

	.tab:hover:not(.disabled) {
		background: var(--pico-muted-background-color) !important;
		color: var(--pico-color) !important;
		--pico-primary-inverse: var(--pico-color);
	}

	.tab.disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	// Force override Pico CSS button styling for tabs
	.tabs button.tab {
		color: var(--pico-color) !important;
		background-color: transparent !important;
		border-color: transparent !important;
	}

	.tabs button.tab:hover:not(.disabled) {
		color: var(--pico-color) !important;
		background-color: var(--pico-muted-background-color) !important;
		border-color: transparent !important;
	}

	.tabs button.tab.active {
		color: var(--pico-color) !important;
		background-color: var(--pico-card-background-color) !important;
		border-color: transparent !important;
	}

	.tab.active {
		background: var(--pico-card-background-color) !important;
		border-bottom-color: var(--pico-primary-500);
		font-weight: $weight-semibold;
		color: var(--pico-color) !important;
		--pico-primary-inverse: var(--pico-color);
	}
</style>