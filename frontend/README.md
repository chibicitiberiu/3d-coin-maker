# Coin Maker Frontend

A modern web frontend for the Coin Maker application built with SvelteKit, TypeScript, and Three.js.

## Features

- **Responsive Design**: Works on desktop and mobile devices
- **Image Processing**: Client-side image processing with Photon WASM and Canvas API fallback
- **Interactive 3D Viewer**: Three.js-based STL viewer with controls
- **Real-time Preview**: Live image processing as parameters change
- **Modern UI**: Clean interface with PicoCSS framework

## Technology Stack

- **Framework**: SvelteKit with TypeScript
- **Styling**: PicoCSS (lightweight CSS framework)
- **Icons**: Lucide Svelte
- **Image Processing**: Photon WASM with Canvas API fallback
- **3D Rendering**: Three.js for STL visualization
- **Package Manager**: pnpm
- **Build**: Vite with static adapter

## Development

### Prerequisites

- Node.js 20+
- pnpm (recommended) or npm

### Setup

```bash
# Install dependencies
pnpm install

# Start development server
pnpm run dev

# The app will be available at http://localhost:5173
```

### Available Scripts

- `pnpm run dev` - Start development server
- `pnpm run build` - Build for production
- `pnpm run preview` - Preview production build
- `pnpm run check` - Run TypeScript and Svelte checks

## Docker

### Production Build

```bash
# Build the Docker image
docker build -t coin-maker-frontend .

# Run the container
docker run -p 3000:80 coin-maker-frontend
```

### Development with Docker

```bash
# Build development image
docker build -f Dockerfile.dev -t coin-maker-frontend-dev .

# Run development container
docker run -p 5173:5173 -v $(pwd):/app -v /app/node_modules coin-maker-frontend-dev
```

### Docker Compose

Production:
```bash
docker compose up frontend
```

Development:
```bash
docker compose -f docker-compose.dev.yml up frontend-dev
```

## Architecture

### Component Structure

- `src/routes/+layout.svelte` - Main layout with navigation
- `src/routes/+page.svelte` - Main application page
- `src/routes/about/+page.svelte` - About page
- `src/lib/STLViewer.svelte` - 3D STL viewer component
- `src/lib/imageProcessor.ts` - Image processing logic

### Key Features

#### Image Processing Pipeline
1. File upload with drag & drop support
2. Client-side processing with Photon WASM
3. Real-time parameter adjustment
4. Canvas API fallback for compatibility

#### User Interface
- **Left Panel (30%)**: Control panels for image processing, coin parameters, and positioning
- **Right Panel (70%)**: Tabbed interface showing original, processed, and 3D result
- **Mobile Responsive**: Stacked layout on screens < 768px

#### 3D Viewer
- Interactive Three.js-based STL viewer
- Mouse controls for rotation and zoom
- Control buttons for common operations
- Auto-rotation toggle

## Configuration

### Environment Variables

The frontend uses environment-specific configuration files:

- **Development**: `config/frontend.dev.env`
- **Production**: `config/frontend.env`

Key configuration options:
- `VITE_API_BASE_URL` - Backend API endpoint
- `VITE_MAX_IMAGE_SIZE` - Maximum upload size in bytes
- `VITE_DEBOUNCE_DELAY` - Parameter change debounce delay
- `VITE_DEBUG_MODE` - Enable/disable debug features
- `VITE_DEV_SERVER_PORT` - Development server port
- `VITE_BUILD_SOURCEMAP` - Generate sourcemaps for builds

### Build Configuration

## Browser Support

- Modern browsers with ES2020+ support
- WebAssembly support for optimal image processing
- Canvas API for fallback image processing
- WebGL for 3D rendering
