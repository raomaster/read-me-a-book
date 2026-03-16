export interface QueueItem {
    text: string;
    elements: HTMLElement[];
    audioUrlPromise?: Promise<string>;
}

export interface QueueResult {
    queue: QueueItem[];
    nextPageStartElement: HTMLElement | null;
}

/**
 * Builds the reading queue for the current page based on strict geometric visibility.
 * @param doc The document containing the text elements.
 * @param viewportWidth The width of the visible page area (viewerElement.clientWidth).
 * @param viewportHeight The height of the visible page area.
 * @param startFromElement Optional element to start scanning from (for clicks).
 */
export function buildReadingQueue(
    doc: Document,
    viewportWidth: number,
    viewportHeight: number,
    startFromElement?: HTMLElement
): QueueResult {
    const allElements = Array.from(
        doc.querySelectorAll('p, h1, h2, h3, h4, h5, h6, li, blockquote, pre')
    ) as HTMLElement[];

    let startIndex = 0;
    if (startFromElement) {
        const container = startFromElement.closest(
            'p, h1, h2, h3, h4, h5, h6, li, blockquote, pre'
        ) as HTMLElement;
        if (container) {
            startIndex = allElements.indexOf(container);
            if (startIndex === -1) startIndex = 0;
        }
    }

    const queue: QueueItem[] = [];
    let nextPageStartElement: HTMLElement | null = null;

    console.log(`[ReaderLogic] Scanning ${allElements.length} elements. Viewport: ${viewportWidth}x${viewportHeight}`);

    for (let i = startIndex; i < allElements.length; i++) {
        const el = allElements[i];
        const rects = el.getClientRects();

        if (rects.length === 0) continue;
        const rect = rects[0];

        // CRITICAL: Page Boundary Check
        // If the element starts after the viewport width (with a small tolerance),
        // it belongs to the next page.
        if (rect.left >= viewportWidth - 20) {
            console.log(`[ReaderLogic] Boundary hit. Element "${el.textContent?.slice(0, 15)}..." at ${rect.left}px > ${viewportWidth - 20}px`);
            nextPageStartElement = el;
            break;
        }

        // VISIBILITY CHECK
        // Must be within the current page's vertical bounds and start within horizontal bounds.
        const isVisible =
            rect.left >= -20 &&
            rect.bottom > 0 &&
            rect.top < viewportHeight &&
            (el.textContent?.trim().length ?? 0) > 0;

        if (isVisible) {
            const txt = el.textContent?.trim() || '';
            const MAX_CHUNK = 800;

            if (txt.length <= MAX_CHUNK) {
                queue.push({ text: txt, elements: [el] });
            } else {
                let remaining = txt;
                while (remaining.length) {
                    let sliceEnd = remaining.lastIndexOf(' ', MAX_CHUNK);
                    if (sliceEnd < MAX_CHUNK * 0.6) sliceEnd = MAX_CHUNK;
                    if (sliceEnd === -1 || sliceEnd === 0) sliceEnd = Math.min(remaining.length, MAX_CHUNK);
                    queue.push({
                        text: remaining.slice(0, sliceEnd).trim(),
                        elements: [el]
                    });
                    remaining = remaining.slice(sliceEnd).trim();
                }
            }
        }
    }

    return { queue, nextPageStartElement };
}

/**
 * Runtime check to verify if an element is still safe to read.
 */
export function isElementOnScreen(el: HTMLElement, viewportWidth: number): boolean {
    const rect = el.getBoundingClientRect();
    // Strict check: if it starts off-screen, it's off-screen.
    return rect.left < viewportWidth - 20;
}
