import { strict as assert } from 'node:assert';
import { test } from 'node:test';
import {
    canSubmitRecommendations,
    shouldShowContextQuestion,
    shouldShowRecommendationButton,
    type ContextQuestion
} from '../src/app/core/context-question-state';

const waiting: ContextQuestion = { state: 'WAITING', questionKey: null, reason: null };
const ready: ContextQuestion = { state: 'READY', questionKey: 'privacy', reason: 'FENCE_DETECTED' };
const skipped: ContextQuestion = { state: 'SKIPPED', questionKey: null, reason: null };

test('button remains hidden while VISION is pending', () => {
    assert.equal(shouldShowRecommendationButton(null), false);
    assert.equal(shouldShowRecommendationButton(waiting), false);
    assert.equal(canSubmitRecommendations(waiting, true, 'YES'), false);
});

test('button appears with the contextual question but remains disabled until answered', () => {
    assert.equal(shouldShowContextQuestion(ready), true);
    assert.equal(shouldShowRecommendationButton(ready), true);
    assert.equal(canSubmitRecommendations(ready, true, undefined), false);
    assert.equal(canSubmitRecommendations(ready, true, 'YES'), true);
    assert.equal(canSubmitRecommendations(ready, false, 'YES'), false);
});

test('explicit no-context result lets a complete questionnaire proceed', () => {
    assert.equal(shouldShowContextQuestion(skipped), false);
    assert.equal(shouldShowRecommendationButton(skipped), true);
    assert.equal(canSubmitRecommendations(skipped, true, undefined), true);
    assert.equal(canSubmitRecommendations(skipped, false, undefined), false);
});
