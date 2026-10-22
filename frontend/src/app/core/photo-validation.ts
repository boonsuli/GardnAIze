export const ALLOWED_PHOTO_TYPES = ['image/jpeg', 'image/png', 'image/webp'] as const;
export const MAX_PHOTO_SIZE_BYTES = 10 * 1024 * 1024;

export function isValidPhoto(type: string, size: number): boolean {
    return ALLOWED_PHOTO_TYPES.some((allowed) => allowed === type)
        && Number.isFinite(size)
        && size >= 0
        && size <= MAX_PHOTO_SIZE_BYTES;
}
