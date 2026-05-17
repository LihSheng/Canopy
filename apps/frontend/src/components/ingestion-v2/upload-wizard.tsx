"use client";

import { useCallback, useRef, useState } from "react";
import { uploadFile } from "@/lib/api/ingestion";
import { ErrorState } from "@/components/shared/error-state";

type UploadState =
  | { status: "idle" }
  | { status: "uploading"; progress: number }
  | { status: "success"; uploadId: string; fileName: string }
  | { status: "error"; message: string };

type Props = {
  onUploadComplete?: (uploadId: string) => void;
};

export function UploadWizard({ onUploadComplete }: Props) {
  const [state, setState] = useState<UploadState>({ status: "idle" });
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setState({ status: "uploading", progress: 0 });
      try {
        const result = await uploadFile(file, "herdhr", "payroll");
        setState({
          status: "success",
          uploadId: result.upload_id,
          fileName: result.file_name,
        });
        onUploadComplete?.(result.upload_id);
      } catch (err) {
        setState({
          status: "error",
          message: err instanceof Error ? err.message : "Upload failed",
        });
      }
    },
    [onUploadComplete],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  if (state.status === "success") {
    return (
      <div className="flex flex-col items-center gap-3 rounded-xl border border-green-200 bg-green-50 p-8 text-center">
        <svg viewBox="0 0 20 20" fill="currentColor" className="h-10 w-10 text-green-500">
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
            clipRule="evenodd"
          />
        </svg>
        <p className="text-sm font-semibold text-green-700">{state.fileName} uploaded</p>
        <button
          onClick={() => setState({ status: "idle" })}
          className="text-sm text-zinc-500 underline hover:text-zinc-700"
        >
          Upload another
        </button>
      </div>
    );
  }

  if (state.status === "error") {
    return <ErrorState message={state.message} onRetry={() => setState({ status: "idle" })} />;
  }

  return (
    <div
      onDrop={handleDrop}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      className={`flex cursor-pointer flex-col items-center gap-4 rounded-xl border-2 border-dashed p-10 text-center transition-colors ${
        dragOver
          ? "border-zinc-900 bg-zinc-50"
          : state.status === "uploading"
            ? "border-zinc-300 bg-zinc-50"
            : "border-zinc-300 hover:border-zinc-400"
      }`}
      onClick={() => inputRef.current?.click()}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") inputRef.current?.click(); }}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".xlsx,.xls,.xlsm,.csv"
        className="hidden"
        onChange={handleChange}
      />

      {state.status === "uploading" ? (
        <>
          <svg className="h-8 w-8 animate-spin text-zinc-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <p className="text-sm text-zinc-500">Uploading...</p>
        </>
      ) : (
        <>
          <svg viewBox="0 0 20 20" fill="currentColor" className="h-10 w-10 text-zinc-400">
            <path d="M9.25 13.25a.75.75 0 001.5 0V4.636l2.955 3.129a.75.75 0 001.09-1.03l-4.25-4.5a.75.75 0 00-1.09 0l-4.25 4.5a.75.75 0 101.09 1.03L9.25 4.636V13.25z" />
            <path d="M3.5 12.75a.75.75 0 00-1.5 0v2.5A2.75 2.75 0 004.75 18h10.5A2.75 2.75 0 0018 15.25v-2.5a.75.75 0 00-1.5 0v2.5c0 .69-.56 1.25-1.25 1.25H4.75c-.69 0-1.25-.56-1.25-1.25v-2.5z" />
          </svg>
          <div>
            <p className="text-sm font-semibold text-zinc-700">Drop your workbook here</p>
            <p className="text-xs text-zinc-400">or click to browse — .xlsx, .xls, .xlsm, .csv up to 50 MB</p>
          </div>
        </>
      )}
    </div>
  );
}
