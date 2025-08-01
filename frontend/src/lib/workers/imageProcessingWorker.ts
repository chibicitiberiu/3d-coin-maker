// Image Processing Web Worker
// This worker handles heavy image processing tasks in the background

import { loadPhoton, type PhotonModule } from '../imageProcessor';

let photonModule: PhotonModule | null = null;

// Message types
interface ProcessImageMessage {
	type: 'processImage';
	id: string;
	imageData: ImageData;
	params: {
		grayscaleMethod: 'average' | 'luminance' | 'red' | 'green' | 'blue' | 'custom';
		brightness: number;
		contrast: number;
		gamma: number;
		invertColors: boolean;
	};
}

interface ProgressMessage {
	type: 'progress';
	id: string;
	step: string;
	progress: number;
	message: string;
}

interface ResultMessage {
	type: 'result';
	id: string;
	success: boolean;
	imageData?: ImageData;
	error?: string;
}

type WorkerMessage = ProcessImageMessage;

// Initialize Photon WASM
async function initializePhoton() {
	if (!photonModule) {
		try {
			photonModule = await loadPhoton();
			console.log('Worker: Photon WASM initialized successfully');
		} catch (error) {
			console.error('Worker: Failed to initialize Photon WASM:', error);
			throw error;
		}
	}
}

// Send progress update
function sendProgress(id: string, step: string, progress: number, message: string) {
	const progressMsg: ProgressMessage = {
		type: 'progress',
		id,
		step,
		progress,
		message
	};
	self.postMessage(progressMsg);
}

// Send result
function sendResult(id: string, success: boolean, imageData?: ImageData, error?: string) {
	const resultMsg: ResultMessage = {
		type: 'result',
		id,
		success,
		imageData,
		error
	};
	self.postMessage(resultMsg);
}

// Process image using Photon WASM
async function processImage(id: string, imageData: ImageData, params: ProcessImageMessage['params']) {
	try {
		sendProgress(id, 'loading', 10, 'Loading image...');
		
		// Ensure Photon is initialized
		if (!photonModule) {
			await initializePhoton();
		}

		sendProgress(id, 'processing', 30, 'Processing image parameters...');

		// Create PhotonImage from ImageData
		// Create PhotonImage from ImageData using OffscreenCanvas
		const canvas = new OffscreenCanvas(imageData.width, imageData.height);
		const ctx = canvas.getContext('2d');
		if (!ctx) throw new Error('Could not get OffscreenCanvas context');
		
		ctx.putImageData(imageData, 0, 0);
		const photonImg = photonModule.open_image(canvas as any, ctx as any);

		// Apply grayscale conversion using available methods
		switch (params.grayscaleMethod) {
			case 'red':
				// Use single_channel_grayscale with channel 0 (red)
				if (photonModule.single_channel_grayscale) {
					photonModule.single_channel_grayscale(photonImg, 0);
				} else {
					photonModule.grayscale(photonImg);
				}
				break;
			case 'green':
				// Use single_channel_grayscale with channel 1 (green)
				if (photonModule.single_channel_grayscale) {
					photonModule.single_channel_grayscale(photonImg, 1);
				} else {
					photonModule.grayscale(photonImg);
				}
				break;
			case 'blue':
				// Use single_channel_grayscale with channel 2 (blue)
				if (photonModule.single_channel_grayscale) {
					photonModule.single_channel_grayscale(photonImg, 2);
				} else {
					photonModule.grayscale(photonImg);
				}
				break;
			case 'luminance':
			case 'average':
			case 'custom':
			default:
				// Use standard grayscale function
				photonModule.grayscale(photonImg);
		}

		sendProgress(id, 'adjusting', 50, 'Applying adjustments...');

		// Apply brightness adjustment
		if (params.brightness !== 0) {
			photonModule.adjust_brightness(photonImg, params.brightness);
		}

		// Apply contrast adjustment
		if (params.contrast !== 0) {
			photonModule.adjust_contrast(photonImg, params.contrast);
		}

		// Apply gamma correction
		if (params.gamma !== 1.0) {
			if (photonModule.gamma_correction) {
				// Use the same gamma value for red, green, and blue channels
				photonModule.gamma_correction(photonImg, params.gamma, params.gamma, params.gamma);
			} else if (photonModule.adjust_gamma) {
				photonModule.adjust_gamma(photonImg, params.gamma);
			}
		}

		// Apply color inversion
		if (params.invertColors) {
			photonModule.invert(photonImg);
		}

		sendProgress(id, 'converting', 80, 'Converting result...');

		// Get processed image data using PhotonImage methods
		let processedImageData: ImageData;
		
		try {
			// Try to get raw pixels and create ImageData manually
			const rawPixels = photonImg.get_raw_pixels();
			const width = photonImg.get_width();
			const height = photonImg.get_height();
			
			console.log('Worker: Got raw pixels, width:', width, 'height:', height, 'pixels length:', rawPixels.length);
			
			// Create ImageData from raw pixels
			processedImageData = new ImageData(new Uint8ClampedArray(rawPixels), width, height);
			
		} catch (rawError) {
			console.warn('Worker: Failed to get raw pixels, trying putImageData approach:', rawError);
			
			// Fallback: try putImageData approach
			try {
				photonModule.putImageData(canvas as any, ctx as any, photonImg);
				processedImageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
			} catch (putError) {
				console.error('Worker: Both methods failed:', putError);
				throw new Error('Failed to extract processed image data');
			}
		}

		sendProgress(id, 'completed', 100, 'Processing completed!');

		// Clean up
		photonImg.free();

		// Send result
		sendResult(id, true, processedImageData);

	} catch (error) {
		console.error('Worker: Error processing image:', error);
		sendResult(id, false, undefined, error instanceof Error ? error.message : 'Processing failed');
	}
}

// Handle messages from main thread
self.onmessage = async (event: MessageEvent<WorkerMessage>) => {
	const { type, id } = event.data;

	switch (type) {
		case 'processImage':
			const { imageData, params } = event.data;
			await processImage(id, imageData, params);
			break;
		default:
			console.warn('Worker: Unknown message type:', type);
	}
};