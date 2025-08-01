# Coin Maker - Implementation Plan

A staged development plan for building a self-hostable web application that generates 3D printable coin STL files from user-uploaded images.

## Implementation Status (Last Updated: 2025-07-30)

**Current Stage: Stage 1 (MVP) - 95% Complete**

### ✅ Completed Features
- ✅ Complete frontend UI with responsive two-panel layout
- ✅ Image upload with drag & drop support and file validation
- ✅ Real-time image processing with Photon WASM + Canvas fallback
- ✅ All Stage 1 image processing controls (grayscale, brightness, contrast, gamma, invert)
- ✅ All Stage 1 coin parameters (shape, size, thickness, relief depth)
- ✅ Heightmap positioning controls (scale, offset, rotation)
- ✅ Three-tab interface (Original, Preprocessed, Final Result)
- ✅ STL viewer with Three.js and custom STL parser
- ✅ FastAPI backend with proper API endpoints
- ✅ Celery task queue for background processing
- ✅ OpenSCAD integration for STL generation
- ✅ File storage and cleanup system
- ✅ Rate limiting and IP-based controls
- ✅ Docker Compose deployment setup
- ✅ Redis integration for caching and task management
- ✅ Health check endpoint

### ✅ Recently Completed
- ✅ **Frontend-Backend integration** (MAJOR MILESTONE - fully implemented with real API calls)
- ✅ **Complete API integration** (upload, process, generate, download, status endpoints)
- ✅ **Parameter mapping and consistency** between frontend and backend
- ✅ **Environment configuration** for API base URLs

### 🚧 In Progress/Partial
- 🚧 Error handling and user feedback (90% - could use more sophisticated error messaging)

### ❌ Missing Features
- ❌ Comprehensive testing (unit, integration, e2e tests)
- ❌ Performance optimization
- ❌ Security hardening for production
- ❌ Component refactoring (break down monolithic +page.svelte)

**Next Priority:** Implement comprehensive testing suite to ensure production readiness.

## Technology Stack

- **Backend**: FastAPI
- **Frontend**: SvelteKit + TypeScript
- **Client-side Image Processing**: Photon WASM (primary), ImageMagick via WASM (fallback)
- **3D Generation**: OpenSCAD (command-line)
- **STL Viewing**: ViewSTL Plugin
- **Deployment**: Docker Compose
- **Storage**: Temporary filesystem storage (no database)
- **Task Queue**: Redis + Celery for background processing

---

## Stage 1: MVP (Minimum Viable Product)

### Core Functionality Specifications

#### File Upload Requirements
- **Supported formats**: PNG, JPEG, GIF, BMP, TIFF
- **Maximum file size**: 50MB
- **File validation**: MIME type checking, image header verification
- **Upload method**: Drag & drop with fallback to file picker
- **Progress indicator**: Real-time upload progress display

#### User Interface Layout
- **Two-section responsive layout**:
  - **Left panel** (30% width): Controls and parameters
  - **Right panel** (70% width): Three-tab interface
- **Right panel tabs**:
  - Tab 1: "Original Image" - Display uploaded image with zoom/pan controls
  - Tab 2: "Preprocessed Image" - Real-time preview of image processing
  - Tab 3: "Final Result" - STL viewer with 3D model (default active tab)
- **Mobile responsiveness**: Stack panels vertically on screens < 768px

#### Stage 1 Preprocessing Controls (Left Panel)

##### Image Processing Section
- **Grayscale Conversion**:
  - Method selector: RGB Average, Luminance (0.299R + 0.587G + 0.114B), Red Channel, Green Channel, Blue Channel, Custom weights
  - Real-time preview update on method change
- **Brightness Adjustment**:
  - Range: -100 to +100
  - Default: 0
  - Slider with numeric input field
- **Contrast Adjustment**:
  - Range: 0% to 300%
  - Default: 100%
  - Slider with numeric input field
- **Gamma Correction**:
  - Range: 0.1 to 5.0
  - Default: 1.0
  - Slider with numeric input field
- **Invert Colors**:
  - Checkbox toggle
  - Default: unchecked

##### Coin Parameters Section
- **Shape Selection**:
  - Options: Circle, Square, Hexagon, Octagon
  - Visual shape previews
  - Default: Circle
- **Coin Size (Diameter)**:
  - Slider range: 10mm to 100mm
  - Custom input field accepting any positive value
  - Default: 30mm
  - Unit display: millimeters
- **Coin Thickness**:
  - Slider range: 1mm to 10mm
  - Custom input field accepting any positive value
  - Default: 3mm
- **Relief Depth**:
  - Range: 0.1mm to thickness value
  - Default: 1mm
  - Description: "Maximum height of raised/recessed areas"

##### Heightmap Positioning Section
- **Scale**:
  - Range: 10% to 500%
  - Default: 100%
  - Description: "Size of heightmap relative to coin"
