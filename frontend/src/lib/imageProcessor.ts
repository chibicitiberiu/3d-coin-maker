import { browser } from '$app/environment';

// Photon WASM types
export interface PhotonImage {
	get_pixels(): Uint8Array;
	get_raw_pixels(): Uint8Array;
	get_width(): number;
	get_height(): number;
	get_image_data(): ImageData;
	free(): void;
}

export interface PhotonModule {
	// Core functions from demos
	open_image: (canvas: HTMLCanvasElement, ctx: CanvasRenderingContext2D) => PhotonImage;
	putImageData: (canvas: HTMLCanvasElement, ctx: CanvasRenderingContext2D, image: PhotonImage) => void;
	
	// PhotonImage constructor
	PhotonImage: {
		new_from_imagedata: (imageData: ImageData) => PhotonImage;
	};
	
	// Grayscale functions from demos
	grayscale: (image: PhotonImage) => void;
	grayscale_average: (image: PhotonImage) => void;
	grayscale_luminance: (image: PhotonImage) => void;
	grayscale_red: (image: PhotonImage) => void;
	grayscale_green: (image: PhotonImage) => void;
	grayscale_blue: (image: PhotonImage) => void;
	single_channel_grayscale: (image: PhotonImage, channel: number) => void;
	
	// Effects functions - using proper adjust functions
	adjust_brightness: (image: PhotonImage, amount: number) => void;
	adjust_contrast: (image: PhotonImage, amount: number) => void;
	adjust_gamma: (image: PhotonImage, gamma: number) => void;
	
	// Optional functions (may or may not exist)
	gamma_correction?: (image: PhotonImage, red: number, green: number, blue: number) => void;
	invert?: (image: PhotonImage) => void;
}

export type GrayscaleMethod = 'average' | 'luminance' | 'red' | 'green' | 'blue' | 'custom';

export interface ImageProcessingParams {
	grayscaleMethod: GrayscaleMethod;
	brightness: number;
	contrast: number;
	gamma: number;
	invertColors: boolean;
}

let photonModule: PhotonModule | null = null;
let isPhotonLoaded = false;

// Initialize Photon WASM following demo pattern
async function initPhoton(): Promise<boolean> {
	if (!browser) return false;
	
	try {
		// Load Photon WASM exactly like the demos
		const photon = await import('@silvia-odwyer/photon');
		console.log('Photon module loaded:', photon);
		console.log('Available methods:', Object.keys(photon));
		
		// Initialize WASM binary (required for wasm-bindgen modules)
		if (typeof photon.default === 'function') {
			console.log('Initializing Photon WASM...');
			await photon.default();
		}
		
		// Store the photon module
		photonModule = photon as any;
		isPhotonLoaded = true;
		console.log('Photon WASM loaded and initialized successfully');
		return true;
	} catch (error) {
		console.warn('Failed to load Photon WASM:', error);
		return false;
	}
}

// Fallback image processing using Canvas API
function fallbackGrayscale(imageData: ImageData, method: GrayscaleMethod): ImageData {
	const data = imageData.data;
	
	for (let i = 0; i < data.length; i += 4) {
		const r = data[i];
		const g = data[i + 1];
		const b = data[i + 2];
		
		let gray: number;
		switch (method) {
			case 'average':
				gray = (r + g + b) / 3;
				break;
			case 'luminance':
				gray = 0.299 * r + 0.587 * g + 0.114 * b;
				break;
			case 'red':
				gray = r;
				break;
			case 'green':
				gray = g;
				break;
			case 'blue':
				gray = b;
				break;
			default:
				gray = 0.299 * r + 0.587 * g + 0.114 * b;
		}
		
		data[i] = gray;
		data[i + 1] = gray;
		data[i + 2] = gray;
	}
	
	return imageData;
}

function fallbackAdjustBrightness(imageData: ImageData, brightness: number): ImageData {
	const data = imageData.data;
	const adjustment = brightness * 2.55; // Convert -100/100 to -255/255
	
	for (let i = 0; i < data.length; i += 4) {
		data[i] = Math.max(0, Math.min(255, data[i] + adjustment));
		data[i + 1] = Math.max(0, Math.min(255, data[i + 1] + adjustment));
		data[i + 2] = Math.max(0, Math.min(255, data[i + 2] + adjustment));
	}
	
	return imageData;
}

function fallbackAdjustContrast(imageData: ImageData, contrast: number): ImageData {
	const data = imageData.data;
	const factor = (259 * (contrast + 255)) / (255 * (259 - contrast));
	
	for (let i = 0; i < data.length; i += 4) {
		data[i] = Math.max(0, Math.min(255, factor * (data[i] - 128) + 128));
		data[i + 1] = Math.max(0, Math.min(255, factor * (data[i + 1] - 128) + 128));
		data[i + 2] = Math.max(0, Math.min(255, factor * (data[i + 2] - 128) + 128));
	}
	
	return imageData;
}

function fallbackAdjustGamma(imageData: ImageData, gamma: number): ImageData {
	const data = imageData.data;
	
	for (let i = 0; i < data.length; i += 4) {
		data[i] = Math.pow(data[i] / 255, gamma) * 255;
		data[i + 1] = Math.pow(data[i + 1] / 255, gamma) * 255;
		data[i + 2] = Math.pow(data[i + 2] / 255, gamma) * 255;
	}
	
	return imageData;
}

function fallbackInvert(imageData: ImageData): ImageData {
	const data = imageData.data;
	
	for (let i = 0; i < data.length; i += 4) {
		data[i] = 255 - data[i];
		data[i + 1] = 255 - data[i + 1];
		data[i + 2] = 255 - data[i + 2];
	}
	
	return imageData;
}


