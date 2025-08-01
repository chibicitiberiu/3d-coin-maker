<script lang="ts">
	import '$lib/styles/index.scss';
	import { page } from '$app/stores';
</script>

<header class="main-header">
	<nav>
		<ul>
			<li>
				<a href="/" class="contrast">
					<strong>3D Coin Maker</strong>
				</a>
			</li>
		</ul>
		<ul>
			<li><a href="/" class:active={$page.url.pathname === '/'}>Generator</a></li>
			<li><a href="/about" class:active={$page.url.pathname === '/about'}>About</a></li>
			<li>
				<a href="https://github.com" target="_blank" rel="noopener noreferrer">
					GitHub
				</a>
			</li>
		</ul>
	</nav>
</header>

<main class="container-fluid">
	<slot />
</main>

<style lang="scss">
	@use '$lib/styles/variables' as *;
	@use '$lib/styles/mixins' as *;

	:root {
		--header-bg-color: color-mix(in srgb, var(--pico-primary-background) 20%, var(--pico-background-color));
		--header-height: 3.5rem; // Approximate header height
		
		// Layout height calculations
		--content-height: calc(100vh - var(--header-height) - #{$spacing-tight});
		--panel-max-height: calc(100vh - var(--header-height) - #{$spacing-xxl} - #{$spacing-tight});
	}

	header.main-header {
		border-bottom: $border-thin solid var(--pico-muted-border-color);
		margin-bottom: $spacing-tight;
		padding: 0;
		background-color: var(--header-bg-color);
	}
	
	nav {
		padding: $spacing-small $spacing-large;
		font-size: 11pt; // Standardized to pt
	}
	
	.active {
		color: var(--pico-primary-500) !important;
		font-weight: $weight-semibold;
	}

	nav a {
		color: var(--pico-color) !important;
		font-size: $font-small;
	}

	nav a strong {
		font-size: $font-body;
	}

	nav li {
		padding: $spacing-tight $spacing-normal;
	}
	
	main {
		min-height: var(--content-height); // Full height minus header and margin
		padding: 0 $spacing-normal;
	}
</style>