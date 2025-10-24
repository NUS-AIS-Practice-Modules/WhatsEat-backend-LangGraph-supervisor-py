import { useCallback } from "react";
import { ChatPanel } from "./components/chat_panel";
import { LocationButton } from "./components/location_button";
import { useLanggraphChat } from "./hooks/use_langgraph_chat";
import { useLocation } from "./hooks/use_location";

function Header() {
  const handleLogoClick = useCallback(() => {
    window.open("https://github.com/NUS-AIS-Practice-Modules/IRS-PM-2025-08-30-IS02PT-GRP-NeverStopCoding-WhatsEat", "_blank", "noreferrer");
  }, []);

  return (
    <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={handleLogoClick}
          className="flex items-center gap-3 border-none bg-transparent p-0 text-left text-brand hover:text-brand-muted"
        >
          <img src="/LOGO.svg" alt="WhatsEat logo" className="h-8 w-8" />
          <span className="text-2xl font-bold tracking-tight">What'sEat</span>
        </button>
      </div>
      <p className="text-sm text-slate-500">
        Powered by LangGraph multi-agent supervisor
      </p>
    </header>
  );
}

function App(): JSX.Element {
  const chat = useLanggraphChat();
  const location = useLocation();

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <Header />
      <main className="flex flex-1 justify-center px-4 py-8">
        <div className="flex w-full max-w-5xl flex-col gap-6">
          {/*/!* Location acquisition component *!/*/}
          {/*<div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">*/}
          {/*  <div className="flex items-start justify-between gap-4">*/}
          {/*    <div className="flex-1">*/}
          {/*      <h2 className="text-sm font-semibold text-slate-700 mb-1">📍 Location Service</h2>*/}
          {/*      <p className="text-xs text-slate-500">*/}
          {/*        Authorize access to your location to recommend nearby restaurants*/}
          {/*      </p>*/}
          {/*    </div>*/}
          {/*    <LocationButton location={location} />*/}
          {/*  </div>*/}
          {/*</div>*/}

          {/* Chat panel */}
          <ChatPanel {...chat} userLocation={location.coordinates} location={location} />
        </div>
      </main>
    </div>
  );
}

export default App;