- **Offset X**:
  - Range: -50mm to +50mm (relative to coin center)
  - Default: 0mm
  - Description: "Horizontal position of heightmap on coin"
- **Offset Y**:
  - Range: -50mm to +50mm (relative to coin center)
  - Default: 0mm
  - Description: "Vertical position of heightmap on coin"
- **Rotation**:
  - Range: 0° to 360°
  - Default: 0°
  - Circular slider with numeric input

##### Action Buttons
- **"Update Preview"**: Refresh preprocessed image tab
- **"Generate STL"**: Create 3D model and switch to Final Result tab
- **"Download STL"**: Download generated file (enabled after successful generation)

#### Image Processing Pipeline Specifications

##### Browser Capability Detection
- **Primary**: Attempt Photon WASM initialization
- **Fallback**: Use ImageMagick WASM if Photon fails
- **Error handling**: Clear user notification if both fail
- **Performance**: Process images up to 4K resolution efficiently

##### Processing Chain
1. **Image loading**: Convert uploaded file to ImageData
2. **Grayscale conversion**: Apply selected algorithm
3. **Adjustments**: Apply brightness, contrast, gamma in sequence
4. **Inversion**: Apply if selected
5. **Export**: Convert to PNG for backend transmission

#### STL Viewer Specifications (Final Result Tab)

##### Viewer Features
- **3D rotation**: Mouse drag to rotate model
- **Zoom**: Mouse wheel or pinch gestures
- **Pan**: Right-click drag or two-finger drag
- **Auto-rotate toggle**: Optional continuous rotation
- **Reset view button**: Return to default camera position
- **Fullscreen option**: Expand viewer to full browser window

##### Model Display
- **Lighting**: Three-point lighting setup for clear detail visibility
- **Materials**: Matte metallic appearance with subtle reflections
- **Grid**: Optional reference grid in world space
- **Measurements**: Display coin dimensions on hover

#### Backend Processing Specifications

##### Temporary Storage System
- **Storage location**: `/tmp/coin_maker/` directory
- **File naming**: UUID-based with timestamp
- **Cleanup schedule**: Remove files older than 30 minutes every 5 minutes
- **File types stored**: Original image, processed heightmap, generated STL
- **Access control**: Files only accessible via generation ID

##### OpenSCAD Integration
- **Template system**: Modular SCAD templates for each shape type
- **Parameter injection**: Dynamic parameter substitution in templates
- **Process isolation**: Each generation runs in separate OpenSCAD process
- **Error capture**: Parse OpenSCAD errors and provide user-friendly messages
- **Timeout handling**: Kill processes running longer than 2 minutes

