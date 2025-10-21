import { useCallback } from "react";
import type { LocationController } from "../hooks/use_location";

interface LocationButtonProps {
  location: LocationController;
}

/**
 * Location button component: displays location status and provides a way to fetch location
 */
export function LocationButton({ location }: LocationButtonProps) {
  const { coordinates, isLoading, error, isSupported, requestLocation, clearLocation } = location;

  const handleLocationClick = useCallback(async () => {
    if (coordinates) {
      // If location already exists, clear it
      clearLocation();
    } else {
      // Otherwise, request location
      await requestLocation();
    }
  }, [coordinates, clearLocation, requestLocation]);

  if (!isSupported) {
    return (
      <div className="flex items-center gap-2 rounded-md border border-slate-300 bg-slate-100 px-3 py-2 text-sm text-slate-500">
        <span>🚫</span>
        <span>Your browser does not support geolocation</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <button
        type="button"
        onClick={handleLocationClick}
        disabled={isLoading}
        className={`flex items-center gap-2 rounded-md border px-4 py-2 text-sm font-medium transition-colors ${
          coordinates
            ? "border-green-500 bg-green-50 text-green-700 hover:bg-green-100"
            : isLoading
            ? "border-slate-300 bg-slate-100 text-slate-500 cursor-not-allowed"
            : "border-orange-500 bg-orange-50 text-orange-700 hover:bg-orange-100"
        }`}
      >
        {isLoading ? (
          <>
            <span className="animate-spin">⏳</span>
            <span>Getting location...</span>
          </>
        ) : coordinates ? (
          <>
            <span>✅</span>
            <span>Located</span>
            <span className="text-xs text-green-600">
              ({coordinates.latitude.toFixed(4)}, {coordinates.longitude.toFixed(4)})
            </span>
          </>
        ) : (
          <>
            <span>📍</span>
            <span>Click to get current location</span>
          </>
        )}
      </button>

      {error && (
        <div className="flex items-start gap-2 rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700">
          <span className="flex-shrink-0">⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {coordinates && (
        <div className="text-xs text-slate-500">
          <div>Latitude: {coordinates.latitude}</div>
          <div>Longitude: {coordinates.longitude}</div>
          {coordinates.accuracy && (
            <div>Accuracy: ±{coordinates.accuracy.toFixed(0)} m</div>
          )}
        </div>
      )}
    </div>
  );
}
