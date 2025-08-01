import { writable, derived } from 'svelte/store';

// Generation progress information
export interface GenerationProgress {
	step: 'uploading' | 'processing' | 'generating' | 'polling' | 'completed' | 'failed';
	progress: number; // 0-100
	message: string;
	error?: string;
}

// Generation and API state
export interface GenerationState {
	generationId: string | null;
	currentTaskId: string | null;
	processingTaskId: string | null;
	generationTaskId: string | null;
	isGenerating: boolean;
	stlGenerationError: string | null;
	generatedSTLUrl: string | null;
	generationProgress: GenerationProgress | null;
}

const initialGenerationState: GenerationState = {
	generationId: null,
	currentTaskId: null,
	processingTaskId: null,
	generationTaskId: null,
	isGenerating: false,
	stlGenerationError: null,
	generatedSTLUrl: null,
	generationProgress: null
};

export const generationState = writable<GenerationState>(initialGenerationState);

// Individual stores for reactive bindings (maintain backward compatibility)
export const generationId = derived(generationState, $state => $state.generationId);
export const currentTaskId = derived(generationState, $state => $state.currentTaskId);
export const processingTaskId = derived(generationState, $state => $state.processingTaskId);
export const generationTaskId = derived(generationState, $state => $state.generationTaskId);
export const isGenerating = derived(generationState, $state => $state.isGenerating);
export const stlGenerationError = derived(generationState, $state => $state.stlGenerationError);
export const generatedSTLUrl = derived(generationState, $state => $state.generatedSTLUrl);
export const generationProgress = derived(generationState, $state => $state.generationProgress);

// Actions for updating generation state
export const generationActions = {
	setGenerationId: (id: string | null) => 
		generationState.update(state => ({ ...state, generationId: id })),
	
	setCurrentTaskId: (id: string | null) => 
		generationState.update(state => ({ ...state, currentTaskId: id })),
	
	setProcessingTaskId: (id: string | null) => 
		generationState.update(state => ({ ...state, processingTaskId: id })),
	
	setGenerationTaskId: (id: string | null) => 
		generationState.update(state => ({ ...state, generationTaskId: id })),
	
	setIsGenerating: (isGenerating: boolean) => 
		generationState.update(state => ({ ...state, isGenerating })),
	
	setStlGenerationError: (error: string | null) => 
		generationState.update(state => ({ ...state, stlGenerationError: error })),
	
	setGeneratedSTLUrl: (url: string | null) => 
		generationState.update(state => ({ ...state, generatedSTLUrl: url })),
	
	setGenerationProgress: (progress: GenerationProgress | null) => 
		generationState.update(state => ({ ...state, generationProgress: progress })),
	
	reset: () => generationState.set(initialGenerationState),
	
	resetError: () => 
		generationState.update(state => ({ ...state, stlGenerationError: null }))
};