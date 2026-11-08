export type QuestionType = 'text' | 'select' | 'number' | 'boolean';
export interface GardenQuestion {
    id: string;
    label: string;
    type: QuestionType;
    required: boolean;
    options?: Array<{ value: string; label: string }>;
}
export interface QuestionnaireResponse {
    photoId: string;
    questions: GardenQuestion[];
}
export interface GardenAnalysisRequest {
    photoId: string;
    answers: Record<string, string | number | boolean | null>;
}
export interface GardenAnalysisResponse {
    analysisId: string;
    status: string;
    plants?: Array<{ name: string; reason: string }>;
}
