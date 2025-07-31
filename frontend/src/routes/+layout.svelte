<script lang="ts">
	import '@picocss/pico';
	import { page } from '$app/stores';
</script>

<header class="main-header">
	<nav>
		<ul>
			<li>
				<a href="/" class="contrast">
					<strong>Coin Maker</strong>
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

<style>
	:root {
		--header-bg-color: color-mix(in srgb, var(--pico-primary-background) 20%, var(--pico-background-color));
	}

	header.main-header {
		border-bottom: 1px solid var(--pico-muted-border-color);
		margin-bottom: 0.25rem;
		padding: 0;
		background-color: var(--header-bg-color);
	}
	
	nav {
		padding: 0.375rem 1rem;
		font-size: 0.85rem;
	}
	
	.active {
		color: var(--pico-primary-500) !important;
		font-weight: 600;
	}

	nav a {
		color: var(--pico-color) !important;
		font-size: 0.8rem;
	}

	nav a strong {
		font-size: 0.9rem;
	}

	nav li {
		padding: 0.25rem 0.5rem;
	}
	
	main {
		min-height: calc(100vh - 80px);
		padding: 0 0.5rem;
	}
</style>