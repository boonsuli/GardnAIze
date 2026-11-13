import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

export interface QuestionnaireOption {
    value: string;
    labelKey: string;
}
export interface QuestionnaireQuestion {
    key: string;
    labelKey: string;
    required: boolean;
    inputType: string;
    options: QuestionnaireOption[];
}
export interface QuestionnaireCatalog {
    schemaVersion: number;
    externalProcessingNoticeKey: string;
    questions: QuestionnaireQuestion[];
}
export interface PhotoProcessingRequest {
    requestId: string;
    gardenId: string;
    photoId: string;
    status: 'ACCEPTED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'REJECTED';
    createdAt: string;
    statusUrl: string;
}
export interface PhotoAnalysisResult {
    photoId: string;
    gardenId: string;
    photoStatus: string;
    processingStatus: string;
    rejectionReason: string | null;
}

export type Exposure = 'FULL_SUN' | 'PARTIAL_SHADE' | 'SHADE';
export type SoilType = 'SANDY' | 'LOAMY' | 'CLAY' | 'UNKNOWN';
export type RequirementLevel = 'LOW' | 'MODERATE' | 'HIGH';

export interface CreateGardenRequest {
    name: string;
    location: string;
    countryCode: string;
    climateRegion: string;
    exposure: Exposure;
    soilType: SoilType;
}

export interface GardenProject extends CreateGardenRequest {
    id: string;
    createdAt: string;
}

export interface GardenPreferencesRequest {
    waterAvailability: RequirementLevel;
    maintenancePreference: RequirementLevel;
    evergreenPreferred: boolean;
    privacyScreeningRequired: boolean;
    desiredHeightCm: number | null;
}

export interface GardenPreferences extends GardenPreferencesRequest {
    gardenId: string;
    updatedAt: string;
}

export interface PlantSuggestion {
    name: string;
    reason: string;
}

export interface RecommendationResponse {
    mode: string;
    plants: PlantSuggestion[];
}

@Injectable({ providedIn: 'root' })
export class GardenApiService {
    private readonly http = inject(HttpClient);

    loadDictionary(language: 'FR' | 'EN'): Observable<Record<string, unknown>> {
        return this.http.get<Record<string, unknown>>(
            '/i18n/GardnAIze_data_' + language + '.json'
        );
    }

    getQuestionnaire(): Observable<QuestionnaireCatalog> {
        return this.http.get<QuestionnaireCatalog>('/api/v1/questionnaire');
    }

    validatePhoto(file: File): Observable<{ valid: boolean; reason: string }> {
        const data = new FormData();
        data.append('file', file, file.name);
        return this.http.post<{ valid: boolean; reason: string }>('/api/v1/photos/validate', data);
    }

    uploadPhoto(gardenId: string, file: File, description: string,
            answers: Record<string, string>, consentKey: string): Observable<PhotoProcessingRequest> {
        const data = new FormData();
        data.append('file', file, file.name);
        data.append('description', description);
        data.append('answersJson', JSON.stringify(answers));
        data.append('consentKey', consentKey);
        return this.http.post<PhotoProcessingRequest>(
            '/api/v1/gardens/' + encodeURIComponent(gardenId) + '/photos', data
        );
    }

    getPhotoRequest(gardenId: string, requestId: string): Observable<PhotoProcessingRequest> {
        return this.http.get<PhotoProcessingRequest>(
            '/api/v1/gardens/' + encodeURIComponent(gardenId)
            + '/photo-requests/' + encodeURIComponent(requestId));
    }

    createGarden(request: CreateGardenRequest): Observable<GardenProject> {
        return this.http.post<GardenProject>('/api/v1/gardens', request);
    }

    savePreferences(id: string, request: GardenPreferencesRequest): Observable<GardenPreferences> {
        return this.http.put<GardenPreferences>(
            `/api/v1/gardens/${encodeURIComponent(id)}/preferences`, request
        );
    }

    getPreferences(id: string): Observable<GardenPreferences> {
        return this.http.get<GardenPreferences>(
            `/api/v1/gardens/${encodeURIComponent(id)}/preferences`
        );
    }

    getRecommendations(id: string): Observable<RecommendationResponse> {
        return this.http.get<RecommendationResponse>(
            `/api/v1/gardens/${encodeURIComponent(id)}/recommendations`
        );
    }
}
