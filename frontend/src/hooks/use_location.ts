import { useCallback, useEffect, useState } from "react";

export interface LocationCoordinates {
  latitude: number;
  longitude: number;
  accuracy?: number;
  source?: 'browser' | 'address'; // Source of location: browser geolocation or address input
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
  setCoordinatesFromAddress: (address: string) => Promise<LocationCoordinates | null>;
  setCoordinatesManually: (coordinates: LocationCoordinates) => void;
}

/**
 * Custom hook to fetch the user's geolocation
 */
export function useLocation(): LocationController {
  const [coordinates, setCoordinates] = useState<LocationCoordinates | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSupported, setIsSupported] = useState(false);

  // Check whether the browser supports geolocation
  useEffect(() => {
    setIsSupported("geolocation" in navigator);
  }, []);

  // Request the user's location
  const requestLocation = useCallback(async () => {
    if (!navigator.geolocation) {
      setError("Your browser does not support geolocation");
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
            enableHighAccuracy: true, // Enable high accuracy
            timeout: 10000, // 10s timeout
            maximumAge: 0, // Do not use cached position
          }
        );
      });

      const newCoordinates: LocationCoordinates = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
        source: 'browser',
      };

      setCoordinates(newCoordinates);
      console.log("Location acquired successfully:", newCoordinates);
    } catch (err) {
      let errorMessage = "Unable to get your location";

      if (err instanceof GeolocationPositionError) {
        switch (err.code) {
          case err.PERMISSION_DENIED:
            errorMessage = "Location permission denied. Please allow location access in browser settings.";
            break;
          case err.POSITION_UNAVAILABLE:
            errorMessage = "Location information is currently unavailable. Please try again later.";
            break;
          case err.TIMEOUT:
            errorMessage = "Getting location timed out. Please check your network connection and retry.";
            break;
        }
      }

      setError(errorMessage);
      console.error("Failed to acquire location:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Clear location
  const clearLocation = useCallback(() => {
    setCoordinates(null);
    setError(null);
  }, []);

  // Manually set coordinates
  const setCoordinatesManually = useCallback((coords: LocationCoordinates) => {
    setCoordinates(coords);
    setError(null);
    console.log("Manually set location:", coords);
  }, []);

  // Get coordinates by address/postcode
  const setCoordinatesFromAddress = useCallback(async (address: string): Promise<LocationCoordinates | null> => {
    if (!address.trim()) {
      setError("Please enter a valid address or postal code");
      return null;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Use Google Geocoding API
      const apiKey = process.env.REACT_APP_GOOGLE_MAPS_API_KEY;
      if (!apiKey) {
        throw new Error("Google Maps API key is not configured. Set REACT_APP_GOOGLE_MAPS_API_KEY in env or contact admin.");
      }

      const response = await fetch(
        `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(address)}&key=${apiKey}`
      );
      
      if (!response.ok) {
        throw new Error("Geocoding request failed");
      }

      const data = await response.json();
      
      if (data.status !== "OK" || !data.results || data.results.length === 0) {
        throw new Error("Could not find a location for that address. Please check the address or postal code.");
      }

      const location = data.results[0].geometry.location;
      const newCoordinates: LocationCoordinates = {
        latitude: location.lat,
        longitude: location.lng,
        source: 'address',
      };

      setCoordinates(newCoordinates);
      console.log("Location from address success:", newCoordinates, "address:", data.results[0].formatted_address);
      return newCoordinates;
    } catch (err) {
      let errorMessage = "Unable to fetch location information";
      if (err instanceof Error) {
        errorMessage = err.message;
      }
      setError(errorMessage);
      console.error("Address to coordinates failed:", err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    coordinates,
    isLoading,
    error,
    isSupported,
    requestLocation,
    clearLocation,
    setCoordinatesFromAddress,
    setCoordinatesManually,
  };
}
