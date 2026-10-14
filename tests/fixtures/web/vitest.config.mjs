import { defineConfig } from 'vitest/config';
export default defineConfig({ test: {
  coverage: { include: ['src/counter.ts'], reporter: ['text', 'lcov'], thresholds: { lines: 80 } },
} });
