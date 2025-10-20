import { FormEvent, useCallback, useState } from "react";
import { ChatTranscript } from "./chat_transcript";
import { RuntimeStatus } from "./runtime_status";
import type { ChatController } from "../hooks/use_langgraph_chat";
import type { LocationCoordinates, LocationController } from "../hooks/use_location";

interface ChatPanelProps extends ChatController {
  userLocation: LocationCoordinates | null;
  location: LocationController;
}

/**
 * 从用户消息中提取地址或邮编
 * 支持多种格式：
 * - "near 238801" 或 "at Marina Bay"
 * - "在 238801" 或 "邮编 238801"
 * - 直接的6位数字邮编
 * - 包含地址关键词的完整地址
 */
function extractAddressFromMessage(message: string): string | null {
  const lowerMessage = message.toLowerCase();
  
  // 1. 检测邮编格式（6位数字）
  const zipCodeMatch = message.match(/\b(\d{6})\b/);
  if (zipCodeMatch) {
    return zipCodeMatch[1];
  }
  
  // 2. 检测带关键词的地址（英文）
  // 支持: near/at/in/from/around + 地址
  const englishAddressMatch = message.match(/(?:near|at|in|from|around)\s+([\w\s,.-]+?)(?:\s+(?:find|search|show|recommend|get)|$)/i);
  if (englishAddressMatch && englishAddressMatch[1]) {
    const address = englishAddressMatch[1].trim();
    // 确保提取的内容有一定长度
    if (address.length >= 3) {
      return address;
    }
  }
  
  // 3. 检测中文地址关键词
  // 支持: 在/邮编/地址 + 地址信息
  const chineseAddressMatch = message.match(/(?:在|邮编|地址|从)\s*([\w\s,，。.、-]+?)(?:\s*(?:找|搜|查|推荐)|$)/);
  if (chineseAddressMatch && chineseAddressMatch[1]) {
    const address = chineseAddressMatch[1].trim();
    if (address.length >= 2) {
      return address;
    }
  }
  
  // 4. 检测常见地名模式（新加坡地区）
  const singaporeAreaMatch = message.match(/\b(marina bay|orchard|sentosa|chinatown|bugis|raffles place|clarke quay|little india|tanjong pagar|dhoby ghaut|city hall|jurong|tampines|bedok|woodlands|yishun|ang mo kio|bishan|serangoon|hougang|punggol|sengkang)\b/i);
  if (singaporeAreaMatch) {
    return singaporeAreaMatch[0];
  }
  
  return null;
}

