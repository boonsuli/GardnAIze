import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const languages = ['FR', 'EN'] as const;

for (const language of languages) {
    test('questionnaire translations and external consent keys exist: ' + language, () => {
        const file = new URL('../public/i18n/GardnAIze_data_' + language + '.json', import.meta.url);
        const data = JSON.parse(readFileSync(file, 'utf8'));
        assert.equal(typeof data.privacy.externalProcessingNotice, 'string');
        assert.equal(typeof data.privacy.refuse, 'string');
        assert.equal(typeof data.privacy.acceptAndContinue, 'string');
        assert.equal(data.privacy.externalProcessingConsentKey, 'privacy.externalProcessingNotice');
        for (const question of ['exposure', 'soilType', 'waterAvailability',
                'maintenancePreference', 'evergreenPreferred', 'privacyScreeningRequired',
                'desiredHeight', 'preferredColors', 'budget', 'gardenStyle']) {
            assert.equal(typeof data.questionnaire[question].label, 'string');
            assert.ok(Object.keys(data.questionnaire[question].options).length > 0);
        }
    });
}