export async function processImage(
	imageElement: HTMLImageElement,
	params: ImageProcessingParams
): Promise<ImageData | null> {
	if (!browser) return null;
	
	try {
		// Create canvas and get image data
		const canvas = document.createElement('canvas');
		const ctx = canvas.getContext('2d');
		if (!ctx) return null;
		
		canvas.width = imageElement.naturalWidth;
		canvas.height = imageElement.naturalHeight;
		
		// Fill with black background BEFORE drawing image to flatten alpha channel
		ctx.fillStyle = 'black';
		ctx.fillRect(0, 0, canvas.width, canvas.height);
		
		// Now draw the image - alpha will composite against black background
		ctx.drawImage(imageElement, 0, 0);
		
		let imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
		
		// Try to initialize Photon if not already loaded
		if (!isPhotonLoaded) {
			await initPhoton();
		}
		
		if (isPhotonLoaded && photonModule) {
			console.log('Using Photon WASM processing');
			
			// Create a temporary canvas to use with Photon (following official docs)
			const tempCanvas = document.createElement('canvas');
			tempCanvas.width = imageData.width;
			tempCanvas.height = imageData.height;
			const tempCtx = tempCanvas.getContext('2d');
			if (!tempCtx) throw new Error('Could not get canvas context');
			
			// Put ImageData on canvas
			tempCtx.putImageData(imageData, 0, 0);
			
			// Create PhotonImage using official API
			const photonImage = photonModule.open_image(tempCanvas, tempCtx);
			console.log('Created PhotonImage using open_image');
			
			// Apply grayscale following demo patterns
			switch (params.grayscaleMethod) {
				case 'red':
					// Use single_channel_grayscale with channel 0 (red) like the demo
					photonModule.single_channel_grayscale(photonImage, 0);
					break;
				case 'green':
					// Use single_channel_grayscale with channel 1 (green)
					photonModule.single_channel_grayscale(photonImage, 1);
					break;
				case 'blue':
					// Use single_channel_grayscale with channel 2 (blue)
					photonModule.single_channel_grayscale(photonImage, 2);
					break;
				case 'luminance':
				case 'average':
				default:
					// Use standard grayscale function like in demo
					photonModule.grayscale(photonImage);
			}
			
			// Apply brightness - map from -100/100 to -255/255
			if (params.brightness !== 0) {
				// Map UI range (-100 to 100) to Photon range (-255 to 255)
				const brightnessValue = Math.round((params.brightness / 100) * 255);
				photonModule.adjust_brightness(photonImage, brightnessValue);
			}
			
			// Apply contrast - map from -100/100 to -255/255 range
			if (params.contrast !== 0) {
				// Map UI range (-100 to 100) to Photon range (-255 to 255)
				const contrastValue = Math.round((params.contrast / 100) * 255);
				photonModule.adjust_contrast(photonImage, contrastValue);
			}
			
			// Apply gamma correction - use same gamma value for all RGB channels
			if (params.gamma !== 1.0) {
				if (photonModule.gamma_correction) {
					// Use the same gamma value for red, green, and blue channels
					photonModule.gamma_correction(photonImage, params.gamma, params.gamma, params.gamma);
				}
			}
			
			// Apply invert - demos don't show this, check if exists
			if (params.invertColors) {
				if (photonModule.invert) {
					photonModule.invert(photonImage);
				}
			}
			
			// Put processed image back on canvas using official API
			photonModule.putImageData(tempCanvas, tempCtx, photonImage);
			
			// Get the processed ImageData from canvas
			imageData = tempCtx.getImageData(0, 0, tempCanvas.width, tempCanvas.height);
			console.log('Photon processing completed successfully');
		} else {
			console.error('Photon WASM not loaded, cannot process image');
			return null;
		}
		
		return imageData;
	} catch (error) {
		console.error('Error processing image:', error);
		return null;
	}
}

// Convert ImageData to blob for download/preview
export function imageDataToBlob(imageData: ImageData): Promise<Blob> {
	return new Promise((resolve, reject) => {
		const canvas = document.createElement('canvas');
		const ctx = canvas.getContext('2d');
		if (!ctx) {
			reject(new Error('Could not get canvas context'));
			return;
		}
		
		canvas.width = imageData.width;
		canvas.height = imageData.height;
		ctx.putImageData(imageData, 0, 0);
		
		canvas.toBlob((blob) => {
			if (blob) {
				resolve(blob);
			} else {
				reject(new Error('Could not create blob'));
			}
		}, 'image/png');
	});
}

/**
 * Convert an HTML image element to ImageData for worker processing
 */
export function imageDataFromImageElement(imageElement: HTMLImageElement): ImageData {
	const canvas = document.createElement('canvas');
	const ctx = canvas.getContext('2d');
	
	if (!ctx) {
		throw new Error('Could not get canvas context');
	}
	
	canvas.width = imageElement.naturalWidth;
	canvas.height = imageElement.naturalHeight;
	
	ctx.drawImage(imageElement, 0, 0);
	
	return ctx.getImageData(0, 0, canvas.width, canvas.height);
}

/**
 * Load and initialize Photon WASM module (for worker)
 */
export async function loadPhoton(): Promise<PhotonModule> {
	if (!photonModule) {
		await initPhoton();
	}
	
	if (!photonModule) {
		throw new Error('Failed to load Photon WASM');
	}
	
	return photonModule;
}

// PhotonModule interface is already exported above