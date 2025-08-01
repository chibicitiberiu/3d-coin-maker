import { backendService, type CoinParameters, type GenerationStatus } from './BackendService';
import { generationActions } from '../stores/generationState';

export interface GenerationProgress {
	step: 'uploading' | 'processing' | 'generating' | 'polling' | 'completed' | 'failed';
	progress: number; // 0-100
	message: string;
	error?: string;
}

export interface GenerationResult {
	success: boolean;
	generationId: string | null;
	stlUrl: string | null;
	error?: string;
}

export type ProgressCallback = (progress: GenerationProgress) => void;

export class GenerationService {
	private abortController: AbortController | null = null;
	private isGenerating = false;

	/**
	 * Check if generation is currently in progress
	 */
	isRunning(): boolean {
		return this.isGenerating;
	}

	/**
	 * Cancel current generation process
	 */
	cancel(): void {
		if (this.abortController) {
			this.abortController.abort();
			this.abortController = null;
		}
		this.isGenerating = false;
		generationActions.setIsGenerating(false);
		backendService.cancelAllRequests();
	}

	/**
	 * Generate STL from processed image blob - orchestrates the entire workflow
	 */
	async generateSTL(
		processedImageBlob: Blob,
		coinParams: CoinParameters,
		onProgress?: ProgressCallback
	): Promise<GenerationResult> {
		if (this.isGenerating) {
			throw new Error('Generation already in progress');
		}

		// Setup cancellation
		this.abortController = new AbortController();
		this.isGenerating = true;
		generationActions.setIsGenerating(true);
		generationActions.resetError();
		generationActions.setGeneratedSTLUrl(null);

		const signal = this.abortController.signal;

		try {
			// Step 1: Upload processed image
			onProgress?.({
				step: 'uploading',
				progress: 5,
				message: 'Uploading processed image...'
			});

			const processedFile = new File([processedImageBlob], 'processed_image.png', {
				type: 'image/png'
			});

			const uploadResult = await backendService.uploadImage(processedFile, { signal });
			const generationId = uploadResult.generation_id;
			
			generationActions.setGenerationId(generationId);

			if (signal.aborted) {
				throw new Error('Generation cancelled');
			}

			// Step 2: Generate STL
			onProgress?.({
				step: 'generating',
				progress: 15,
				message: 'Starting STL generation...'
			});

			const generateResult = await backendService.generateSTL(generationId, coinParams, { signal });
			const taskId = generateResult.task_id;
			
			generationActions.setGenerationTaskId(taskId);

			if (signal.aborted) {
				throw new Error('Generation cancelled');
			}

			// Step 3: Poll for completion
			onProgress?.({
				step: 'polling',
				progress: 20,
				message: 'Processing STL generation...'
			});

			const finalStatus = await this.pollTaskCompletion(
				generationId,
				taskId,
				signal,
				(pollProgress, backendStep) => {
					// Map backend steps to user-friendly messages
					const stepMessages: Record<string, string> = {
						'stl_generation_starting': 'Starting STL generation...',
						'relief_mesh_generation': 'Generating relief mesh from heightmap...',
						'heightmap_preprocessing': 'Preprocessing heightmap...',
						'hmm_mesh_generation': 'Creating 3D mesh with HMM...',
						'mesh_loading': 'Loading generated mesh...',
						'mesh_transformation': 'Applying transformations...',
						'coin_shape_generation': 'Creating coin base shape...',
						'mesh_combination': 'Combining relief with base...',
						'stl_export': 'Exporting STL file...',
						'stl_export_complete': 'STL export complete!',
						'stl_generated': 'STL generation completed!'
					};
					
					const message = stepMessages[backendStep] || 'Processing STL generation...';
					
					onProgress?.({
						step: 'polling',
						progress: pollProgress,
						message: message
					});
				}
			);

			if (signal.aborted) {
				throw new Error('Generation cancelled');
			}

			// Step 4: Get download URL
			onProgress?.({
				step: 'completed',
				progress: 95,
				message: 'Finalizing STL...'
			});

			const timestamp = finalStatus?.stl_timestamp;
			const stlUrl = backendService.getSTLDownloadUrl(generationId, timestamp || Date.now());
			
			generationActions.setGeneratedSTLUrl(stlUrl);

			onProgress?.({
				step: 'completed',
				progress: 100,
				message: 'STL generation completed!'
			});

			return {
				success: true,
				generationId,
				stlUrl
			};

		} catch (error) {
			const errorMessage = error instanceof Error ? error.message : String(error);
			
			generationActions.setStlGenerationError(errorMessage);
			
			onProgress?.({
				step: 'failed',
				progress: 0,
				message: 'STL generation failed',
				error: errorMessage
			});

			return {
				success: false,
				generationId: null,
				stlUrl: null,
				error: errorMessage
			};
		} finally {
			this.isGenerating = false;
			this.abortController = null;
			generationActions.setIsGenerating(false);
			// Clear progress when generation is complete (success or failure)
			setTimeout(() => {
				generationActions.setGenerationProgress(null);
			}, 2000); // Keep progress visible for 2 seconds after completion
		}
	}

	/**
	 * Poll for task completion with progress updates
	 */
	private async pollTaskCompletion(
		generationId: string,
		taskId: string,
		signal: AbortSignal,
		onProgress?: (progress: number, step: string) => void
	): Promise<GenerationStatus> {
		const maxAttempts = 120; // 2 minutes with 1s intervals
		let attempts = 0;

		while (attempts < maxAttempts && !signal.aborted) {
			try {
				const status = await backendService.getGenerationStatus(generationId, taskId, { 
					signal,
					timeout: 5000 // Shorter timeout for polling
				});

				// Use actual progress and step from backend
				const backendProgress = status.progress || 0;
				const backendStep = status.step || 'unknown';
				onProgress?.(backendProgress, backendStep);

				if (status.status === 'SUCCESS') {
					onProgress?.(100, status.step || 'completed');
					return status;
				} else if (status.status === 'FAILURE') {
					const backendError = new Error(status.error || 'STL generation failed');
					backendError.name = 'BackendError';
					throw backendError;
				}

				// Wait 1 second before next poll
				await new Promise(resolve => setTimeout(resolve, 1000));
				attempts++;

			} catch (error) {
				// If this is a backend error (FAILURE status), don't retry
				if (error instanceof Error && error.name === 'BackendError') {
					throw error;
				}
				
				// If signal was aborted, throw cancellation error
				if (signal.aborted) {
					throw new Error('Generation cancelled');
				}
				
				// For other errors (network issues), retry until max attempts
				if (attempts === maxAttempts - 1) {
					throw error;
				}
				
				await new Promise(resolve => setTimeout(resolve, 1000));
				attempts++;
			}
		}

		if (signal.aborted) {
			throw new Error('Generation cancelled');
		}

		throw new Error('STL generation timed out');
	}

	/**
	 * Download STL file with proper error handling
	 */
	async downloadSTL(generationId: string): Promise<void> {
		try {
			const blob = await backendService.downloadSTL(generationId);
			
			// Create download link
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `coin_${generationId}.stl`;
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
			URL.revokeObjectURL(url);
			
		} catch (error) {
			const errorMessage = error instanceof Error ? error.message : 'Unknown error';
			throw new Error(`Error downloading STL: ${errorMessage}`);
		}
	}

	/**
	 * Get generation status for a specific generation ID
	 */
	async getStatus(generationId: string, taskId?: string): Promise<GenerationStatus> {
		return await backendService.getGenerationStatus(generationId, taskId);
	}
}

// Singleton instance
export const generationService = new GenerationService();