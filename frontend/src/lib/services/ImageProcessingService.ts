import { browser } from '$app/environment';
import { processImage, imageDataToBlob, imageDataFromImageElement, type ImageProcessingParams } from '../imageProcessor';
import { imageProcessingActions, type ImageProcessingParams as StoreImageProcessingParams } from '../stores/imageProcessingState';
import { imageProcessingWorkerService } from './ImageProcessingWorkerService';
import { DragFeedbackController } from './DragFeedbackController';

export interface ProcessingResult {
	success: boolean;
	imageData: ImageData | null;
	blob: Blob | null;
	error?: string;
}

export type ProcessingProgressCallback = (progress: {
	step: 'loading' | 'processing' | 'converting' | 'completed';
	progress: number; // 0-100
	message: string;
}) => void;

export class ImageProcessingService {
	private processingTimeout: ReturnType<typeof setTimeout> | null = null;
	private isProcessing = false;
	private abortController: AbortController | null = null;
	private lastParams: string = '';
	private dragFeedbackController: DragFeedbackController;

	constructor() {
		// Initialize with CPU core count or fallback to 2 workers (only in browser)
		const maxWorkers = browser && navigator.hardwareConcurrency 
			? Math.min(navigator.hardwareConcurrency, 4) 
			: 2;
		this.dragFeedbackController = new DragFeedbackController(maxWorkers);
	}

	/**
	 * Check if processing is currently in progress
	 */
	isRunning(): boolean {
		return this.isProcessing;
	}

	/**
	 * Cancel current processing
	 */
	cancel(): void {
		console.log('ImageProcessingService: Canceling all processing');
		
		if (this.processingTimeout) {
			clearTimeout(this.processingTimeout);
			this.processingTimeout = null;
		}
		
		if (this.abortController) {
			this.abortController.abort();
			this.abortController = null;
		}
		
		// Cancel drag feedback processing
		this.dragFeedbackController.cancelAllRequests();
		
		// Cancel any worker processing
		imageProcessingWorkerService.cancelAllRequests();
		
		this.isProcessing = false;
		imageProcessingActions.setIsProcessing(false);
	}

	/**
	 * Process image with debouncing - prevents excessive processing on rapid parameter changes
	 */
	processImageDebounced(
		imageUrl: string,
		params: StoreImageProcessingParams,
		debounceMs: number = 300,
		onProgress?: ProcessingProgressCallback
	): Promise<ProcessingResult> {
		// Cancel any existing processing
		this.cancel();

		// Create a string representation of params for comparison
		const paramsString = JSON.stringify(params);
		
		// If parameters haven't changed, don't reprocess
		if (paramsString === this.lastParams && !this.isProcessing) {
			return Promise.resolve({
				success: true,
				imageData: null,
				blob: null
			});
		}

		return new Promise((resolve) => {
			this.processingTimeout = setTimeout(async () => {
				this.lastParams = paramsString;
				const result = await this.processImage(imageUrl, params, onProgress);
				resolve(result);
			}, debounceMs);
		});
	}

