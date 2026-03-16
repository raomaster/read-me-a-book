import { shouldTurnPageFromGeometry, type ViewportRect } from './readerVisibility';

export interface PageTurnContext {
	elementIndex?: number;
	endIndex?: number;
	lastNavigationTime: number;
	now: number;
	debounceMs?: number;
	rect?: ViewportRect;
	element?: HTMLElement;
	viewportWidth?: number;
	spreadWidth?: number;
	geometryBuffer?: number;
}

/**
 * Decide if we should trigger a page turn (or jump) for the current reading element.
 * - Turns immediately when the element is no longer visible in the viewport.
 * - Otherwise prefers location index comparison (elementIndex > endIndex).
 * - Falls back to geometry only if indexes are unavailable.
 * - Respects a debounce window to avoid double-turns.
 */
export function needsPageTurn(ctx: PageTurnContext): boolean {
	const {
		elementIndex,
		endIndex,
		lastNavigationTime,
		now,
		debounceMs = 250,
		rect,
		viewportWidth,
		spreadWidth,
		geometryBuffer
	} = ctx;

	if (now - lastNavigationTime < debounceMs) return false;

	const hasIndexes = Number.isFinite(elementIndex) && Number.isFinite(endIndex);
	const indexDelta = hasIndexes ? (elementIndex as number) - (endIndex as number) : 0;
	const buffer = geometryBuffer ?? 20;

	let isOffscreen = false;
	let fullyInvisible = false;

	if (ctx.element && ctx.element.getClientRects) {
		const rects = ctx.element.getClientRects();
		if (rects.length > 0) {
			isOffscreen = true;
			fullyInvisible = true;
			const effectiveWidth =
				spreadWidth && viewportWidth && spreadWidth > viewportWidth * 0.8 ? spreadWidth : viewportWidth;

			for (let i = 0; i < rects.length; i++) {
				const r = rects[i];
				if (effectiveWidth && r.left < effectiveWidth - buffer) {
					isOffscreen = false;
				}
				if (viewportWidth && !(r.right <= 0 || r.left >= viewportWidth)) {
					fullyInvisible = false;
				}
			}
		}
	} else if (rect && viewportWidth) {
		isOffscreen = shouldTurnPageFromGeometry(rect, viewportWidth, buffer, spreadWidth);
		fullyInvisible = rect.right <= 0 || rect.left >= viewportWidth;
	}

	// If the highlighted element is no longer visible, turn immediately.
	if (fullyInvisible) return true;

	if (hasIndexes) {
		if (indexDelta >= 0 && isOffscreen) return true;
		return false;
	}

	if (!hasIndexes && isOffscreen) {
		return true;
	}

	return false;
}
