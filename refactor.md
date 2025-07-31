# Component Refactoring Plan

The current `+page.svelte` file is doing too much and should be broken down into logical components for better maintainability, testability, and collaboration.

## Current Issues
- Single 1600+ line file handling everything
- Mixed concerns (UI, state management, image processing, canvas drawing)
- Hard to test individual features
- Difficult for multiple developers to work on

## Proposed Component Structure

### 1. **`CoinMakerApp.svelte`** - Main layout and state management
- App-wide state management
- Layout structure (2-column grid)
- State coordination between components

### 2. **`ControlsPanel.svelte`** - Left sidebar with all controls
- Upload controls
- All parameter controls
- Generate STL button
- Scrollable content area

### 3. **`ImageViewer.svelte`** - Right side with tabs and viewers
- Tab navigation (Original, Prepared, Result)
- Content switching logic
- Tab-specific viewers

### 4. **Control Components:**
- **`ImageUpload.svelte`** - File upload controls and status
- **`ImageProcessingControls.svelte`** - Grayscale, brightness, contrast, gamma, invert
- **`CoinParameterControls.svelte`** - Shape, size, thickness, relief depth
- **`HeightmapPositioningControls.svelte`** - Scale, offset X/Y, rotation

### 5. **Viewer Components:**
- **`OriginalImageViewer.svelte`** - Original image display with zoom/pan
- **`PreparedImageViewer.svelte`** - Canvas-based prepared image with rulers, grid, axes
- **`ResultViewer.svelte`** - STL download and preview

### 6. **Utility Components:**
- **`RulerComponent.svelte`** - Reusable ruler with marks
- **`CanvasRenderer.svelte`** - Canvas drawing utilities
- **`ImageProcessor.svelte`** - Image processing logic wrapper

## State Management Options

### Option 1: Svelte Stores (Recommended)
```typescript
// stores/coinMakerStore.ts
export const imageState = writable({
  uploadedImageUrl: null,
  processedImageData: null,
  // ... other image state
});

export const coinParameters = writable({
  shape: 'circle',
  size: 30,
  thickness: 3,
  // ... other parameters
});

export const processingState = writable({
  isUploading: false,
  isProcessing: false,
  isGenerating: false
});
```

### Option 2: Context API
- Use Svelte's context for passing state down
- Good for avoiding prop drilling

### Option 3: Props Drilling
- Simple but can get messy with deep nesting
- Not recommended for this scale

## Migration Strategy

### Phase 1: Extract Control Components
1. Create `ControlsPanel.svelte`
2. Extract `ImageProcessingControls.svelte`
3. Extract `CoinParameterControls.svelte`
4. Extract `HeightmapPositioningControls.svelte`

### Phase 2: Extract Viewer Components
1. Create `ImageViewer.svelte`
2. Extract `PreparedImageViewer.svelte` (with canvas logic)
3. Extract `OriginalImageViewer.svelte`
4. Extract `ResultViewer.svelte`

### Phase 3: Create Utility Components
1. Extract `RulerComponent.svelte`
2. Create reusable canvas utilities
3. Extract image processing logic

### Phase 4: State Management
1. Implement Svelte stores
2. Replace props with store subscriptions
3. Clean up state management

## Benefits After Refactoring

- **Maintainability**: Each component has single responsibility
- **Reusability**: Components can be reused or easily modified
- **Testing**: Much easier to unit test individual components
- **Performance**: Better optimization opportunities with granular reactivity
- **Collaboration**: Multiple developers can work on different components
- **Type Safety**: Better TypeScript support with smaller, focused components
- **Bundle Splitting**: Potential for better code splitting

## Files to Create

```
src/lib/components/
├── CoinMakerApp.svelte
├── controls/
│   ├── ControlsPanel.svelte
│   ├── ImageUpload.svelte
│   ├── ImageProcessingControls.svelte
│   ├── CoinParameterControls.svelte
│   └── HeightmapPositioningControls.svelte
├── viewers/
│   ├── ImageViewer.svelte
│   ├── OriginalImageViewer.svelte
│   ├── PreparedImageViewer.svelte
│   └── ResultViewer.svelte
└── ui/
    ├── RulerComponent.svelte
    └── CanvasRenderer.svelte

src/lib/stores/
├── coinMakerStore.ts
├── imageStore.ts
└── processingStore.ts
```

---

**Note**: This refactoring should be done after fixing current bugs to avoid introducing new issues during the migration.