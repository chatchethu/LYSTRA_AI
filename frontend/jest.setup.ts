import "@testing-library/jest-dom";

jest.mock("next/navigation", () => ({
    useRouter: () => ({
        push: jest.fn(),
        replace: jest.fn(),
        back: jest.fn(),
        forward: jest.fn(),
        refresh: jest.fn(),
        prefetch: jest.fn(),
    }),
    useSearchParams: () => new URLSearchParams(),
    usePathname: () => "/chat",
}));

Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: jest.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
    })),
});

class MockBroadcastChannel {
    name: string;

    constructor(name: string) {
        this.name = name;
    }

    postMessage() { }
    close() { }
    addEventListener() { }
    removeEventListener() { }
}

global.BroadcastChannel = MockBroadcastChannel as unknown as typeof BroadcastChannel;
