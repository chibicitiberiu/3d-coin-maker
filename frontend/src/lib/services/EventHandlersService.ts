import { imageProcessingActions } from '../stores/imageProcessingState';
import { coinParametersActions } from '../stores/coinParametersState';
import { generationActions } from '../stores/generationState';
import { uiActions } from '../stores/uiState';

export interface EventHandlersService {
	handleFileProcessed: (event: CustomEvent<{ file: File; imageUrl: string }>) => void;
	handleUploadError: (event: CustomEvent<{ message: string }>) => void;
	handleImageProcessingChanged: (event: CustomEvent<{
		grayscaleMethod: 'average' | 'luminance' | 'red' | 'green' | 'blue' | 'custom';
		brightness: number;
		contrast: number;
		gamma: number;
		invertColors: boolean;
		isDragFeedback?: boolean;
	}>) => void;
	handleCoinParametersChanged: (event: CustomEvent<{
		coinShape: 'circle' | 'square' | 'hexagon' | 'octagon';
		coinSize: number;
		coinThickness: number;
		reliefDepth: number;
	}>) => void;
	handleHeightmapPositioningChanged: (event: CustomEvent<{
		heightmapScale: number;
		offsetX: number;
		offsetY: number;
		rotation: number;
	}>) => void;
	handleTabChanged: (event: CustomEvent<{ tabId: string }>) => void;
}

export function createEventHandlersService(
	updatePreview: () => void,
	updatePreviewAdaptive: () => Promise<void>,
	setIsDragProcessing: (value: boolean) => void
): EventHandlersService {
	
	function handleFileProcessed(event: CustomEvent<{ file: File; imageUrl: string }>) {
		const { file, imageUrl } = event.detail;
		
		// Reset state through store actions
		imageProcessingActions.setUploadedFile(file, imageUrl);
		imageProcessingActions.resetProcessingState();
		generationActions.reset();
		
		console.log('File processed successfully:', file.name);
		
		// The reactive statement will automatically trigger processing for the new image
	}

	function handleUploadError(event: CustomEvent<{ message: string }>) {
		alert(event.detail.message);
	}

	function handleImageProcessingChanged(event: CustomEvent<{
		grayscaleMethod: 'average' | 'luminance' | 'red' | 'green' | 'blue' | 'custom';
		brightness: number;
		contrast: number;
		gamma: number;
		invertColors: boolean;
		isDragFeedback?: boolean;
	}>) {
		const { 
			grayscaleMethod: newGrayscaleMethod, 
			brightness: newBrightness, 
			contrast: newContrast, 
			gamma: newGamma, 
			invertColors: newInvertColors, 
			isDragFeedback 
		} = event.detail;
		
		imageProcessingActions.updateParams({
			grayscaleMethod: newGrayscaleMethod,
			brightness: newBrightness,
			contrast: newContrast,
			gamma: newGamma,
			invertColors: newInvertColors
		});
		
		// Use adaptive processing for drag feedback, normal processing otherwise
		if (isDragFeedback) {
			setIsDragProcessing(true);
			updatePreviewAdaptive().finally(() => {
				// Short delay before allowing regular processing again
				setTimeout(() => {
					setIsDragProcessing(false);
				}, 100);
			});
		} else {
			setIsDragProcessing(false);
			updatePreview();
		}
	}

	function handleCoinParametersChanged(event: CustomEvent<{
		coinShape: 'circle' | 'square' | 'hexagon' | 'octagon';
		coinSize: number;
		coinThickness: number;
		reliefDepth: number;
	}>) {
		const { 
			coinShape: newCoinShape, 
			coinSize: newCoinSize, 
			coinThickness: newCoinThickness, 
			reliefDepth: newReliefDepth 
		} = event.detail;
		
		coinParametersActions.updateCoinParameters({
			coinShape: newCoinShape,
			coinSize: newCoinSize,
			coinThickness: newCoinThickness,
			reliefDepth: newReliefDepth
		});
	}

	function handleHeightmapPositioningChanged(event: CustomEvent<{
		heightmapScale: number;
		offsetX: number;
		offsetY: number;
		rotation: number;
	}>) {
		const { 
			heightmapScale: newHeightmapScale, 
			offsetX: newOffsetX, 
			offsetY: newOffsetY, 
			rotation: newRotation 
		} = event.detail;
		
		coinParametersActions.updateHeightmapPositioning({
			heightmapScale: newHeightmapScale,
			offsetX: newOffsetX,
			offsetY: newOffsetY,
			rotation: newRotation
		});
		
		// These parameters only affect canvas display, not image processing
		// CanvasViewer will automatically redraw when its props change
	}

	function handleTabChanged(event: CustomEvent<{ tabId: string }>) {
		uiActions.setActiveTab(event.detail.tabId as 'original' | 'processed' | 'result');
	}

	return {
		handleFileProcessed,
		handleUploadError,
		handleImageProcessingChanged,
		handleCoinParametersChanged,
		handleHeightmapPositioningChanged,
		handleTabChanged
	};
}