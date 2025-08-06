import { env } from '$env/dynamic/public';

const API_BASE_URL = env.PUBLIC_API_BASE_URL || '/api';

export interface GenerationStatus {
	generation_id: string;
	status: string;
	progress: number;
	step: string;
	error?: string | null;
	has_original: boolean;
	has_processed: boolean;
	has_heightmap: boolean;
	has_stl: boolean;
	stl_timestamp?: number | null;
}

export interface ImageProcessingParams {
	grayscaleMethod: 'average' | 'luminance' | 'red' | 'green' | 'blue';
	brightness: number;
	contrast: number;
	gamma: number;
	invertColors: boolean;
}

export interface CoinParameters {
	shape: 'circle' | 'square' | 'hexagon' | 'octagon';
	diameter: number;
	thickness: number;
	reliefDepth: number;
	scale: number;
	offsetX: number;
	offsetY: number;
	rotation: number;
}

export interface RequestOptions {
	timeout?: number;
	retries?: number;
	retryDelay?: number;
	signal?: AbortSignal;
}

export class BackendService {
	private baseUrl: string;
	private activeRequests = new Map<string, AbortController>();

	constructor() {
		this.baseUrl = API_BASE_URL;
	}

	/**
	 * Enhanced fetch with retry logic, timeout, and error handling
	 */
	private async enhancedFetch(
		url: string, 
		options: RequestInit & RequestOptions = {}
	): Promise<Response> {
		const { timeout = 30000, retries = 3, retryDelay = 1000, signal, ...fetchOptions } = options;
		
		// Create abort controller for timeout
		const controller = new AbortController();
		const combinedSignal = signal ? this.combineAbortSignals([signal, controller.signal]) : controller.signal;
		
		// Set timeout
		const timeoutId = setTimeout(() => controller.abort(), timeout);
		
		let lastError: Error;
		
		for (let attempt = 0; attempt <= retries; attempt++) {
			try {
				const response = await fetch(url, {
					...fetchOptions,
					signal: combinedSignal
				});
				
				clearTimeout(timeoutId);
				
				if (!response.ok) {
					const errorData = await response.json().catch(() => ({}));
					throw new Error(errorData.error || `Request failed: ${response.statusText}`);
				}
				
				return response;
			} catch (error) {
				lastError = error instanceof Error ? error : new Error('Unknown error');
				
				// Don't retry if aborted or on last attempt
				if (combinedSignal.aborted || attempt === retries) {
					clearTimeout(timeoutId);
					throw lastError;
				}
				
				// Wait before retry
				await new Promise(resolve => setTimeout(resolve, retryDelay * Math.pow(2, attempt)));
			}
		}
		
		clearTimeout(timeoutId);
		throw lastError!;
	}

	/**
	 * Combine multiple AbortSignals
	 */
	private combineAbortSignals(signals: AbortSignal[]): AbortSignal {
		const controller = new AbortController();
		
		for (const signal of signals) {
			if (signal.aborted) {
				controller.abort();
				break;
			}
			signal.addEventListener('abort', () => controller.abort());
		}
		
		return controller.signal;
	}

	/**
	 * Cancel a specific request by ID
	 */
	cancelRequest(requestId: string): void {
		const controller = this.activeRequests.get(requestId);
		if (controller) {
			controller.abort();
			this.activeRequests.delete(requestId);
		}
	}

	/**
	 * Cancel all active requests
	 */
	cancelAllRequests(): void {
		for (const [id, controller] of this.activeRequests) {
			controller.abort();
		}
		this.activeRequests.clear();
	}

	/**
	 * Upload an image file and get a generation ID
	 */
	async uploadImage(file: File, options: RequestOptions = {}): Promise<{ generation_id: string; message: string }> {
		const requestId = `upload_${Date.now()}`;
		const controller = new AbortController();
		this.activeRequests.set(requestId, controller);

		try {
			const formData = new FormData();
			formData.append('image', file);

			const response = await this.enhancedFetch(`${this.baseUrl}/upload/`, {
				method: 'POST',
				body: formData,
				signal: controller.signal,
				...options
			});

			return await response.json();
		} finally {
			this.activeRequests.delete(requestId);
		}
	}

