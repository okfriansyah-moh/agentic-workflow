// Import this policy after the project's TypeScript and Svelte parser configuration.
export default [{
  ignores: ['**/generated/**', '**/build/**', '**/dist/**', '**/node_modules/**'],
}, {
  files: ['**/*.{js,mjs,cjs,ts,tsx,svelte}'],
  rules: {
    'max-lines-per-function': ['error', { max: 50, skipBlankLines: true, skipComments: true, IIFEs: true }],
    complexity: ['error', 10],
    'max-depth': ['error', 3],
  },
}];
