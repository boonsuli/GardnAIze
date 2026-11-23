/** User-facing workflow messages. Technical statuses stay in GDAI-BACK. */
export type GardenWorkflowPhase =
    | 'PHOTO_READY'
    | 'VALIDATING'
    | 'PHOTO_VALID'
    | 'CONSENT_REQUIRED'
    | 'VISION_RUNNING'
    | 'QUESTIONNAIRE_RUNNING'
    | 'CONTEXT_READY'
    | 'ANSWERS_REQUIRED'
    | 'PLANT_RUNNING'
    | 'COMPLETED'
    | 'FAILED';

export type WorkflowStatusTone = 'info' | 'success' | 'warning' | 'error';

export interface WorkflowStatus {
    phase: GardenWorkflowPhase;
    messageKey: string;
    tone: WorkflowStatusTone;
    busy: boolean;
}

const STATUS: Record<GardenWorkflowPhase, Omit<WorkflowStatus, 'phase'>> = {
    PHOTO_READY: { messageKey: 'workflowStatus.photoReady', tone: 'info', busy: false },
    VALIDATING: { messageKey: 'workflowStatus.validating', tone: 'info', busy: true },
    PHOTO_VALID: { messageKey: 'workflowStatus.photoValid', tone: 'success', busy: false },
    CONSENT_REQUIRED: { messageKey: 'workflowStatus.consentRequired', tone: 'warning', busy: false },
    VISION_RUNNING: { messageKey: 'workflowStatus.visionRunning', tone: 'info', busy: true },
    QUESTIONNAIRE_RUNNING: { messageKey: 'workflowStatus.questionnaireRunning', tone: 'info', busy: true },
    CONTEXT_READY: { messageKey: 'workflowStatus.contextReady', tone: 'info', busy: false },
    ANSWERS_REQUIRED: { messageKey: 'workflowStatus.answersRequired', tone: 'warning', busy: false },
    PLANT_RUNNING: { messageKey: 'workflowStatus.plantRunning', tone: 'info', busy: true },
    COMPLETED: { messageKey: 'workflowStatus.completed', tone: 'success', busy: false },
    FAILED: { messageKey: 'workflowStatus.failed', tone: 'error', busy: false }
};

export function workflowStatus(phase: GardenWorkflowPhase): WorkflowStatus {
    return { phase, ...STATUS[phase] };
}
