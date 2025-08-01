import { writable, derived } from 'svelte/store';

// Image processing parameters and state
export interface ImageProcessingParams {
	grayscaleMethod: 'average' | 'luminance' | 'red' | 'green' | 'blue' | 'custom';
	brightness: number;
	contrast: number;
	gamma: number;
	invertColors: boolean;
}

export interface ImageState {
	// Upload state
	uploadedFile: File | null;
	uploadedImageUrl: string | null;
	
	// Processing state
	isProcessing: boolean;
	processedImageData: ImageData | null;
	processedImageBlob: Blob | null;
	processedImageUrl: string | null;
}

export interface ImageProcessingState extends ImageState {
	params: ImageProcessingParams;
}

const initialImageProcessingParams: ImageProcessingParams = {
	grayscaleMethod: 'luminance',
	brightness: 0,
	contrast: 0,
	gamma: 1.0,
	invertColors: false
};

const initialImageState: ImageState = {
	uploadedFile: null,
	uploadedImageUrl: null,
	isProcessing: false,
	processedImageData: null,
	processedImageBlob: null,
	processedImageUrl: null
};

const initialImageProcessingState: ImageProcessingState = {
	...initialImageState,
	params: initialImageProcessingParams
};

export const imageProcessingState = writable<ImageProcessingState>(initialImageProcessingState);

// Individual stores for reactive bindings (maintain backward compatibility)
export const uploadedFile = derived(imageProcessingState, $state => $state.uploadedFile);
export const uploadedImageUrl = derived(imageProcessingState, $state => $state.uploadedImageUrl);
export const isProcessing = derived(imageProcessingState, $state => $state.isProcessing);
export const processedImageData = derived(imageProcessingState, $state => $state.processedImageData);
export const processedImageBlob = derived(imageProcessingState, $state => $state.processedImageBlob);
export const processedImageUrl = derived(imageProcessingState, $state => $state.processedImageUrl);

// Parameter stores - these need to be writable for two-way binding
export const grayscaleMethod = writable(initialImageProcessingParams.grayscaleMethod);
export const brightness = writable(initialImageProcessingParams.brightness);
export const contrast = writable(initialImageProcessingParams.contrast);
export const gamma = writable(initialImageProcessingParams.gamma);
export const invertColors = writable(initialImageProcessingParams.invertColors);

// Sync parameter stores with main state (individual → main)
grayscaleMethod.subscribe(value => 
	imageProcessingState.update(state => ({ ...state, params: { ...state.params, grayscaleMethod: value } }))
);
brightness.subscribe(value => 
	imageProcessingState.update(state => ({ ...state, params: { ...state.params, brightness: value } }))
);
contrast.subscribe(value => 
	imageProcessingState.update(state => ({ ...state, params: { ...state.params, contrast: value } }))
);
gamma.subscribe(value => 
	imageProcessingState.update(state => ({ ...state, params: { ...state.params, gamma: value } }))
);
invertColors.subscribe(value => 
	imageProcessingState.update(state => ({ ...state, params: { ...state.params, invertColors: value } }))
);

// Sync main state with individual parameter stores (main → individual)
imageProcessingState.subscribe(state => {
	grayscaleMethod.set(state.params.grayscaleMethod);
	brightness.set(state.params.brightness);
	contrast.set(state.params.contrast);
	gamma.set(state.params.gamma);
	invertColors.set(state.params.invertColors);
});

// Actions for updating image processing state
export const imageProcessingActions = {
	setUploadedFile: (file: File | null, imageUrl: string | null) => 
		imageProcessingState.update(state => ({ 
			...state, 
			uploadedFile: file, 
			uploadedImageUrl: imageUrl 
		})),
	
	setIsProcessing: (isProcessing: boolean) => 
		imageProcessingState.update(state => ({ ...state, isProcessing })),
	
	setProcessedImageData: (data: ImageData | null) => 
		imageProcessingState.update(state => ({ ...state, processedImageData: data })),
	
	setProcessedImageBlob: (blob: Blob | null) => 
		imageProcessingState.update(state => ({ ...state, processedImageBlob: blob })),
	
	setProcessedImageUrl: (url: string | null) => 
		imageProcessingState.update(state => ({ ...state, processedImageUrl: url })),
	
	updateParams: (params: Partial<ImageProcessingParams>) => 
		imageProcessingState.update(state => ({ 
			...state, 
			params: { ...state.params, ...params } 
		})),
	
	setGrayscaleMethod: (method: ImageProcessingParams['grayscaleMethod']) => 
		imageProcessingState.update(state => ({ 
			...state, 
			params: { ...state.params, grayscaleMethod: method } 
		})),
	
	setBrightness: (brightness: number) => 
		imageProcessingState.update(state => ({ 
			...state, 
			params: { ...state.params, brightness } 
		})),
	
	setContrast: (contrast: number) => 
		imageProcessingState.update(state => ({ 
			...state, 
			params: { ...state.params, contrast } 
		})),
	
	setGamma: (gamma: number) => 
		imageProcessingState.update(state => ({ 
			...state, 
			params: { ...state.params, gamma } 
		})),
	
	setInvertColors: (invertColors: boolean) => 
		imageProcessingState.update(state => ({ 
			...state, 
			params: { ...state.params, invertColors } 
		})),
	
	reset: () => imageProcessingState.set(initialImageProcessingState),
	
	resetProcessingState: () => 
		imageProcessingState.update(state => ({
			...state,
			isProcessing: false,
			processedImageData: null,
			processedImageBlob: null,
			processedImageUrl: null
		}))
};