##### API Endpoint Specifications
- **POST /api/upload/**: Accept image file, return generation ID
- **POST /api/process/**: Process image with parameters, return processed image URL
- **POST /api/generate/**: Generate STL with coin parameters, return status
- **GET /api/status/{id}/**: Return current processing status and progress
- **GET /api/download/{id}/stl**: Serve STL file with proper headers
- **GET /api/preview/{id}**: Serve processed heightmap image

##### Rate Limiting
- **Per IP limits**: 20 generations per hour, 5 concurrent processes
- **File size limits**: 50MB per upload
- **Process limits**: Maximum 3 concurrent OpenSCAD processes
- **Cleanup on limits**: Clear oldest files when storage exceeds 1GB

---

## Stage 2: Enhanced Preprocessing & Custom Shapes

### New Features

#### Advanced Image Processing
- **Cropping tool**: Visual rectangle selector with aspect ratio constraints
- **Image filters**: Blur, sharpen, edge detection, emboss
- **Histogram display**: Live histogram of grayscale values
- **Auto-level**: Automatic contrast stretching to full range
- **Noise reduction**: Gaussian blur with configurable radius

#### Custom SVG Shapes
- **SVG upload**: Support for simple SVG path files
- **Shape validation**: Ensure closed paths suitable for coin perimeter
- **SVG editor**: Basic path editing tools for uploaded shapes
- **Shape library**: Save and reuse custom shapes across sessions

#### Enhanced Coin Parameters
- **Base thickness**: Separate from total thickness for raised/recessed effects
- **Edge style**: Options for chamfered, rounded, or sharp edges
- **Dual-sided**: Support for different heightmaps on front and back
- **Text addition**: Simple text embossing around coin perimeter

### UI Enhancements

#### Left Panel Additions
- **Processing tab system**: Organize controls into collapsible sections
- **Preset management**: Save and load parameter combinations
- **Real-time updates**: Live preview updates as parameters change
- **Parameter linking**: Lock aspect ratios, scale multiple parameters together

#### Advanced Preview Features
- **Overlay comparisons**: Side-by-side or overlay comparison views
- **Processing history**: Undo/redo for parameter changes
- **Export options**: Save processed images separately
- **Print simulation**: Preview how model will appear when 3D printed

---

## Stage 3: Advanced STL Features & Batch Processing

### Enhanced STL Generation

#### Multiple Export Formats
- **STL variants**: ASCII and binary STL export options
- **OBJ export**: Include materials and UV mapping
- **3MF support**: Microsoft 3D Manufacturing Format
- **Quality settings**: High/medium/low polygon density options

#### Advanced Model Features
- **Support structures**: Automatic support generation preview
- **Manifold validation**: Check and fix non-manifold geometry
- **Model optimization**: Reduce polygon count while preserving detail
- **Scale verification**: Ensure model dimensions match specifications

#### Batch Processing System
- **Multiple file upload**: Process multiple images simultaneously
- **Parameter templates**: Apply same settings to multiple images
- **Queue management**: Track progress of multiple generations
- **Batch download**: ZIP archive of all generated STL files

### Enhanced STL Viewer
- **Measurement tools**: Distance, angle, and area measurement
- **Cross-sections**: View internal geometry with cutting planes
- **Animation**: Rotate model automatically for presentation
- **Print analysis**: Overhang detection, layer height recommendations

---

## Stage 4: Performance Optimization & Polish

### Performance Enhancements

#### Client-side Optimization
- **WebWorker processing**: Move heavy image processing to background threads
- **Progressive loading**: Stream large images during processing
- **Memory management**: Efficient handling of large image files
- **Caching strategy**: Cache processed images for parameter adjustments

#### Server Optimization
- **Process pooling**: Reuse OpenSCAD processes for faster generation
- **Parallel processing**: Handle multiple requests simultaneously
- **Resource monitoring**: Track CPU, memory, and disk usage
- **Adaptive quality**: Adjust processing based on available resources

### User Experience Polish

#### Advanced UI Features
- **Keyboard shortcuts**: Power user navigation and control
- **Accessibility**: Full screen reader and keyboard navigation support
- **Mobile optimization**: Touch-friendly controls and gestures
- **Progressive web app**: Offline functionality and app-like experience

#### Error Handling & Feedback
- **Detailed error messages**: Context-specific help for processing failures
- **Progress visualization**: Detailed progress bars with estimated completion times
- **Recovery options**: Retry failed operations with suggested parameter adjustments
- **Help system**: Integrated tooltips and documentation

---

## Deployment Specifications

### Docker Container Requirements

#### Frontend Container
- **Base image**: Node.js Alpine for minimal size
- **Build process**: SvelteKit static build with adapter-static
- **Served by**: nginx with gzip compression and caching headers
- **Environment**: Production-optimized with source maps disabled

#### Backend Container
- **Base image**: Python slim with OpenSCAD binary
- **Dependencies**: PIL, requests, celery, redis-py
- **Process management**: Gunicorn with multiple workers
- **Health checks**: Endpoint monitoring and automatic restart

#### Storage & Networking
- **Volume mounting**: Persistent storage for temporary files
- **Network isolation**: Internal communication between containers
- **Port exposure**: Only reverse proxy ports exposed externally
- **SSL termination**: nginx with Let's Encrypt certificate automation

### Self-Hosting Configuration

#### Resource Requirements
- **Minimum specs**: 2 CPU cores, 4GB RAM, 20GB storage
- **Recommended specs**: 4 CPU cores, 8GB RAM, 100GB storage
- **Scaling considerations**: Additional workers for high-traffic scenarios

#### Environment Configuration
- **Rate limiting**: Configurable limits based on server capacity
- **File retention**: Adjustable cleanup intervals and storage limits
- **Processing limits**: Configurable concurrent operation limits
- **Monitoring**: Optional metrics collection and alerting

#### Security Features
- **Input sanitization**: File type validation and content scanning
- **Process isolation**: Sandboxed OpenSCAD execution
- **Network security**: Internal service communication only
- **Access logging**: Comprehensive request and error logging

---

## Quality Assurance Specifications

### Testing Requirements

#### Frontend Testing
- **Unit tests**: Component logic and image processing functions
- **Integration tests**: End-to-end user workflows
- **Cross-browser testing**: Chrome, Firefox, Safari, Edge compatibility
- **Performance testing**: Large file handling and memory usage

#### Backend Testing
- **API testing**: All endpoint functionality and error cases
- **OpenSCAD integration**: Template generation and parameter handling
- **File handling**: Upload, processing, and cleanup operations
- **Load testing**: Concurrent user and high-volume scenarios

### Performance Benchmarks
- **Image processing**: Sub-second response for images up to 4K resolution
- **STL generation**: Complete coin generation within 30 seconds
- **Memory usage**: Maximum 512MB per processing operation
- **Concurrent users**: Support for 10 simultaneous generations