	/**
	 * Process image immediately without debouncing
	 */
	async processImage(
		imageUrl: string,
		params: StoreImageProcessingParams,
		onProgress?: ProcessingProgressCallback,
		quality: 'preview' | 'final' = 'final'
	): Promise<ProcessingResult> {
		if (!browser) {
			return { success: false, imageData: null, blob: null, error: 'Not running in browser' };
		}

		if (this.isProcessing) {
			// If already processing, cancel and start new one
			this.cancel();
		}

		this.isProcessing = true;
		this.abortController = new AbortController();
		imageProcessingActions.setIsProcessing(true);

		const signal = this.abortController.signal;

		try {
			const isPreview = quality === 'preview';
			const qualityLabel = isPreview ? 'preview' : 'final';
			
			onProgress?.({
				step: 'loading',
				progress: 10,
				message: `Loading image for ${qualityLabel} processing...`
			});

			// Create temporary image element for processing
			const imageElement = await this.loadImage(imageUrl, signal);
			
			if (signal.aborted) {
				throw new Error('Processing cancelled');
			}

			onProgress?.({
				step: 'processing',
				progress: 30,
				message: `Processing ${qualityLabel} image...`
			});

			// Get original dimensions
			const originalWidth = imageElement.naturalWidth;
			const originalHeight = imageElement.naturalHeight;
			
			let processedImageData: ImageData;
			
			if (isPreview) {
				// For preview: downscale for speed, then process, then upscale back
				const maxDimension = 400;
				const scaleFactor = Math.min(1, maxDimension / Math.max(originalWidth, originalHeight));
				const lowResWidth = Math.floor(originalWidth * scaleFactor);
				const lowResHeight = Math.floor(originalHeight * scaleFactor);

				console.log(`Preview processing: ${originalWidth}x${originalHeight} -> ${lowResWidth}x${lowResHeight} (${scaleFactor.toFixed(2)}x)`);

				// Create low-res version
				const lowResCanvas = document.createElement('canvas');
				lowResCanvas.width = lowResWidth;
				lowResCanvas.height = lowResHeight;
				const lowResCtx = lowResCanvas.getContext('2d')!;
				lowResCtx.imageSmoothingEnabled = true;
				lowResCtx.imageSmoothingQuality = 'high';
				lowResCtx.drawImage(imageElement, 0, 0, lowResWidth, lowResHeight);
				
				const lowResImageData = lowResCtx.getImageData(0, 0, lowResWidth, lowResHeight);
				
				// Process using worker (same pipeline as final)
				imageProcessingWorkerService.cancelAllRequests();
				
				const processorParams: ImageProcessingParams = {
					grayscaleMethod: params.grayscaleMethod,
					brightness: params.brightness,
					contrast: params.contrast,
					gamma: params.gamma,
					invertColors: params.invertColors
				};

				const workerResult = await imageProcessingWorkerService.processImage(
					lowResImageData,
					processorParams,
					(progress) => {
						onProgress?.({
							step: progress.step as 'loading' | 'processing' | 'converting' | 'completed',
							progress: progress.progress,
							message: progress.message
						});
					}
				);
				
				if (!workerResult.success || !workerResult.imageData) {
					throw new Error(workerResult.error || 'Failed to process preview image');
				}
				
				// Upscale back to original size
				const fullResCanvas = document.createElement('canvas');
				fullResCanvas.width = originalWidth;
				fullResCanvas.height = originalHeight;
				const fullResCtx = fullResCanvas.getContext('2d')!;

				const tempCanvas = document.createElement('canvas');
				tempCanvas.width = lowResWidth;
				tempCanvas.height = lowResHeight;
				const tempCtx = tempCanvas.getContext('2d')!;
				tempCtx.putImageData(workerResult.imageData, 0, 0);

				fullResCtx.imageSmoothingEnabled = true;
				fullResCtx.imageSmoothingQuality = 'high';
				fullResCtx.drawImage(tempCanvas, 0, 0, originalWidth, originalHeight);

				processedImageData = fullResCtx.getImageData(0, 0, originalWidth, originalHeight);
			} else {
				// For final: full resolution processing
				const processorParams: ImageProcessingParams = {
					grayscaleMethod: params.grayscaleMethod,
					brightness: params.brightness,
					contrast: params.contrast,
					gamma: params.gamma,
					invertColors: params.invertColors
				};

				// Cancel any existing processing to ensure only the latest request is processed
				imageProcessingWorkerService.cancelAllRequests();
				
				// Get ImageData from image element for worker processing
				const inputImageData = imageDataFromImageElement(imageElement);
				
				// Process image using Web Worker for non-blocking processing
				const workerResult = await imageProcessingWorkerService.processImage(
					inputImageData,
					processorParams,
					(progress) => {
						onProgress?.({
							step: progress.step as 'loading' | 'processing' | 'converting' | 'completed',
							progress: progress.progress,
							message: progress.message
						});
					}
				);
				
				if (!workerResult.success || !workerResult.imageData) {
					// Fallback to main thread processing if worker fails
					console.warn('Worker processing failed, falling back to main thread:', workerResult.error);
					const imageData = await processImage(imageElement, processorParams);
					
					if (!imageData) {
						throw new Error('Failed to process image');
					}
					
					processedImageData = imageData;
				} else {
					processedImageData = workerResult.imageData;
				}
			}

			if (signal.aborted) {
				throw new Error('Processing cancelled');
			}

			// For final processing, convert to blob; for preview, skip blob generation for speed
			let blob: Blob | null = null;
			if (!isPreview) {
				onProgress?.({
					step: 'converting',
					progress: 70,
					message: 'Converting to blob...'
				});

				blob = await imageDataToBlob(processedImageData);

				if (signal.aborted) {
					throw new Error('Processing cancelled');
				}
			}

			onProgress?.({
				step: 'completed',
				progress: 100,
				message: `${qualityLabel} processing completed!`
			});

			// Update store with results
			imageProcessingActions.setProcessedImageData(processedImageData);
			if (blob) {
				imageProcessingActions.setProcessedImageBlob(blob);
			}

			return {
				success: true,
				imageData: processedImageData,
				blob
			};

		} catch (error) {
			const errorMessage = error instanceof Error ? error.message : String(error);
			
			// Don't treat cancellation as an error
			if (errorMessage === 'Processing cancelled') {
				return {
					success: false,
					imageData: null,
					blob: null
				};
			}

			console.error('Error processing image:', error);
			
			return {
				success: false,
				imageData: null,
				blob: null,
				error: errorMessage
			};
		} finally {
			this.isProcessing = false;
			this.abortController = null;
			imageProcessingActions.setIsProcessing(false);
		}
	}

