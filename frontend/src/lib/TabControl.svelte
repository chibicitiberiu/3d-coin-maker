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
		@include button-reset;
		flex: 1;
		padding: $spacing-normal;
		font-size: $font-small;
		color: var(--pico-muted-color); // Use muted color for better contrast
		background: var(--pico-muted-background-color);
		border-bottom: 3px solid transparent;
		transition: all $transition-normal $easing-standard;
		
		&:hover:not(.disabled) {
			background: var(--pico-card-background-color);
			color: var(--pico-primary);
		}
		
		&.active {
			background: var(--pico-card-background-color);
			border-bottom-color: var(--pico-primary);
			font-weight: $weight-semibold;
			color: var(--pico-primary);
		}
		
		&.disabled {
			opacity: 0.5;
			cursor: not-allowed;
		}
		
		&:focus-visible {
			@include focus-outline;
		}
		
		@include high-contrast-support;
	}
</style>