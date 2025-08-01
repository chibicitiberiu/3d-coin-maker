export interface RulerMark {
	position: number;
	label: string;
	major: boolean;
}

export interface CoordinateService {
	generateRulerMarks: (containerSize: number, coinSizeMM: number, pixelsPerMM: number) => RulerMark[];
}

export function createCoordinateService(): CoordinateService {
	
	/**
	 * Calculate ruler marks based on coin size and pixel density
	 * @param containerSize - Total container size in pixels
	 * @param coinSizeMM - Coin size in millimeters  
	 * @param pixelsPerMM - Pixels per millimeter ratio
	 * @returns Array of ruler marks with positions and labels
	 */
	function generateRulerMarks(containerSize: number, coinSizeMM: number, pixelsPerMM: number): RulerMark[] {
		const marks: RulerMark[] = [];
		
		// The canvas starts at 30px offset from ruler origin
		const rulerOffset = 30;
		const canvasSize = containerSize - rulerOffset; // Actual canvas size
		const canvasCenterInRuler = rulerOffset + canvasSize / 2;
		
		// Generate marks every 10mm (major) and 5mm (minor) for better spacing
		const maxRangeMM = Math.floor(canvasSize / pixelsPerMM / 2);
		
		for (let mm = -maxRangeMM; mm <= maxRangeMM; mm += 5) {
			const position = canvasCenterInRuler + (mm * pixelsPerMM);
			if (position >= rulerOffset && position <= containerSize) {
				const isMajor = mm % 10 === 0;
				const label = isMajor ? `${mm}mm` : '';
				marks.push({ position, label, major: isMajor });
			}
		}
		
		return marks;
	}

	return {
		generateRulerMarks
	};
}

// Create singleton instance
export const coordinateService = createCoordinateService();