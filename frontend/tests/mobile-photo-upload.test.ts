import assert from 'node:assert/strict';
import test from 'node:test';
import { isValidPhoto, MAX_PHOTO_SIZE_BYTES } from '../src/app/core/photo-validation';

test('photo limit is exactly 5 MiB', () => {
    assert.equal(MAX_PHOTO_SIZE_BYTES, 5 * 1024 * 1024);
    assert.equal(isValidPhoto('image/jpeg', MAX_PHOTO_SIZE_BYTES), true);
    assert.equal(isValidPhoto('image/jpeg', MAX_PHOTO_SIZE_BYTES + 1), false);
});

test('accepted smartphone image formats', () => {
    for (const type of ['image/jpeg', 'image/png', 'image/webp']) {
        assert.equal(isValidPhoto(type, 1024), true);
    }
    assert.equal(isValidPhoto('image/heic', 1024), false);
    assert.equal(isValidPhoto('application/pdf', 1024), false);
});
