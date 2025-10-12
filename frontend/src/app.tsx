import { useCallback } from "react";
import { ChatPanel } from "./components/chat_panel";
import { useLanggraphChat } from "./hooks/use_langgraph_chat";

function Header() {
  const handleLogoClick = useCallback(() => {
    window.open("https://github.com/langchain-ai/langgraph", "_blank", "noreferrer");
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

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <Header />
      <main className="flex flex-1 justify-center px-4 py-8">
        <div className="flex w-full max-w-5xl flex-col gap-6">
          <ChatPanel {...chat} />
        </div>
      </main>
    </div>
  );
}

export default App;
