import { useCallback, useEffect, useState } from "react";

export interface LocationCoordinates {
  latitude: number;
  longitude: number;
  accuracy?: number;
  source?: 'browser' | 'address'; // 定位来源：浏览器定位或地址输入
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
        source: 'browser',
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

  // 手动设置坐标
  const setCoordinatesManually = useCallback((coords: LocationCoordinates) => {
    setCoordinates(coords);
    setError(null);
    console.log("手动设置位置:", coords);
  }, []);

  // 通过地址/邮编获取坐标
  const setCoordinatesFromAddress = useCallback(async (address: string): Promise<LocationCoordinates | null> => {
    if (!address.trim()) {
      setError("请输入有效的地址或邮编");
      return null;
    }

    setIsLoading(true);
    setError(null);

    try {
      // 使用 Google Geocoding API
      const apiKey = process.env.REACT_APP_GOOGLE_MAPS_API_KEY;
      if (!apiKey) {
        throw new Error("未配置 Google Maps API 密钥，请联系管理员或在环境变量中设置 REACT_APP_GOOGLE_MAPS_API_KEY");
      }

      const response = await fetch(
        `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(address)}&key=${apiKey}`
      );
      
      if (!response.ok) {
        throw new Error("地理编码请求失败");
      }

      const data = await response.json();
      
      if (data.status !== "OK" || !data.results || data.results.length === 0) {
        throw new Error("无法找到该地址对应的位置，请检查地址或邮编是否正确");
      }

      const location = data.results[0].geometry.location;
      const newCoordinates: LocationCoordinates = {
        latitude: location.lat,
        longitude: location.lng,
        source: 'address',
      };

      setCoordinates(newCoordinates);
      console.log("通过地址获取位置成功:", newCoordinates, "地址:", data.results[0].formatted_address);
      return newCoordinates;
    } catch (err) {
      let errorMessage = "无法获取位置信息";
      if (err instanceof Error) {
        errorMessage = err.message;
      }
      setError(errorMessage);
      console.error("地址转换失败:", err);
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

