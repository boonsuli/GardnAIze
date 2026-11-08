import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { GardenAnalysisRequest, GardenAnalysisResponse } from './garden-context.model';

export type Exposure = 'FULL_SUN' | 'PARTIAL_SHADE' | 'SHADE';
export type SoilType = 'SANDY' | 'LOAMY' | 'CLAY' | 'UNKNOWN';

export interface CreateGardenRequest {
    name: string;
    location: string;
    exposure: Exposure;
    soilType: SoilType;
}
export interface GardenProject extends CreateGardenRequest {
    id: string;
    createdAt: string;
}
export interface PlantSuggestion {
    name: string;
    reason: string;
}
export interface RecommendationResponse {
    mode: string;
    plants: PlantSuggestion[];
}
export interface PhotoUploadResponse {
    photoId: string;
    status: 'VALID' | 'INVALID' | 'PENDING';
    message?: string;
}

@Injectable({ providedIn: 'root' })
export class GardenApiService {
    private readonly http = inject(HttpClient);

    createGarden(request: CreateGardenRequest): Observable<GardenProject> {
        return this.http.post<GardenProject>('/api/v1/gardens', request);
    }

    getRecommendations(id: string): Observable<RecommendationResponse> {
        return this.http.get<RecommendationResponse>(
            `/api/v1/gardens/${encodeURIComponent(id)}/recommendations`
        );
    }

    // Proposed GDAI-BACK contracts: implement/align backend before end-to-end deployment.
    uploadPhoto(file: File): Observable<PhotoUploadResponse> {
        const body = new FormData();
        body.append('photo', file, file.name);
        return this.http.post<PhotoUploadResponse>('/api/v1/gardens/photos/validate', body);
    }

    analyzeGarden(request: GardenAnalysisRequest): Observable<GardenAnalysisResponse> {
        return this.http.post<GardenAnalysisResponse>('/api/v1/gardens/analyze', request);
    }
}
