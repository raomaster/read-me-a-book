import { describe, expect, it } from 'vitest';
import { buildReadingQueue, isElementOnScreen } from './reader-logic';

// Mock HTMLElement and DOMRect for testing
class MockRect {
	left: number;
	top: number;
	bottom: number;
	width: number;
	height: number;
	right: number;

	constructor(left: number, top: number, width: number, height: number) {
		this.left = left;
		this.top = top;
		this.width = width;
		this.height = height;
		this.bottom = top + height;
		this.right = left + width;
	}
}

type MockEl = {
	textContent: string;
	getClientRects: () => MockRect[];
	getBoundingClientRect: () => MockRect;
	closest: () => MockEl | null;
};

function createMockElement(textContent: string, rect: MockRect): MockEl {
	return {
		textContent,
		getClientRects: () => [rect],
		getBoundingClientRect: () => rect,
		closest: () => null // Simplified
	};
}

function createMockDoc(elements: MockEl[]): Document {
	return {
		querySelectorAll: () => elements
	} as unknown as Document;
}

describe('reader-logic', () => {
	it('builds a queue with only visible elements and marks next page start', () => {
		const el1 = createMockElement('Paragraph 1', new MockRect(10, 10, 100, 20));
		const el2 = createMockElement('Paragraph 2', new MockRect(850, 10, 100, 20));
		const doc = createMockDoc([el1, el2]);

		const result = buildReadingQueue(doc, 800, 600);

		expect(result.queue).toHaveLength(1);
		expect(result.queue[0]?.text).toBe('Paragraph 1');
		expect(result.nextPageStartElement).toBe(el2);
	});

	it('treats an element starting near the boundary as belonging to the next page', () => {
		const el3 = createMockElement('Paragraph 3', new MockRect(790, 10, 100, 20));
		const { queue, nextPageStartElement } = buildReadingQueue(createMockDoc([el3]), 800, 600);

		expect(queue).toHaveLength(0);
		expect(nextPageStartElement).toBe(el3);
	});

	it('detects on-screen/off-screen elements at runtime', () => {
		const el1 = createMockElement('Paragraph 1', new MockRect(10, 10, 100, 20));
		const el2 = createMockElement('Paragraph 2', new MockRect(850, 10, 100, 20));

		expect(isElementOnScreen(el1 as unknown as HTMLElement, 800)).toBe(true);
		expect(isElementOnScreen(el2 as unknown as HTMLElement, 800)).toBe(false);
	});
});
