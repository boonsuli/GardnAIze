/** UI rules for a questionnaire completed alongside asynchronous GDAI-VISION. */
export type ContextQuestionState = 'WAITING' | 'READY' | 'SKIPPED' | 'UNAVAILABLE';

export interface ContextQuestion {
    state: ContextQuestionState;
    questionKey: string | null;
    reason: string | null;
}

/** The action is not rendered until the context question (or explicit skip) arrives. */
export function shouldShowRecommendationButton(context: ContextQuestion | null): boolean {
    return context?.state === 'READY' || context?.state === 'SKIPPED';
}

/** Rendering and enabling are deliberately separate decisions. */
export function canSubmitRecommendations(
    context: ContextQuestion | null,
    mandatoryAnswersComplete: boolean,
    contextualAnswer: string | undefined
): boolean {
    if (!mandatoryAnswersComplete || !shouldShowRecommendationButton(context)) return false;
    if (context?.state === 'SKIPPED') return true;
    return !!contextualAnswer?.trim();
}

export function shouldShowContextQuestion(context: ContextQuestion | null): boolean {
    return context?.state === 'READY' && !!context.questionKey;
}
