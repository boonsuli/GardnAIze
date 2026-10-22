import assert from 'node:assert/strict';
import { test } from 'node:test';
import { isValidPhoto, MAX_PHOTO_SIZE_BYTES } from '../src/app/core/photo-validation';

test('accepts supported image formats', () => {
    for (const type of ['image/jpeg', 'image/png', 'image/webp']) {
        assert.equal(isValidPhoto(type, 1024), true);
    }
});

test('rejects unsupported formats', () => {
    assert.equal(isValidPhoto('image/svg+xml', 1024), false);
    assert.equal(isValidPhoto('application/pdf', 1024), false);
});

test('rejects oversize and invalid sizes', () => {
    assert.equal(isValidPhoto('image/jpeg', MAX_PHOTO_SIZE_BYTES), true);
    assert.equal(isValidPhoto('image/jpeg', MAX_PHOTO_SIZE_BYTES + 1), false);
    assert.equal(isValidPhoto('image/jpeg', -1), false);
    assert.equal(isValidPhoto('image/jpeg', Number.NaN), false);
});
