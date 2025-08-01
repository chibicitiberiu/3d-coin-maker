// Dynamic Drag Feedback Controller
// Automatically adjusts processing frequency based on hardware capability and image complexity

import { browser } from '$app/environment';

export interface FeedbackMetrics {
	averageProcessingTime: number;
	queueLength: number;
	successRate: number;
	lastUpdateTime: number;
}

export class DragFeedbackController {
	private maxConcurrentWorkers: number;
	private currentFPS: number;
	private targetFPS = 5; // Desired FPS for immediate feedback (increased for low-res processing)
	private minFPS = 1; // Minimum FPS (1 second intervals)
	private maxFPS = 8; // Maximum FPS for very fast systems (increased for low-res)
	
	private processingTimes: number[] = [];
	private maxProcessingTimeHistory = 10;
	private pendingRequestCount = 0;
	
	// Timing control
	private lastRequestTime = 0;
	private currentInterval: number;
	
	constructor(maxWorkers = 2) {
		this.maxConcurrentWorkers = maxWorkers;
		this.currentFPS = this.targetFPS;
		this.currentInterval = 1000 / this.currentFPS;
		
		if (browser) {
			console.log(`DragFeedbackController initialized: ${maxWorkers} max workers, ${this.currentFPS}fps target`);
		}
	}
	
	/**
	 * Check if we should process a new request now
	 */
	shouldProcessNow(): boolean {
		const now = Date.now();
		const timeSinceLastRequest = now - this.lastRequestTime;
		
		// If we have no pending requests, always allow immediate processing
		if (this.pendingRequestCount === 0) {
			return true;
		}
		
		// Check if we have available worker capacity
		if (this.pendingRequestCount >= this.maxConcurrentWorkers) {
			if (browser) {
				console.log(`DragFeedbackController: Max workers (${this.maxConcurrentWorkers}) busy, skipping`);
			}
			return false;
		}
		
		// For subsequent requests, check if enough time has passed based on current FPS
		if (timeSinceLastRequest < this.currentInterval) {
			return false;
		}
		
		return true;
	}
	
	/**
	 * Calculate when the next request should be processed
	 */
	getNextProcessingDelay(): number {
		const now = Date.now();
		const timeSinceLastRequest = now - this.lastRequestTime;
		const remainingTime = Math.max(0, this.currentInterval - timeSinceLastRequest);
		
		return remainingTime;
	}
	
	/**
	 * Mark that a processing request has started
	 */
	markRequestStarted(): void {
		this.lastRequestTime = Date.now();
		this.pendingRequestCount++;
		if (browser) {
			console.log(`DragFeedbackController: Request started (${this.pendingRequestCount}/${this.maxConcurrentWorkers} workers busy)`);
		}
	}
	
	/**
	 * Mark that a processing request has completed and update metrics
	 */
	markRequestCompleted(processingTime: number, success: boolean): void {
		this.pendingRequestCount = Math.max(0, this.pendingRequestCount - 1);
		
		if (success) {
			// Track successful processing times
			this.processingTimes.push(processingTime);
			if (this.processingTimes.length > this.maxProcessingTimeHistory) {
				this.processingTimes.shift();
			}
			
			// Adjust FPS based on performance
			this.adjustFPS();
		}
		
		if (browser) {
			console.log(`DragFeedbackController: Request completed in ${processingTime}ms (${this.pendingRequestCount}/${this.maxConcurrentWorkers} workers busy)`);
		}
	}
	
	/**
	 * Cancel all pending requests (e.g., when drag ends)
	 */
	cancelAllRequests(): void {
		if (browser) {
			console.log(`DragFeedbackController: Canceling ${this.pendingRequestCount} pending requests`);
		}
		this.pendingRequestCount = 0;
	}
	
	/**
	 * Dynamically adjust FPS based on processing performance
	 */
	private adjustFPS(): void {
		if (this.processingTimes.length < 3) {
			return; // Need more data points
		}
		
		const averageProcessingTime = this.processingTimes.reduce((a, b) => a + b, 0) / this.processingTimes.length;
		const currentInterval = 1000 / this.currentFPS;
		
		// Calculate ideal FPS based on processing time and worker capacity
		// We want processing to complete before the next request, with some buffer
		const idealInterval = averageProcessingTime * 1.5; // 50% buffer
		const idealFPS = Math.min(1000 / idealInterval, this.maxFPS);
		
		// Also consider worker capacity - if we have multiple workers, we can go faster
		const capacityBasedFPS = this.maxConcurrentWorkers * idealFPS;
		const targetFPS = Math.min(capacityBasedFPS, this.maxFPS);
		
		// Smooth adjustment - move towards target gradually
		const adjustment = 0.3; // 30% adjustment per update
		const newFPS = this.currentFPS + (targetFPS - this.currentFPS) * adjustment;
		
		// Clamp to min/max bounds
		this.currentFPS = Math.max(this.minFPS, Math.min(this.maxFPS, newFPS));
		this.currentInterval = 1000 / this.currentFPS;
		
		if (browser) {
			console.log(`DragFeedbackController: Adjusted FPS ${this.currentFPS.toFixed(1)} (avg processing: ${averageProcessingTime.toFixed(0)}ms, ${this.maxConcurrentWorkers} workers)`);
		}
	}
	
	/**
	 * Get current metrics for debugging
	 */
	getMetrics(): FeedbackMetrics {
		const averageProcessingTime = this.processingTimes.length > 0 
			? this.processingTimes.reduce((a, b) => a + b, 0) / this.processingTimes.length 
			: 0;
			
		return {
			averageProcessingTime,
			queueLength: this.pendingRequestCount,
			successRate: 1.0, // TODO: Track failure rate
			lastUpdateTime: this.lastRequestTime
		};
	}
	
	/**
	 * Get current FPS for display/debugging
	 */
	getCurrentFPS(): number {
		return this.currentFPS;
	}
	
	/**
	 * Reset controller state (e.g., when switching images)
	 */
	reset(): void {
		this.processingTimes = [];
		this.pendingRequestCount = 0;
		this.currentFPS = this.targetFPS;
		this.currentInterval = 1000 / this.currentFPS;
		this.lastRequestTime = 0;
		if (browser) {
			console.log('DragFeedbackController: Reset to default state');
		}
	}
}