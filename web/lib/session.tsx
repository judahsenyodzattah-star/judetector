"use client";

/**
 * Session memory for the current visit only.
 *
 * The chosen image and its result live in React state and object URLs: nothing
 * is persisted to browser storage, cookies or the server, so a reload starts
 * clean. That is a deliberate limit, not an unfinished feature — an analysis
 * history would outlive the visitor's intent.
 */

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import type { DetectResponse } from "./contracts";

export interface StagedImage {
  file: File;
  url: string;
  name: string;
  size: number;
}

export interface Thresholds {
  confidence: number;
  iou: number;
}

export interface SessionValue {
  staged: StagedImage | null;
  result: DetectResponse | null;
  thresholds: Thresholds;
  includeAnnotated: boolean;
  stage: (file: File) => void;
  clearStaged: () => void;
  setThresholds: (next: Partial<Thresholds>) => void;
  setIncludeAnnotated: (value: boolean) => void;
  setResult: (result: DetectResponse | null) => void;
  reset: () => void;
}

export const DEFAULT_THRESHOLDS: Thresholds = { confidence: 0.25, iou: 0.45 };

const SessionContext = createContext<SessionValue | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [staged, setStaged] = useState<StagedImage | null>(null);
  const [result, setResult] = useState<DetectResponse | null>(null);
  const [thresholds, setThresholdsState] = useState<Thresholds>(DEFAULT_THRESHOLDS);
  const [includeAnnotated, setIncludeAnnotated] = useState(true);
  const urlRef = useRef<string | null>(null);

  const releaseUrl = useCallback(() => {
    if (urlRef.current) {
      URL.revokeObjectURL(urlRef.current);
      urlRef.current = null;
    }
  }, []);

  const stage = useCallback(
    (file: File) => {
      releaseUrl();
      const url = URL.createObjectURL(file);
      urlRef.current = url;
      setStaged({ file, url, name: file.name, size: file.size });
      setResult(null);
    },
    [releaseUrl],
  );

  const clearStaged = useCallback(() => {
    releaseUrl();
    setStaged(null);
  }, [releaseUrl]);

  const setThresholds = useCallback((next: Partial<Thresholds>) => {
    setThresholdsState((current) => ({ ...current, ...next }));
  }, []);

  const reset = useCallback(() => {
    releaseUrl();
    setStaged(null);
    setResult(null);
    setThresholdsState(DEFAULT_THRESHOLDS);
    setIncludeAnnotated(true);
  }, [releaseUrl]);

  const value = useMemo<SessionValue>(
    () => ({
      staged,
      result,
      thresholds,
      includeAnnotated,
      stage,
      clearStaged,
      setThresholds,
      setIncludeAnnotated,
      setResult,
      reset,
    }),
    [staged, result, thresholds, includeAnnotated, stage, clearStaged, setThresholds, setResult, reset],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession(): SessionValue {
  const value = useContext(SessionContext);
  if (!value) throw new Error("useSession must be used inside SessionProvider");
  return value;
}
