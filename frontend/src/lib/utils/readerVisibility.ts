export interface ViewportRect {
	left: number;
	right: number;
}

// Detect when the current reading element is outside (or spilling past) the visible page.
// When spread mode is active (two columns), pass the spreadWidth to avoid turning when only moving to column 2.
export function shouldTurnPageFromGeometry(
	rect: ViewportRect,
	viewportWidth: number,
	buffer = 20,
	spreadWidth?: number
): boolean {
	const effectiveWidth =
		spreadWidth && spreadWidth > viewportWidth * 0.8 ? spreadWidth : viewportWidth;

	if (!rect || typeof rect.left !== 'number' || typeof rect.right !== 'number' || effectiveWidth <= 0) {
		return false;
	}

	// Turn if the element completely starts near/after the end of the spread.
	// IMPORTANT: In Epub.js (CSS Columns), elements spanning pages have 
	// rect.right far beyond the viewport. We must NOT turn the page 
	// just because it spills over, only if it strictly STARTS off-screen.
	const nearOrPastEnd = rect.left >= effectiveWidth - buffer;

	return nearOrPastEnd;
}
