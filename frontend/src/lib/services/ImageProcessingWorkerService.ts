// Image Processing Worker Service
// Manages Web Worker for non-blocking image processing

import type { ImageProcessingParams } from '../stores/imageProcessingState';

// Simple browser check without SvelteKit environment dependency
const isBrowser = typeof window !== 'undefined' && typeof document !== 'undefined';

export interface ProcessingProgress {
	step: string;
	progress: number;
	message: string;
}

export interface ProcessingResult {
	success: boolean;
	imageData?: ImageData;
	error?: string;
}

interface PendingRequest {
	resolve: (result: ProcessingResult) => void;
	reject: (error: Error) => void;
	onProgress?: (progress: ProcessingProgress) => void;
}

class ImageProcessingWorkerService {
	private worker: Worker | null = null;
	private pendingRequests = new Map<string, PendingRequest>();
	private requestIdCounter = 0;

	constructor() {
		this.initializeWorker();
	}

	private initializeWorker() {
		// Only initialize worker in browser environment
		if (!isBrowser) {
			console.log('ImageProcessingWorkerService: Skipping worker initialization on server');
			return;
		}

		try {
			// Create worker from the TypeScript file - Vite will handle the bundling
			this.worker = new Worker(
				new URL('../workers/imageProcessingWorker.ts', import.meta.url),
				{ type: 'module' }
			);

			this.worker.onmessage = (event) => {
				console.log('Worker message received:', event.data.type, event.data.id);
				this.handleWorkerMessage(event);
			};

			this.worker.onerror = (error) => {
				console.error('Worker error:', error);
				this.worker = null; // Mark worker as failed
				// Reject all pending requests
				this.pendingRequests.forEach(({ reject }) => {
					reject(new Error('Worker encountered an error'));
				});
				this.pendingRequests.clear();
			};

			console.log('ImageProcessingWorkerService: Worker initialized successfully');
		} catch (error) {
			console.error('Failed to initialize worker:', error);
			this.worker = null; // Ensure worker is null on failure
		}
	}

	private handleWorkerMessage(event: MessageEvent) {
		const { type, id } = event.data;

		const request = this.pendingRequests.get(id);
		if (!request) {
			console.warn('Received message for unknown request ID:', id);
			return;
		}

		switch (type) {
			case 'progress':
				if (request.onProgress) {
					const { step, progress, message } = event.data;
					request.onProgress({ step, progress, message });
				}
				break;

			case 'result':
				const { success, imageData, error } = event.data;
				
				// Remove from pending requests
				this.pendingRequests.delete(id);

				// Resolve/reject the promise
				if (success && imageData) {
					request.resolve({ success: true, imageData });
				} else {
					request.resolve({ success: false, error: error || 'Processing failed' });
				}
				break;

			default:
				console.warn('Unknown message type from worker:', type);
		}
	}

	private generateRequestId(): string {
		return `req_${++this.requestIdCounter}_${Date.now()}`;
	}

	/**
	 * Process image with given parameters using Web Worker
	 */
	async processImage(
		imageData: ImageData,
		params: ImageProcessingParams,
		onProgress?: (progress: ProcessingProgress) => void
	): Promise<ProcessingResult> {
		if (!isBrowser) {
			return { success: false, error: 'Not in browser environment' };
		}
		
		if (!this.worker) {
			return { success: false, error: 'Worker not available - falling back to main thread processing would be needed' };
		}

		const requestId = this.generateRequestId();

		return new Promise<ProcessingResult>((resolve, reject) => {
			// Store the request
			this.pendingRequests.set(requestId, { resolve, reject, onProgress });

			// Send message to worker
			this.worker!.postMessage({
				type: 'processImage',
				id: requestId,
				imageData,
				params
			});
		});
	}

	/**
	 * Cancel all pending requests
	 */
	cancelAllRequests() {
		this.pendingRequests.forEach(({ reject }) => {
			reject(new Error('Request cancelled'));
		});
		this.pendingRequests.clear();
	}

	/**
	 * Terminate the worker and clean up
	 */
	terminate() {
		if (this.worker) {
			this.worker.terminate();
			this.worker = null;
		}
		this.cancelAllRequests();
	}
}

// Export singleton instance with lazy initialization
let _instance: ImageProcessingWorkerService | null = null;

export const imageProcessingWorkerService = {
	getInstance(): ImageProcessingWorkerService {
		if (!_instance) {
			_instance = new ImageProcessingWorkerService();
		}
		return _instance;
	},
	
	// Proxy methods for easier usage
	async processImage(
		imageData: ImageData,
		params: ImageProcessingParams,
		onProgress?: (progress: ProcessingProgress) => void
	): Promise<ProcessingResult> {
		return this.getInstance().processImage(imageData, params, onProgress);
	},
	
	cancelAllRequests() {
		if (_instance) {
			_instance.cancelAllRequests();
		}
	},
	
	terminate() {
		if (_instance) {
			_instance.terminate();
			_instance = null;
		}
	}
};