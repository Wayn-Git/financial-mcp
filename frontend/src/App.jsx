import { useEffect, useRef, useState } from "react";
import { TrendingUp, Shield, Zap, Search, ArrowRight, BarChart3, Activity, Building2, Scale, Cpu, LineChart } from "lucide-react";

/* ------------------------------
   Helper: Render AI Messages
-------------------------------- */
function RenderMessage({ content }) {
  // Parse markdown-style formatting
  const parseText = (text) => {
    const parts = [];
    let currentIndex = 0;
    
    // Match **bold** text
    const boldRegex = /\*\*(.*?)\*\*/g;
    let match;
    
    while ((match = boldRegex.exec(text)) !== null) {
      // Add text before bold
      if (match.index > currentIndex) {
        parts.push({
          type: 'text',
          content: text.slice(currentIndex, match.index)
        });
      }
      // Add bold text
      parts.push({
        type: 'bold',
        content: match[1]
      });
      currentIndex = match.index + match[0].length;
    }
    
    // Add remaining text
    if (currentIndex < text.length) {
      parts.push({
        type: 'text',
        content: text.slice(currentIndex)
      });
    }
    
    return parts;
  };

  // Split content into sections
  const sections = content.split(/\n\s*\n/);
  
  return (
    <div className="space-y-4 text-sm">
      {sections.map((section, sectionIdx) => {
        const lines = section.split('\n').filter(l => l.trim());
        
        // Check if this is a header section (all bold or ends with colon)
        const isHeader = lines.length === 1 && (lines[0].includes('**') || lines[0].trim().endsWith(':'));
        
        if (isHeader) {
          const headerText = lines[0].replace(/\*\*/g, '').replace(/:$/, '');
          return (
            <div key={sectionIdx} className="pt-3 first:pt-0">
              <div className="inline-flex items-center gap-2 pb-2 border-b border-neutral-800/50">
                <div className="w-1 h-1 rounded-full bg-white" />
                <h3 className="text-sm font-bold text-white tracking-tight">
                  {headerText}
                </h3>
              </div>
            </div>
          );
        }
        
        // Check if this section contains a numbered list
        const hasNumberedList = lines.some(l => /^\d+\./.test(l.trim()));
        
        if (hasNumberedList) {
          return (
            <div key={sectionIdx} className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {lines.map((line, idx) => {
                const match = line.match(/^(\d+)\.\s*\*\*(.*?)\*\*:?\s*(.*)/);
                if (match) {
                  const [, num, title, description] = match;
                  return (
                    <div
                      key={idx}
                      className="group relative overflow-hidden rounded-xl p-4 bg-neutral-900/30 border border-neutral-800/50 hover:border-neutral-700/80 hover:bg-neutral-900/50 transition-all duration-300"
                    >
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 w-6 h-6 rounded-lg bg-white/5 border border-neutral-800/50 flex items-center justify-center">
                          <span className="text-xs font-bold text-neutral-400">{num}</span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-bold text-white text-sm mb-1 group-hover:text-white transition-colors">
                            {title}
                          </h4>
                          {description && (
                            <p className="text-xs text-neutral-400 leading-relaxed">
                              {description}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                }
                return null;
              }).filter(Boolean)}
            </div>
          );
        }
        
        // Regular paragraph with inline formatting
        return (
          <div key={sectionIdx} className="space-y-2">
            {lines.map((line, idx) => {
              if (!line.trim()) return null;
              
              const parts = parseText(line);
              
              return (
                <div key={idx} className="leading-relaxed text-neutral-300">
                  {parts.map((part, i) => {
                    if (part.type === 'bold') {
                      return (
                        <span key={i} className="font-semibold text-white">
                          {part.content}
                        </span>
                      );
                    }
                    return <span key={i}>{part.content}</span>;
                  })}
                </div>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}

/* ------------------------------
   Main App
-------------------------------- */
export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sessionId = useRef(crypto.randomUUID());
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage() {
    if (!input.trim()) return;

    setMessages((prev) => [
      ...prev,
      { role: "user", content: input },
    ]);

    setInput("");
    setLoading(true);

    try {
      const res = await fetch("http://127.0.0.1:8000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: input,
          session_id: sessionId.current,
        }),
      });

      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "⚠️ Something went wrong. Try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-neutral-950 relative overflow-hidden">
      
      {/* Subtle lighting */}
      <div className="fixed top-0 right-0 w-[600px] h-[600px] bg-white/[0.02] rounded-full blur-[120px]" />
      <div className="fixed bottom-0 left-0 w-[500px] h-[500px] bg-white/[0.015] rounded-full blur-[100px]" />
      
      {/* Grid pattern overlay */}
      <div className="fixed inset-0 bg-[linear-gradient(to_right,#80808008_1px,transparent_1px),linear-gradient(to_bottom,#80808008_1px,transparent_1px)] bg-[size:24px_24px]" />

      {/* NAVBAR */}
      <header className="sticky top-0 z-50 px-4 py-3 bg-neutral-950/80 backdrop-blur-xl border-b border-neutral-800/50">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-white flex items-center justify-center">
              <TrendingUp className="w-4 h-4 text-black" strokeWidth={2.5} />
            </div>
            <span className="text-sm font-bold text-white tracking-tight">FintelAI</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-neutral-900/50 border border-neutral-800/50">
              <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
              <span className="text-xs font-medium text-neutral-400">Live</span>
            </div>
          </div>
        </div>
      </header>

      {/* LANDING STATE */}
      {messages.length === 0 && (
        <main className="flex-1 flex items-center justify-center px-4 py-12 relative">
          <div className="max-w-4xl w-full text-center">
            
            {/* Clean Icon */}
            <div className="relative inline-flex items-center justify-center mb-6 animate-scale-in">
              <div className="w-16 h-16 rounded-2xl bg-white flex items-center justify-center shadow-xl">
                <BarChart3 className="w-8 h-8 text-black" strokeWidth={2.5} />
              </div>
            </div>

            <div className="animate-fade-in-up space-y-3" style={{animationDelay: '100ms', animationFillMode: 'both'}}>
              <h2 className="text-4xl md:text-5xl font-bold tracking-tight leading-tight text-white">
                AI-Powered Financial Intelligence
              </h2>

              <p className="text-sm text-neutral-400 max-w-xl mx-auto leading-relaxed">
                Get instant insights on companies, markets, and trends with advanced AI analysis
              </p>
            </div>

            {/* Feature Pills */}
            <div className="flex flex-wrap justify-center gap-2 my-6 animate-fade-in-up" style={{animationDelay: '200ms', animationFillMode: 'both'}}>
              {[
                { icon: Zap, text: "Real-time Data" },
                { icon: Shield, text: "Secure Analysis" },
                { icon: Activity, text: "Live Markets" },
              ].map((feature, i) => (
                <div
                  key={i}
                  className="px-3 py-1.5 rounded-full bg-neutral-900/50 border border-neutral-800/50 text-xs font-medium text-neutral-300 flex items-center gap-1.5"
                >
                  <feature.icon className="w-3 h-3" />
                  {feature.text}
                </div>
              ))}
            </div>

            {/* Query Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-w-2xl mx-auto animate-fade-in-up" style={{animationDelay: '300ms', animationFillMode: 'both'}}>
              {[
                { q: "Top tech companies overview", icon: Building2 },
                { q: "Tesla risk assessment", icon: Shield },
                { q: "Apple vs Microsoft comparison", icon: Scale },
                { q: "Nvidia trend analysis", icon: LineChart },
              ].map((item, i) => (
                <button
                  key={i}
                  onClick={() => setInput(item.q)}
                  className="group relative overflow-hidden px-4 py-3 rounded-xl text-left
                             bg-neutral-900/30 backdrop-blur-sm border border-neutral-800/50
                             hover:bg-neutral-900/50 hover:border-neutral-700
                             transition-all duration-300 hover:scale-[1.02]"
                >
                  <div className="relative flex items-center gap-3">
                    <item.icon className="w-4 h-4 text-neutral-500 group-hover:text-neutral-300 transition-colors" />
                    <span className="text-xs font-medium text-neutral-300 group-hover:text-white transition-colors flex-1">
                      {item.q}
                    </span>
                    <ArrowRight className="w-3 h-3 text-neutral-600 group-hover:text-neutral-400 transition-colors" />
                  </div>
                </button>
              ))}
            </div>
          </div>
        </main>
      )}

      {/* CHAT CONVERSATION */}
      {messages.length > 0 && (
        <div className="flex-1 overflow-y-auto px-4 py-6 relative">
          <div className="max-w-4xl mx-auto space-y-4">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex animate-slide-up ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
                style={{animationDelay: `${i * 40}ms`, animationFillMode: 'both'}}
              >
                <div
                  className={`max-w-[80%] ${
                    msg.role === "user"
                      ? "bg-white text-black rounded-2xl px-4 py-2.5 shadow-lg text-sm font-medium"
                      : "bg-neutral-900/50 backdrop-blur-sm rounded-2xl px-4 py-3 shadow-lg border border-neutral-800/50"
                  }`}
                >
                  {msg.role === "assistant" ? (
                    <RenderMessage content={msg.content} />
                  ) : (
                    <p className="text-sm leading-relaxed">{msg.content}</p>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start animate-fade-in">
                <div className="bg-neutral-900/50 backdrop-blur-sm rounded-2xl px-4 py-3 shadow-lg border border-neutral-800/50">
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1">
                      <div className="w-1.5 h-1.5 rounded-full bg-white animate-bounce" style={{animationDelay: '0ms'}} />
                      <div className="w-1.5 h-1.5 rounded-full bg-white animate-bounce" style={{animationDelay: '150ms'}} />
                      <div className="w-1.5 h-1.5 rounded-full bg-white animate-bounce" style={{animationDelay: '300ms'}} />
                    </div>
                    <span className="text-xs text-neutral-400 ml-1">Analyzing...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        </div>
      )}

      {/* INPUT BAR */}
      <footer className="sticky bottom-0 p-4 relative z-10">
        <div className="max-w-4xl mx-auto">
          <div className="relative group">
            <div className="relative flex items-center gap-2 
                            bg-neutral-900/80 backdrop-blur-xl rounded-2xl 
                            shadow-xl border border-neutral-800/50
                            group-focus-within:border-neutral-700
                            transition-all duration-300 p-2">
              <Search className="w-4 h-4 text-neutral-500 ml-2" />
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                placeholder="Ask about markets, companies, trends..."
                className="flex-1 px-2 py-2.5 bg-transparent text-white placeholder-neutral-500 text-sm outline-none"
              />
              <button
                onClick={sendMessage}
                disabled={loading || !input.trim()}
                className="px-4 py-2.5 rounded-xl bg-white text-black text-xs font-semibold
                           shadow-lg hover:shadow-xl hover:scale-[1.02] active:scale-[0.98]
                           disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100
                           transition-all duration-200 flex items-center gap-1.5"
              >
                Send
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>
      </footer>

      {/* ANIMATIONS */}
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(30px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes scaleIn {
          from { opacity: 0; transform: scale(0.95); }
          to { opacity: 1; transform: scale(1); }
        }
        
        .animate-fade-in { animation: fadeIn 0.5s ease-out; }
        .animate-slide-up { animation: slideUp 0.4s ease-out; }
        .animate-fade-in-up { animation: fadeInUp 0.6s ease-out; }
        .animate-scale-in { animation: scaleIn 0.6s ease-out; }
      `}</style>
    </div>
  );
}