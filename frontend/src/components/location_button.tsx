import { useCallback } from "react";
import type { LocationController } from "../hooks/use_location";

interface LocationButtonProps {
  location: LocationController;
}

/**
 * 位置按钮组件，显示位置状态并提供获取位置的功能
 */
export function LocationButton({ location }: LocationButtonProps) {
  const { coordinates, isLoading, error, isSupported, requestLocation, clearLocation } = location;

  const handleLocationClick = useCallback(async () => {
    if (coordinates) {
      // 如果已经有位置信息，清除它
      clearLocation();
    } else {
      // 否则请求获取位置
      await requestLocation();
    }
  }, [coordinates, clearLocation, requestLocation]);

  if (!isSupported) {
    return (
      <div className="flex items-center gap-2 rounded-md border border-slate-300 bg-slate-100 px-3 py-2 text-sm text-slate-500">
        <span>🚫</span>
        <span>您的浏览器不支持定位</span>
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
            <span>正在获取位置...</span>
          </>
        ) : coordinates ? (
          <>
            <span>✅</span>
            <span>已定位</span>
            <span className="text-xs text-green-600">
              ({coordinates.latitude.toFixed(4)}, {coordinates.longitude.toFixed(4)})
            </span>
          </>
        ) : (
          <>
            <span>📍</span>
            <span>点击获取当前位置</span>
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
          <div>纬度: {coordinates.latitude}</div>
          <div>经度: {coordinates.longitude}</div>
          {coordinates.accuracy && (
            <div>精度: ±{coordinates.accuracy.toFixed(0)}米</div>
          )}
        </div>
      )}
    </div>
  );
}