	/**
	 * Process an uploaded image with parameters
	 */
	async processImage(
		generationId: string,
		filename: string,
		params: ImageProcessingParams,
		options: RequestOptions = {}
	): Promise<{ task_id: string; generation_id: string; message: string }> {
		const requestId = `process_${generationId}`;
		const controller = new AbortController();
		this.activeRequests.set(requestId, controller);

		try {
			const requestData = {
				generation_id: generationId,
				filename: filename,
				grayscale_method: params.grayscaleMethod,
				brightness: params.brightness,
				contrast: params.contrast,
				gamma: params.gamma,
				invert: params.invertColors,
			};

			const response = await this.enhancedFetch(`${this.baseUrl}/process/`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify(requestData),
				signal: controller.signal,
				...options
			});

			return await response.json();
		} finally {
			this.activeRequests.delete(requestId);
		}
	}

	/**
	 * Generate STL file from processed image
	 */
	async generateSTL(
		generationId: string,
		params: CoinParameters,
		options: RequestOptions = {}
	): Promise<{ task_id: string; generation_id: string; message: string }> {
		const requestId = `generate_${generationId}`;
		const controller = new AbortController();
		this.activeRequests.set(requestId, controller);

		try {
			const requestData = {
				generation_id: generationId,
				shape: params.shape,
				diameter: params.diameter,
				thickness: params.thickness,
				relief_depth: params.reliefDepth,
				scale: params.scale,
				offset_x: params.offsetX,
				offset_y: params.offsetY,
				rotation: params.rotation,
			};

			const response = await this.enhancedFetch(`${this.baseUrl}/generate/`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify(requestData),
				signal: controller.signal,
				...options
			});

			return await response.json();
		} finally {
			this.activeRequests.delete(requestId);
		}
	}

	/**
	 * Get the status of a generation process
	 */
	async getGenerationStatus(
		generationId: string, 
		taskId?: string, 
		options: RequestOptions = {}
	): Promise<GenerationStatus> {
		const requestId = `status_${generationId}_${taskId || 'general'}`;
		const controller = new AbortController();
		this.activeRequests.set(requestId, controller);

		try {
			const url = new URL(`${this.baseUrl}/status/${generationId}/`);
			if (taskId) {
				url.searchParams.set('task_id', taskId);
			}

			const response = await this.enhancedFetch(url.toString(), {
				signal: controller.signal,
				...options
			});

			return await response.json();
		} finally {
			this.activeRequests.delete(requestId);
		}
	}

	/**
	 * Get processed image preview URL
	 */
	getPreviewImageUrl(generationId: string, type: 'processed' | 'heightmap' = 'processed'): string {
		return `${this.baseUrl}/preview/${generationId}?type=${type}`;
	}

	/**
	 * Get STL download URL
	 */
	getSTLDownloadUrl(generationId: string, timestamp?: number): string {
		const baseUrl = `${this.baseUrl}/download/${generationId}/stl`;
		return timestamp ? `${baseUrl}?t=${timestamp}` : baseUrl;
	}

	/**
	 * Download STL file as blob
	 */
	async downloadSTL(generationId: string, options: RequestOptions = {}): Promise<Blob> {
		const requestId = `download_${generationId}`;
		const controller = new AbortController();
		this.activeRequests.set(requestId, controller);

		try {
			const response = await this.enhancedFetch(this.getSTLDownloadUrl(generationId), {
				signal: controller.signal,
				...options
			});

			return await response.blob();
		} finally {
			this.activeRequests.delete(requestId);
		}
	}

	/**
	 * Health check
	 */
	async healthCheck(options: RequestOptions = {}): Promise<any> {
		const requestId = `health_${Date.now()}`;
		const controller = new AbortController();
		this.activeRequests.set(requestId, controller);

		try {
			const response = await this.enhancedFetch(`${this.baseUrl}/health/`, {
				signal: controller.signal,
				...options
			});
			return await response.json();
		} finally {
			this.activeRequests.delete(requestId);
		}
	}

	/**
	 * Get active request count for monitoring
	 */
	getActiveRequestCount(): number {
		return this.activeRequests.size;
	}

	/**
	 * Get active request IDs
	 */
	getActiveRequestIds(): string[] {
		return Array.from(this.activeRequests.keys());
	}
}

// Singleton instance
export const backendService = new BackendService();