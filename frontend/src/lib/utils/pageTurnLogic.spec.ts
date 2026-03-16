import { describe, expect, it } from 'vitest';
import { needsPageTurn } from './pageTurnLogic';

const now = 1_000_000;

describe('needsPageTurn', () => {
	it('turns when element index is well after end index (delta > 1)', () => {
		expect(
			needsPageTurn({
				elementIndex: 12,
				endIndex: 10,
				lastNavigationTime: now - 1000,
				now
			})
		).toBe(true);
	});

	it('does not turn when element is within the same page window', () => {
		expect(
			needsPageTurn({
				elementIndex: 10,
				endIndex: 10,
				lastNavigationTime: now - 1000,
				now
			})
		).toBe(false);
	});

	it('turns when delta is 1 (next location) and off-screen', () => {
		expect(
			needsPageTurn({
				elementIndex: 11,
				endIndex: 10,
				rect: { left: 820, right: 1020 },
				viewportWidth: 800,
				spreadWidth: 800,
				geometryBuffer: 20,
				lastNavigationTime: now - 1000,
				now
			})
		).toBe(true);
	});

	it('turns immediately when element is fully invisible to the left or right', () => {
		expect(
			needsPageTurn({
				elementIndex: 10,
				endIndex: 10,
				rect: { left: -5, right: -1 },
				viewportWidth: 800,
				spreadWidth: 800,
				lastNavigationTime: now - 1000,
				now
			})
		).toBe(true);
		expect(
			needsPageTurn({
				elementIndex: 10,
				endIndex: 10,
				rect: { left: 801, right: 820 },
				viewportWidth: 800,
				spreadWidth: 800,
				lastNavigationTime: now - 1000,
				now
			})
		).toBe(true);
	});

	it('does not turn when delta is 1 but element still on-screen', () => {
		expect(
			needsPageTurn({
				elementIndex: 10.4,
				endIndex: 10,
				rect: { left: 100, right: 700 },
				viewportWidth: 800,
				spreadWidth: 800,
				geometryBuffer: 20,
				lastNavigationTime: now - 1000,
				now
			})
		).toBe(false);
	});

	it('turns when indexes are equal but element is off-screen', () => {
		expect(
			needsPageTurn({
				elementIndex: 10,
				endIndex: 10,
				rect: { left: 820, right: 1020 },
				viewportWidth: 800,
				spreadWidth: 800,
				geometryBuffer: 20,
				lastNavigationTime: now - 1000,
				now
			})
		).toBe(true);
	});

	it('respects debounce window to avoid double turns', () => {
		expect(
			needsPageTurn({
				elementIndex: 11,
				endIndex: 10,
				lastNavigationTime: now - 100,
				now,
				debounceMs: 250
			})
		).toBe(false);
	});

	it('falls back to geometry when off-screen in spread', () => {
		expect(
			needsPageTurn({
				rect: { left: 820, right: 1020 },
				viewportWidth: 800,
				spreadWidth: 800,
				lastNavigationTime: now - 1000,
				now
			})
		).toBe(true);
	});

	it('does not turn when element fits within spread geometry', () => {
		expect(
			needsPageTurn({
				rect: { left: 100, right: 700 },
				viewportWidth: 800,
				spreadWidth: 800,
				lastNavigationTime: now - 1000,
				now
			})
		).toBe(false);
	});
});
