import { writable, derived } from 'svelte/store';

// Coin parameters state
export interface CoinParameters {
	coinShape: 'circle' | 'square' | 'hexagon' | 'octagon';
	coinSize: number; // diameter in mm
	coinThickness: number; // in mm
	reliefDepth: number; // in mm
}

export interface HeightmapPositioning {
	heightmapScale: number; // percentage
	offsetX: number; // percentage of coin size
	offsetY: number; // percentage of coin size
	rotation: number; // degrees
}

export interface CoinParametersState extends CoinParameters, HeightmapPositioning {
	// View scaling
	pixelsPerMM: number; // pixels per millimeter - controls zoom level
}

const initialCoinParametersState: CoinParametersState = {
	// Coin parameters
	coinShape: 'circle',
	coinSize: 30,
	coinThickness: 3,
	reliefDepth: 1,
	
	// Heightmap positioning
	heightmapScale: 100,
	offsetX: 0,
	offsetY: 0,
	rotation: 0,
	
	// View scaling
	pixelsPerMM: 4
};

export const coinParametersState = writable<CoinParametersState>(initialCoinParametersState);

// Individual stores for reactive bindings - these need to be writable for two-way binding
export const coinShape = writable(initialCoinParametersState.coinShape);
export const coinSize = writable(initialCoinParametersState.coinSize);
export const coinThickness = writable(initialCoinParametersState.coinThickness);
export const reliefDepth = writable(initialCoinParametersState.reliefDepth);
export const heightmapScale = writable(initialCoinParametersState.heightmapScale);
export const offsetX = writable(initialCoinParametersState.offsetX);
export const offsetY = writable(initialCoinParametersState.offsetY);
export const rotation = writable(initialCoinParametersState.rotation);
export const pixelsPerMM = writable(initialCoinParametersState.pixelsPerMM);

// Sync individual stores with main state (individual → main)
coinShape.subscribe(value => 
	coinParametersState.update(state => ({ ...state, coinShape: value }))
);
coinSize.subscribe(value => 
	coinParametersState.update(state => ({ ...state, coinSize: value }))
);
coinThickness.subscribe(value => 
	coinParametersState.update(state => ({ ...state, coinThickness: value }))
);
reliefDepth.subscribe(value => 
	coinParametersState.update(state => ({ ...state, reliefDepth: value }))
);
heightmapScale.subscribe(value => 
	coinParametersState.update(state => ({ ...state, heightmapScale: value }))
);
offsetX.subscribe(value => 
	coinParametersState.update(state => ({ ...state, offsetX: value }))
);
offsetY.subscribe(value => 
	coinParametersState.update(state => ({ ...state, offsetY: value }))
);
rotation.subscribe(value => 
	coinParametersState.update(state => ({ ...state, rotation: value }))
);
pixelsPerMM.subscribe(value => 
	coinParametersState.update(state => ({ ...state, pixelsPerMM: value }))
);

// Sync main state with individual stores (main → individual)
coinParametersState.subscribe(state => {
	coinShape.set(state.coinShape);
	coinSize.set(state.coinSize);
	coinThickness.set(state.coinThickness);
	reliefDepth.set(state.reliefDepth);
	heightmapScale.set(state.heightmapScale);
	offsetX.set(state.offsetX);
	offsetY.set(state.offsetY);
	rotation.set(state.rotation);
	pixelsPerMM.set(state.pixelsPerMM);
});

// Actions for updating coin parameters state
export const coinParametersActions = {
	setCoinShape: (shape: CoinParameters['coinShape']) => 
		coinParametersState.update(state => ({ ...state, coinShape: shape })),
	
	setCoinSize: (size: number) => 
		coinParametersState.update(state => ({ ...state, coinSize: size })),
	
	setCoinThickness: (thickness: number) => 
		coinParametersState.update(state => ({ ...state, coinThickness: thickness })),
	
	setReliefDepth: (depth: number) => 
		coinParametersState.update(state => ({ ...state, reliefDepth: depth })),
	
	setHeightmapScale: (scale: number) => 
		coinParametersState.update(state => ({ ...state, heightmapScale: scale })),
	
	setOffsetX: (x: number) => 
		coinParametersState.update(state => ({ ...state, offsetX: x })),
	
	setOffsetY: (y: number) => 
		coinParametersState.update(state => ({ ...state, offsetY: y })),
	
	setRotation: (rotation: number) => 
		coinParametersState.update(state => ({ ...state, rotation })),
	
	setPixelsPerMM: (pixels: number) => 
		coinParametersState.update(state => ({ ...state, pixelsPerMM: pixels })),
	
	updateCoinParameters: (params: Partial<CoinParameters>) => 
		coinParametersState.update(state => ({ ...state, ...params })),
	
	updateHeightmapPositioning: (params: Partial<HeightmapPositioning>) => 
		coinParametersState.update(state => ({ ...state, ...params })),
	
	reset: () => coinParametersState.set(initialCoinParametersState)
};