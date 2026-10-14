import { expect, test } from 'vitest';
import { increment } from './counter';
test('increments the supplied value', () => expect(increment(2)).toBe(3));
