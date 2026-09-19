"use client";

import { useEffect, useRef, useState } from "react";
import { Mic, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/cn";

export interface VoiceRecorderHandle {
  recording: boolean;
  supported: boolean;
}

/**
 * Accessible microphone control. Capatures one audio blob and hands it to
 * `onCaptured`. Falls back through `onUnsupported` (no microphone / not a
 * secure context) so callers can offer a typed-transcript alternative.
 */
export function VoiceRecorder({
  onCaptured,
  onUnsupported,
  onError,
}: {
  onCaptured: (blob: Blob) => void;
  onUnsupported?: () => void;
  onError?: (message: string) => void;
}) {
  const [recording, setRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);
  const onCapturedRef = useRef(onCaptured);
  const onErrorRef = useRef(onError);

  useEffect(() => {
    onCapturedRef.current = onCaptured;
    onErrorRef.current = onError;
  });

  useEffect(() => {
    return () => {
      if (timerRef.current !== null) window.clearInterval(timerRef.current);
      if (mediaRef.current && mediaRef.current.state !== "inactive") {
        mediaRef.current.stop();
      }
    };
  }, []);

  async function start() {
    if (!("mediaDevices" in navigator) || !navigator.mediaDevices?.getUserMedia) {
      onUnsupported?.();
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        const type = recorder.mimeType || "audio/webm";
        const blob = new Blob(chunksRef.current, { type });
        stream.getTracks().forEach((track) => track.stop());
        if (seconds < 1) {
          onErrorRef.current?.("Recording was too short to use. Please try again.");
        } else if (blob.size === 0) {
          onErrorRef.current?.("Nothing was recorded. Please try again.");
        } else {
          onCapturedRef.current(blob);
        }
        setSeconds(0);
      };
      mediaRef.current = recorder;
      recorder.start();
      setRecording(true);
      setSeconds(0);
      timerRef.current = window.setInterval(() => {
        setSeconds((value) => value + 1);
      }, 1000);
    } catch {
      onUnsupported?.();
    }
  }

  function stop() {
    if (!mediaRef.current || mediaRef.current.state === "inactive") return;
    if (timerRef.current !== null) window.clearInterval(timerRef.current);
    timerRef.current = null;
    setRecording(false);
    mediaRef.current.stop();
  }

  const busy = recording;
  return (
    <div className="space-y-2">
      <div
        className={cn(
          "flex items-center gap-3 rounded-md border px-3 py-2.5",
          busy ? "border-brand-300 bg-brand-50" : "border-line-strong bg-surface",
        )}
      >
        <span
          className={cn(
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
            busy ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-500",
          )}
          aria-hidden
        >
          {busy ? <Square className="h-3.5 w-3.5 fill-current" /> : <Mic className="h-4 w-4" />}
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-slate-800">
            {busy ? "Recording…" : "Record a spoken update"}
          </p>
          <p className="text-xs text-muted" aria-live="polite">
            {busy ? `${seconds}s elapsed` : "Tap record, speak, then tap stop."}
          </p>
        </div>
        <Button
          type="button"
          variant={busy ? "secondary" : "primary"}
          size="sm"
          onClick={busy ? stop : undefined}
          onMouseDown={(event) => {
            if (!busy) {
              event.preventDefault();
              void start();
            }
          }}
          disabled={false}
          aria-label={busy ? "Stop recording" : "Start recording"}
        >
          {busy ? "Stop" : "Record"}
        </Button>
      </div>
    </div>
  );
}