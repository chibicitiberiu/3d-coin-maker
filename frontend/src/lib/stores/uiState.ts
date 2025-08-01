import { writable, derived } from 'svelte/store';

// UI state management
export interface UIState {
	activeTab: 'original' | 'processed' | 'result';
	
	// Collapsible sections state
	imageProcessingExpanded: boolean;
	coinParametersExpanded: boolean;
	heightmapPositioningExpanded: boolean;
}

const initialUIState: UIState = {
	activeTab: 'processed',
	imageProcessingExpanded: true,
	coinParametersExpanded: true,
	heightmapPositioningExpanded: true
};

export const uiState = writable<UIState>(initialUIState);

// Individual stores for reactive bindings - these need to be writable for two-way binding
export const activeTab = writable(initialUIState.activeTab);
export const imageProcessingExpanded = writable(initialUIState.imageProcessingExpanded);
export const coinParametersExpanded = writable(initialUIState.coinParametersExpanded);
export const heightmapPositioningExpanded = writable(initialUIState.heightmapPositioningExpanded);

// Sync individual stores with main state (individual → main)
activeTab.subscribe(value => 
	uiState.update(state => ({ ...state, activeTab: value }))
);
imageProcessingExpanded.subscribe(value => 
	uiState.update(state => ({ ...state, imageProcessingExpanded: value }))
);
coinParametersExpanded.subscribe(value => 
	uiState.update(state => ({ ...state, coinParametersExpanded: value }))
);
heightmapPositioningExpanded.subscribe(value => 
	uiState.update(state => ({ ...state, heightmapPositioningExpanded: value }))
);

// Sync main state with individual stores (main → individual)
uiState.subscribe(state => {
	activeTab.set(state.activeTab);
	imageProcessingExpanded.set(state.imageProcessingExpanded);
	coinParametersExpanded.set(state.coinParametersExpanded);
	heightmapPositioningExpanded.set(state.heightmapPositioningExpanded);
});

// Actions for updating UI state
export const uiActions = {
	setActiveTab: (tab: UIState['activeTab']) => 
		uiState.update(state => ({ ...state, activeTab: tab })),
	
	setImageProcessingExpanded: (expanded: boolean) => 
		uiState.update(state => ({ ...state, imageProcessingExpanded: expanded })),
	
	setCoinParametersExpanded: (expanded: boolean) => 
		uiState.update(state => ({ ...state, coinParametersExpanded: expanded })),
	
	setHeightmapPositioningExpanded: (expanded: boolean) => 
		uiState.update(state => ({ ...state, heightmapPositioningExpanded: expanded })),
	
	reset: () => uiState.set(initialUIState)
};