	/**
	 * Load image element with abort signal support
	 */
	private loadImage(imageUrl: string, signal: AbortSignal): Promise<HTMLImageElement> {
		return new Promise((resolve, reject) => {
			const imageElement = document.createElement('img');
			imageElement.crossOrigin = 'anonymous';

			const handleLoad = () => {
				cleanup();
				resolve(imageElement);
			};

			const handleError = (error: any) => {
				cleanup();
				reject(new Error('Image failed to load'));
			};

			const handleAbort = () => {
				cleanup();
				reject(new Error('Processing cancelled'));
			};

			const cleanup = () => {
				imageElement.removeEventListener('load', handleLoad);
				imageElement.removeEventListener('error', handleError);
				signal.removeEventListener('abort', handleAbort);
			};

			// Set up event listeners
			imageElement.addEventListener('load', handleLoad);
			imageElement.addEventListener('error', handleError);
			signal.addEventListener('abort', handleAbort);

			// Check if already aborted
			if (signal.aborted) {
				handleAbort();
				return;
			}

			// Start loading
			imageElement.src = imageUrl;
		});
	}

	/**
	 * Process image with fast low-resolution feedback for drag interactions
	 * Uses the same processing pipeline as final but with preview quality
	 */
	processImageAdaptive(
		imageUrl: string,
		params: StoreImageProcessingParams,
		onProgress?: ProcessingProgressCallback
	): Promise<ProcessingResult> {
		if (!browser) {
			return Promise.resolve({ success: false, imageData: null, blob: null, error: 'Not running in browser' });
		}

		// Check if we should process now or wait
		if (!this.dragFeedbackController.shouldProcessNow()) {
			const delay = this.dragFeedbackController.getNextProcessingDelay();
			
			// Return immediately for throttled requests - don't process
			return Promise.resolve({ 
				success: false, 
				imageData: null, 
				blob: null, 
				error: `Throttled: waiting ${delay}ms` 
			});
		}

		// Mark request as started for capacity tracking
		this.dragFeedbackController.markRequestStarted();
		const startTime = Date.now();

		// Use the same processing pipeline with preview quality
		return this.processImage(imageUrl, params, onProgress, 'preview')
			.then(result => {
				// Track completion time and success
				const processingTime = Date.now() - startTime;
				this.dragFeedbackController.markRequestCompleted(processingTime, result.success);
				return result;
			})
			.catch(error => {
				// Track failed processing
				const processingTime = Date.now() - startTime;
				this.dragFeedbackController.markRequestCompleted(processingTime, false);
				
				// Don't re-throw cancellation errors for adaptive processing
				const errorMessage = error instanceof Error ? error.message : String(error);
				if (errorMessage === 'Processing cancelled' || errorMessage === 'Request cancelled') {
					return {
						success: false,
						imageData: null,
						blob: null,
						error: errorMessage
					};
				}
				
				throw error;
			});
	}


	/**
	 * Get current drag feedback metrics for debugging
	 */
	getDragFeedbackMetrics() {
		return {
			...this.dragFeedbackController.getMetrics(),
			currentFPS: this.dragFeedbackController.getCurrentFPS()
		};
	}

	/**
	 * Reset processing state and clear cache
	 */
	reset(): void {
		this.cancel();
		this.lastParams = '';
		this.dragFeedbackController.reset();
		imageProcessingActions.resetProcessingState();
	}

	/**
	 * Get cache key for current parameters
	 */
	getParametersHash(params: StoreImageProcessingParams): string {
		return JSON.stringify(params);
	}

	/**
	 * Check if parameters have changed since last processing
	 */
	hasParametersChanged(params: StoreImageProcessingParams): boolean {
		const currentHash = this.getParametersHash(params);
		return currentHash !== this.lastParams;
	}
}

// Singleton instance
export const imageProcessingService = new ImageProcessingService();