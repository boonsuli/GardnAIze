import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

export type Exposure = 'FULL_SUN' | 'PARTIAL_SHADE' | 'SHADE';
export type SoilType = 'SANDY' | 'LOAMY' | 'CLAY' | 'UNKNOWN';
export type RequirementLevel = 'LOW' | 'MODERATE' | 'HIGH';

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
