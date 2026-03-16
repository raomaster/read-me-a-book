import { describe, expect, it } from 'vitest';
import { shouldTurnPageFromGeometry } from './readerVisibility';

const rect = (left: number, right: number) => ({ left, right });

describe('shouldTurnPageFromGeometry', () => {
	it('returns false when element fits inside the viewport', () => {
		expect(shouldTurnPageFromGeometry(rect(10, 400), 800)).toBe(false);
	});

	it('returns true when the element is completely to the right of the viewport', () => {
		expect(shouldTurnPageFromGeometry(rect(820, 1020), 800)).toBe(true);
	});

	it('returns true when the element starts on the current page but spills into the next', () => {
		// Regression: long paragraphs spanning multiple columns should trigger a turn.
		expect(shouldTurnPageFromGeometry(rect(0, 1050), 800)).toBe(true);
	});

	it('does not turn when moving to column 2 inside the same spread', () => {
		// Two-column spread: viewportWidth=400, spreadWidth=800, element in column 2
		expect(shouldTurnPageFromGeometry(rect(420, 780), 400, 20, 800)).toBe(false);
	});

	it('turns when element is near end of spread', () => {
		expect(shouldTurnPageFromGeometry(rect(980, 1020), 1000, 20, 1000)).toBe(true);
	});
});
