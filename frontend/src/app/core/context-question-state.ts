/** UI rules for a questionnaire completed alongside asynchronous GDAI-VISION. */
export type ContextQuestionState = 'WAITING' | 'READY' | 'SKIPPED' | 'UNAVAILABLE';

export interface ContextQuestion {
    state: ContextQuestionState;
    questionKey: string | null;
    reason: string | null;
}

/** The action is always rendered while the questionnaire is displayed. */
export function shouldShowRecommendationButton(_context: ContextQuestion | null): boolean {
    return true;
}

/** The action stays disabled until VISION resolves and required answers are complete. */
export function canSubmitRecommendations(
    context: ContextQuestion | null,
    mandatoryAnswersComplete: boolean,
    contextualAnswer: string | undefined
): boolean {
    if (!mandatoryAnswersComplete || context === null) return false;
    if (context.state === 'SKIPPED') return true;
    if (context.state !== 'READY' || !context.questionKey) return false;
    return !!contextualAnswer?.trim();
}

export function shouldShowContextQuestion(context: ContextQuestion | null): boolean {
    return context?.state === 'READY' && !!context.questionKey;
}
