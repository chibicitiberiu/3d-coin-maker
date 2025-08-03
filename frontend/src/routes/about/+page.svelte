<script lang="ts">
	import { Mail, Github, Globe } from 'lucide-svelte';
</script>

<svelte:head>
	<title>About - 3D Coin Maker</title>
</svelte:head>

<article>
	<header>
		<h1>About 3D Coin Maker</h1>
		<p>Transform your images into 3D printable coins</p>
	</header>

	<section>
		<h2>What is 3D Coin Maker?</h2>
		<p>
			3D Coin Maker is a self-hostable web application that converts your images into 3D printable coin STL files. 
			Upload an image, adjust the processing parameters, and generate a custom coin ready for 3D printing.
		</p>

		<h3>Features</h3>
		<ul>
			<li>Client-side image processing with WASM</li>
			<li>Multiple coin shapes (Circle, Square, Hexagon, Octagon)</li>
			<li>Adjustable coin dimensions and relief depth</li>
			<li>Real-time preview of processed images</li>
			<li>3D STL viewer with interactive controls</li>
			<li>No data retention - all processing is temporary</li>
		</ul>

		<h3>Supported Image Formats</h3>
		<p>PNG, JPEG, GIF, BMP, TIFF (up to 50MB)</p>
	</section>

	<section>
		<h2>Technology Stack</h2>
		<ul>
			<li><strong>Frontend:</strong> SvelteKit + TypeScript</li>
			<li><strong>Backend:</strong> Django + Django REST Framework</li>
			<li><strong>Image Processing:</strong> Photon WASM</li>
			<li><strong>3D Generation:</strong> HMM + Manifold3D</li>
			<li><strong>Deployment:</strong> Docker Compose</li>
		</ul>
	</section>

	<section>
		<h2>Contact & Links</h2>
		<div class="grid">
			<div>
				<h4><Mail size={20} class="icon" />Contact</h4>
				<p>For questions or support, please reach out via the project repository.</p>
			</div>
			<div>
				<h4><Github size={20} class="icon" />Source Code</h4>
				<p>This project is open source and available on GitHub.</p>
			</div>
			<div>
				<h4><Globe size={20} class="icon" />Self-Hosting</h4>
				<p>Deploy your own instance with Docker Compose for private use.</p>
			</div>
		</div>
	</section>

	<footer>
		<small>
			Built with care using modern web technologies. 
			<a href="/" class="secondary">← Back to Generator</a>
		</small>
	</footer>
</article>

<style lang="scss">
	@use '$lib/styles/variables' as *;
	@use '$lib/styles/mixins' as *;

	article {
		max-width: 50rem; // 800px → rem
		margin: 0 auto;
	}
	
	section {
		margin: $spacing-xxl 0; // 2rem → design system variable
	}
	
	.grid {
		margin-top: $spacing-large; // 1rem → design system variable
	}
	
	h4 {
		margin-bottom: $spacing-normal; // 0.5rem → design system variable
		@include flex-align; // display flex + align-items center
	}
	
	footer {
		margin-top: $spacing-xxl; // 2rem → design system variable
		padding-top: $spacing-xxl; // 2rem → design system variable
		border-top: $border-thin solid var(--pico-muted-border-color);
		text-align: center;
	}
	
	.icon {
		display: inline;
		margin-inline-end: $spacing-normal; // Logical property for better i18n
	}
</style>