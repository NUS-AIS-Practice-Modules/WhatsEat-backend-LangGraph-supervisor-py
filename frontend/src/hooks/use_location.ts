import { useCallback, useEffect, useState } from "react";

export interface LocationCoordinates {
  latitude: number;
  longitude: number;
  accuracy?: number;
}

export interface LocationState {
  coordinates: LocationCoordinates | null;
  isLoading: boolean;
  error: string | null;
  isSupported: boolean;
}

export interface LocationController extends LocationState {
  requestLocation: () => Promise<void>;
  clearLocation: () => void;
}

/**
 * Custom hook that retrieves the user location and exposes helpers to
 * request or clear the coordinates while managing loading/error state.
 */
export function useLocation(): LocationController {
  const [coordinates, setCoordinates] = useState<LocationCoordinates | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSupported, setIsSupported] = useState(false);

  useEffect(() => {
    setIsSupported("geolocation" in navigator);
  }, []);

  const requestLocation = useCallback(async () => {
    if (!navigator.geolocation) {
      setError("Your browser does not support geolocation.");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(
          resolve,
          reject,
          {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0,
          }
        );
      });

      const newCoordinates: LocationCoordinates = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
      };

      setCoordinates(newCoordinates);
      console.log("Location acquired:", newCoordinates);
    } catch (err) {
      let errorMessage = "We couldn’t determine your location.";

      if (err instanceof GeolocationPositionError) {
        switch (err.code) {
          case err.PERMISSION_DENIED:
            errorMessage = "You denied the location request. Please enable access in your browser settings.";
            break;
          case err.POSITION_UNAVAILABLE:
            errorMessage = "Location information is currently unavailable. Please try again later.";
            break;
          case err.TIMEOUT:
            errorMessage = "The location request timed out. Check your network connection and try again.";
            break;
        }
      }

      setError(errorMessage);
      console.error("Failed to acquire location:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearLocation = useCallback(() => {
    setCoordinates(null);
    setError(null);
  }, []);

  return {
    coordinates,
    isLoading,
    error,
    isSupported,
    requestLocation,
    clearLocation,
  };
}