export function ChatPanel({
  messages,
  sendMessage,
  reset,
  status,
  isStreaming,
  error,
  userLocation,
  location,
}: ChatPanelProps) {
  const [input, setInput] = useState("");

  const handleSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      const message = input.trim();
      if (!message) {
        return;
      }
      setInput("");
      
      // 如果用户还没有定位，尝试从消息中提取地址并获取经纬度
      let locationToUse = userLocation;
      if (!userLocation) {
        // 尝试提取地址或邮编
        const addressToGeocode = extractAddressFromMessage(message);
        
        if (addressToGeocode) {
          console.log("检测到地址信息，正在获取坐标:", addressToGeocode);
          try {
            const coordinates = await location.setCoordinatesFromAddress(addressToGeocode);
            if (coordinates) {
              locationToUse = coordinates;
              console.log("成功获取坐标:", locationToUse);
            }
          } catch (err) {
            console.warn("自动地址识别失败，继续发送消息:", err);
          }
        }
      }
      
      // 发送消息时携带用户位置信息（可能是原有的定位，也可能是从地址转换的）
      await sendMessage(message, locationToUse);
    },
    [input, sendMessage, userLocation, location]
  );

  const handleReset = useCallback(() => {
    reset();
  }, [reset]);

  const handleRequestMore = useCallback(async () => {
    if (status !== "ready" || isStreaming) {
      return;
    }
    await sendMessage("Please recommend more restaurants.", userLocation);
  }, [isStreaming, sendMessage, status, userLocation]);

  const handleRecommend = useCallback(async () => {
    if (status !== "ready" || isStreaming) {
      return;
    }
    await sendMessage("Recommend nearby restaurants", userLocation);
  }, [isStreaming, sendMessage, status, userLocation]);

  const handleLocationClick = useCallback(async () => {
    if (location.isLoading) {
      return;
    }
    if (userLocation) {
      location.clearLocation();
      return;
    }
    await location.requestLocation();
  }, [location, userLocation]);

  return (
    <section className="flex flex-1 min-h-0 flex-col gap-4 rounded-lg border border-slate-200 bg-white shadow-lg">
      <div className="flex flex-col gap-3 px-6 pt-6">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold text-brand">Culinary discovery assistant</h1>
          <RuntimeStatus status={status} onReset={handleReset} />
        </div>
        <p className="text-sm text-slate-400">
          Ask for nearby restaurants, request personalized picks, or explore summaries from the multi-agent workflow.
        </p>
      </div>
      <div className="flex-1 min-h-0 overflow-hidden px-2">
        <ChatTranscript
          messages={messages}
          isStreaming={isStreaming}
          userLocation={userLocation}
          onRequestMore={handleRequestMore}
          disableRequestMore={status !== "ready" || isStreaming}
        />
      </div>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3 border-t border-slate-200 bg-slate-50 px-6 py-4">
        <button
          type="button"
          onClick={handleRecommend}
          disabled={status !== "ready" || isStreaming}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-orange-500 px-4 py-2 font-medium text-white transition-colors hover:bg-orange-600 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <span>Recommend Nearby</span>
        </button>

        {userLocation ? (
          userLocation.source === 'browser' ? (
            <div className="flex items-center gap-2 rounded border border-green-200 bg-green-50 px-3 py-2 text-xs text-green-700">
              <span>✅</span>
              <span>已通过浏览器定位获取位置 — 将使用您的当前位置进行附近搜索</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 rounded border border-blue-200 bg-blue-50 px-3 py-2 text-xs text-blue-700">
              <span>📍</span>
              <span>已通过地址设置位置 — 将使用该位置进行附近搜索</span>
            </div>
          )
        ) : (
          <div className="flex items-center gap-2 rounded border border-orange-200 bg-orange-50 px-3 py-2 text-xs text-orange-700">
            <span>💡</span>
            <span>提示：您可以在消息中输入地址或邮编（如 "near 238801" 或 "在 Marina Bay"），系统会自动识别并使用该位置</span>
          </div>
        )}

        <div className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Find spicy ramen near me..."
            aria-label="Message the WhatsEat supervisor"
            disabled={status === "unavailable" || isStreaming}
            className="flex-1"
          />
          <button type="submit" disabled={status !== "ready" || isStreaming || !input.trim()}>
            Send
          </button>
          <button
            type="button"
            onClick={handleLocationClick}
            disabled={location.isLoading}
            className={`flex h-10 w-10 items-center justify-center rounded-full transition-colors ${
              userLocation
                ? userLocation.source === 'browser'
                  ? "bg-green-500 text-white hover:bg-green-600"
                  : "bg-blue-500 text-white hover:bg-blue-600"
                : location.isLoading
                ? "cursor-not-allowed bg-slate-300 text-slate-500"
                : "bg-orange-500 text-white hover:bg-orange-600"
            }`}
            aria-label={userLocation ? "Clear location" : "Get location"}
          >
            {location.isLoading ? (
              <svg className="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            ) : userLocation ? (
              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            ) : (
              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z"
                  clipRule="evenodd"
                />
              </svg>
            )}
          </button>
        </div>
        {error ? <span className="text-sm text-red-500">{error}</span> : null}
        {location.error && !error ? <span className="text-sm text-red-500">{location.error}</span> : null}
      </form>
    </section>
  );
}
