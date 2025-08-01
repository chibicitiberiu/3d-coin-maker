import { env } from '$env/dynamic/public';

const API_BASE_URL = env.PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

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

export class CoinMakerAPI {
	private baseUrl: string;

	constructor() {
		this.baseUrl = API_BASE_URL;
	}

	/**
	 * Upload an image file and get a generation ID
	 */
	async uploadImage(file: File): Promise<{ generation_id: string; message: string }> {
		const formData = new FormData();
		formData.append('image', file);

		const response = await fetch(`${this.baseUrl}/upload/`, {
			method: 'POST',
			body: formData,
		});

		if (!response.ok) {
			const errorData = await response.json().catch(() => ({}));
			throw new Error(errorData.error || `Upload failed: ${response.statusText}`);
		}

		return response.json();
	}

	/**
	 * Process an uploaded image with parameters
	 */
	async processImage(
		generationId: string,
		filename: string,
		params: ImageProcessingParams
	): Promise<{ task_id: string; generation_id: string; message: string }> {
		const requestData = {
			generation_id: generationId,
			filename: filename,
			grayscale_method: params.grayscaleMethod,
			brightness: params.brightness,
			contrast: params.contrast,
			gamma: params.gamma,
			invert: params.invertColors,
		};

		const response = await fetch(`${this.baseUrl}/process/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify(requestData),
		});

		if (!response.ok) {
			const errorData = await response.json().catch(() => ({}));
			throw new Error(errorData.error || `Image processing failed: ${response.statusText}`);
		}

		return response.json();
	}

	/**
	 * Generate STL file from processed image
	 */
	async generateSTL(
		generationId: string,
		params: CoinParameters
	): Promise<{ task_id: string; generation_id: string; message: string }> {
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

		const response = await fetch(`${this.baseUrl}/generate/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify(requestData),
		});

		if (!response.ok) {
			const errorData = await response.json().catch(() => ({}));
			throw new Error(errorData.error || `STL generation failed: ${response.statusText}`);
		}

		return response.json();
	}

	/**
	 * Get the status of a generation process
	 */
	async getGenerationStatus(generationId: string, taskId?: string): Promise<GenerationStatus> {
		const url = new URL(`${this.baseUrl}/status/${generationId}/`);
		if (taskId) {
			url.searchParams.set('task_id', taskId);
		}

		const response = await fetch(url.toString());

		if (!response.ok) {
			const errorData = await response.json().catch(() => ({}));
			throw new Error(errorData.error || `Status check failed: ${response.statusText}`);
		}

		return response.json();
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
	async downloadSTL(generationId: string): Promise<Blob> {
		const response = await fetch(this.getSTLDownloadUrl(generationId));

		if (!response.ok) {
			throw new Error(`STL download failed: ${response.statusText}`);
		}

		return response.blob();
	}

	/**
	 * Health check
	 */
	async healthCheck(): Promise<any> {
		const response = await fetch(`${this.baseUrl}/health/`);
		return response.json();
	}
}

export const api = new CoinMakerAPI();