<script lang="ts">
	import { Upload, Loader2, Image } from 'lucide-svelte';
	import { browser } from '$app/environment';
	import { createEventDispatcher } from 'svelte';

	// Props
	export let disabled = false;

	// State
	let uploadedFile: File | null = null;
	let uploadedImageUrl: string | null = null;
	let isUploading = false;
	let fileInput: HTMLInputElement;
	let isDragOver = false;

	// Event dispatcher for parent communication
	const dispatch = createEventDispatcher<{
		fileProcessed: { file: File; imageUrl: string };
		error: { message: string };
	}>();

	// Constants
	const ACCEPTED_TYPES = ['image/png', 'image/jpeg', 'image/gif', 'image/bmp', 'image/tiff'];
	const MAX_SIZE = 50 * 1024 * 1024; // 50MB

	function handleFileSelect(event: Event) {
		const target = event.target as HTMLInputElement;
		if (target.files && target.files[0]) {
			processFile(target.files[0]);
		}
	}

	function handleDrop(event: DragEvent) {
		event.preventDefault();
		if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
			processFile(event.dataTransfer.files[0]);
		}
	}

	function handleDragOver(event: DragEvent) {
		event.preventDefault();
		isDragOver = true;
	}

	function handleDragLeave(event: DragEvent) {
		event.preventDefault();
		isDragOver = false;
	}

	async function processFile(file: File) {
		if (!ACCEPTED_TYPES.includes(file.type)) {
			dispatch('error', { message: 'Please upload a valid image file (PNG, JPEG, GIF, BMP, TIFF)' });
			return;
		}

		if (file.size > MAX_SIZE) {
			dispatch('error', { message: 'File size must be less than 50MB' });
			return;
		}

		console.log('processFile: Starting to process file', file.name, file.size);
		isUploading = true;
		
		try {
			// Create object URL for preview
			if (uploadedImageUrl) {
				URL.revokeObjectURL(uploadedImageUrl);
			}
			uploadedImageUrl = URL.createObjectURL(file);
			uploadedFile = file;
			console.log('processFile: Created image URL', uploadedImageUrl);
			
			console.log('processFile: Image uploaded successfully');
			
			// Dispatch success event
			dispatch('fileProcessed', { file, imageUrl: uploadedImageUrl });
			
		} catch (error) {
			dispatch('error', { 
				message: 'Error loading file: ' + (error instanceof Error ? error.message : 'Unknown error')
			});
			console.error(error);
		} finally {
			isUploading = false;
		}
	}

	function triggerFileSelect() {
		fileInput.click();
	}

	// Export file info for parent access
	export function getFileInfo() {
		return { uploadedFile, uploadedImageUrl };
	}

	// Reset function for parent to call
	export function reset() {
		if (uploadedImageUrl) {
			URL.revokeObjectURL(uploadedImageUrl);
		}
		uploadedFile = null;
		uploadedImageUrl = null;
		isUploading = false;
	}
</script>

<section 
	class="upload-section"
	class:drag-over={isDragOver}
	role="application"
	aria-label="File drop zone"
	on:drop={(e) => { handleDrop(e); isDragOver = false; }}
	on:dragover={handleDragOver}
	on:dragleave={handleDragLeave}
>
	<div class="control-grid">
		<label><Upload size={14} /> Upload Image</label>
		<div class="upload-control">
			<input
				type="file"
				bind:this={fileInput}
				on:change={handleFileSelect}
				accept=".png,.jpg,.jpeg,.gif,.bmp,.tiff"
				style="display: none;"
			/>
			<button 
				class="upload-btn secondary"
				on:click={triggerFileSelect}
				disabled={isUploading || disabled}
			>
				{#if isUploading}
					<Loader2 size={12} class="spin" />
				{:else}
					Browse
				{/if}
			</button>
			{#if uploadedFile}
				<div class="upload-status">
					<Image size={10} />
					<span>{uploadedFile.name} ({Math.round(uploadedFile.size / 1024)} KB)</span>
				</div>
			{/if}
		</div>
	</div>
</section>

<style>
	.upload-section {
		transition: background-color 0.2s;
	}

	.control-grid {
		display: grid;
		grid-template-columns: 1fr 1.5fr;
		gap: 0.5rem;
		align-items: baseline;
		margin-bottom: 0.4rem;
	}

	.upload-control {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.upload-btn {
		padding: 0.2rem 0.4rem;
		font-size: 10pt;
		min-width: 55px;
		margin: 0;
	}

	.upload-status {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		font-size: 9pt;
		color: var(--pico-muted-color);
		flex: 1;
		min-width: 0;
	}

	.upload-status span {
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	/* Drop zone styling */
	.upload-section.drag-over {
		background-color: var(--pico-primary-background);
	}

	.control-grid label {
		display: block;
		margin: 0;
		font-size: 11pt;
		color: var(--pico-color);
		align-self: baseline;
		padding-top: 0.25rem;
	}
</style>