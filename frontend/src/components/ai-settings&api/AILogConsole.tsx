// src/components/AILogConsole.tsx
import React, { useEffect, useRef, useState } from "react";
import { Cpu, AlertTriangle } from "lucide-react";

const API_BASE_URL = process.env.REACT_APP_API_URL;
const WS_URL = "ws://http://127.0.0.1:8000/api/ws/ai-logs";

const AILogConsole: React.FC = () => {
  const [logs, setLogs] = useState<string[]>([]);
  const [status, setStatus] = useState<"running" | "stopped" | "unknown">("unknown");
  const [wsConnected, setWsConnected] = useState(false);
  const [aiRunning, setAiRunning] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  // --- ดึงสถานะ AI จาก backend ---
  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/ai/status`);
      const data = await res.json();
      const s = (data.status as "running" | "stopped") ?? "unknown";
      setStatus(s);
      setAiRunning(s === "running");
    } catch {
      setStatus("unknown");
      setAiRunning(false);
    }
  };

  // --- start/stop AI ---
  const startAI = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/ai/start`, { method: "POST" });
      if (!res.ok) {
        const err = await res.json();
        alert(`เริ่ม AI ไม่ได้: ${err.detail ?? res.statusText}`);
        return;
      }
      setLogs((prev) => [...prev, ">> START requested"]);
      setStatus("running");
      setAiRunning(true);
      alert("✅ AI Started");
    } catch {
      alert("❌ เริ่ม AI ไม่ได้");
    }
  };

  const stopAI = async () => {
    if (!window.confirm("คุณแน่ใจหรือไม่ว่าต้องการหยุด AI ?")) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/ai/stop`, { method: "POST" });
      if (!res.ok) {
        const err = await res.json();
        alert(`หยุด AI ไม่ได้: ${err.detail ?? res.statusText}`);
        return;
      }
      setLogs((prev) => [...prev, ">> STOP requested"]);
      setStatus("stopped");
      setAiRunning(false);
      alert("🛑 AI Stopped");
    } catch {
      alert("❌ หยุด AI ไม่ได้");
    }
  };

  // --- ครั้งแรก โหลด status ---
  useEffect(() => {
    fetchStatus();
  }, []);

  // --- จัดการ websocket logs ---
  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      setWsConnected(true);
      const keepAlive = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send("ping");
        }
      }, 2000);
      (ws as any)._keepAlive = keepAlive;
    };

    ws.onmessage = (ev) => {
      setLogs((prev) => {
        const next = [...prev, ev.data as string];
        if (next.length > 2000) next.splice(0, next.length - 2000);
        return next;
      });
      if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      }
    };

    ws.onclose = () => {
      setWsConnected(false);
      if ((ws as any)._keepAlive) clearInterval((ws as any)._keepAlive);
      // auto reconnect
      setTimeout(() => {
        if (wsRef.current === ws) wsRef.current = null;
      }, 1500);
    };

    ws.onerror = () => {
      setWsConnected(false);
    };

    return () => {
      if (ws) {
        if ((ws as any)._keepAlive) clearInterval((ws as any)._keepAlive);
        ws.close();
      }
    };
  }, []);

  return (
    <div className="bg-white rounded-xl shadow-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold">AI Realtime Logs</h3>
        <div className="flex items-center gap-2">
          <span
            className={`px-2 py-1 rounded text-sm ${
              status === "running" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-700"
            }`}
          >
            {status === "running" ? "RUNNING" : status.toUpperCase()}
          </span>
          <span
            className={`px-2 py-1 rounded text-sm ${
              wsConnected ? "bg-blue-100 text-blue-700" : "bg-gray-100 text-gray-700"
            }`}
          >
            WS: {wsConnected ? "CONNECTED" : "DISCONNECTED"}
          </span>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="font-mono text-sm bg-black text-green-200 rounded p-3 h-72 overflow-auto"
        style={{ whiteSpace: "pre-wrap" }}
      >
        {logs.join("\n")}
      </div>

      <div className="mt-3 flex gap-3">
        {!aiRunning ? (
          <button
            onClick={startAI}
            className="flex items-center space-x-2 bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 transition-colors shadow-lg"
          >
            <Cpu size={20} />
            <span>Start AI</span>
          </button>
        ) : (
          <button
            onClick={stopAI}
            className="flex items-center space-x-2 bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 transition-colors shadow-lg"
          >
            <AlertTriangle size={20} />
            <span>Stop AI</span>
          </button>
        )}
      </div>
    </div>
  );
};

export default AILogConsole;
