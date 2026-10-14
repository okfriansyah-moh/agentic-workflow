module.exports = {
  forbidden: [{ name: 'no-cycles', severity: 'error', from: {}, to: { circular: true } }],
  options: { doNotFollow: { path: 'node_modules' }, exclude: { path: '(^|/)(generated|build|dist)/' } },
};
