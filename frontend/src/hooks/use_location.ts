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
 * 自定义 Hook 用于获取用户的地理位置
 */
export function useLocation(): LocationController {
  const [coordinates, setCoordinates] = useState<LocationCoordinates | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSupported, setIsSupported] = useState(false);

  // 检查浏览器是否支持地理定位
  useEffect(() => {
    setIsSupported("geolocation" in navigator);
  }, []);

  // 请求获取用户位置
  const requestLocation = useCallback(async () => {
    if (!navigator.geolocation) {
      setError("您的浏览器不支持地理定位功能");
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
            enableHighAccuracy: true, // 启用高精度
            timeout: 10000, // 10秒超时
            maximumAge: 0, // 不使用缓存的位置
          }
        );
      });

      const newCoordinates: LocationCoordinates = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
      };

      setCoordinates(newCoordinates);
      console.log("位置获取成功:", newCoordinates);
    } catch (err) {
      let errorMessage = "无法获取您的位置";

      if (err instanceof GeolocationPositionError) {
        switch (err.code) {
          case err.PERMISSION_DENIED:
            errorMessage = "您拒绝了位置权限请求，请在浏览器设置中允许位置访问";
            break;
          case err.POSITION_UNAVAILABLE:
            errorMessage = "位置信息暂时不可用，请稍后再试";
            break;
          case err.TIMEOUT:
            errorMessage = "获取位置超时，请检查网络连接后重试";
            break;
        }
      }

      setError(errorMessage);
      console.error("位置获取失败:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 清除位置信息
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

