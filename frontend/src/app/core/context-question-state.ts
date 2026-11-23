/**
 * Questionnaire completion rules for the asynchronous VISION workflow.
 * The submit button is never shown while VISION is still pending.
 */
export type ContextQuestionState = 'WAITING' | 'READY' | 'SKIPPED' | 'UNAVAILABLE';

export interface ContextQuestion {
    state: ContextQuestionState;
    questionKey: string | null;
    reason: string | null;
}

export function shouldShowRecommendationButton(
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
