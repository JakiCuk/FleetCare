// Pulls in @testing-library/jest-dom's Vitest matcher type augmentations
// (toBeInTheDocument, toHaveClass, ...) so `tsc --noEmit` recognizes them on
// Vitest's `expect`. Runtime registration happens in ./setup.ts.
import '@testing-library/jest-dom/vitest';
