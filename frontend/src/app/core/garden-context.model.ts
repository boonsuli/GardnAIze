export type Exposure = 'FULL_SUN' | 'PARTIAL_SHADE' | 'SHADE';
export type SoilType = 'SANDY' | 'LOAMY' | 'CLAY' | 'UNKNOWN';
export type Watering = 'LOW' | 'MODERATE' | 'REGULAR';
export type Maintenance = 'LOW' | 'MODERATE' | 'HIGH';
export type PlantStyle = 'EVERGREEN' | 'FLOWERING' | 'MIXED';

export interface GardenContext {
    location: string;
    exposure: Exposure;
    soilType: SoilType;
    watering: Watering;
    maintenance: Maintenance;
    style: PlantStyle;
    maxHeightCm: number | null;
    privacyScreen: boolean;
}

export interface GardenAnalysisRequest {
    photoId: string;
    context: GardenContext;
}

export interface GardenAnalysisResponse {
    analysisId: string;
    status: string;
    plants?: Array<{ name: string; reason: string }>;
}
