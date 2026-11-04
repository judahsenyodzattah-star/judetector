"use client";

import { useId, useRef, useState, type DragEvent } from "react";

import { ACCEPT_ATTRIBUTE, FORMAT_LABEL, rejectionFor } from "@/lib/limits";

import { UploadIcon } from "./icons";

export interface UploaderProps {
  onSelect: (file: File) => void;
  /** Extra line under the control, e.g. the privacy note on Home. */
  note?: string;
  compact?: boolean;
}

export function Uploader({ onSelect, note, compact = false }: UploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const errorId = useId();

  function accept(files: FileList | null) {
    const file = files?.[0];
    if (!file) return;
    const rejection = rejectionFor(file);
    if (rejection) {
      setError(rejection);
      return;
    }
    setError(null);
    onSelect(file);
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    accept(event.dataTransfer?.files ?? null);
  }

  return (
    <div className="stack stack--tight">
      <div
        className="uploader"
        data-dragging={dragging}
        data-compact={compact || undefined}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <UploadIcon className="uploader__icon" width={28} height={28} />
        <p className="uploader__title">Choose an image to analyse</p>
        <p className="uploader__hint">
          Drag a file here, or use the button below. {FORMAT_LABEL}, up to 25 MB.
        </p>
        <div className="uploader__actions">
          <button
            type="button"
            className="button"
            onClick={() => inputRef.current?.click()}
            aria-describedby={error ? errorId : undefined}
          >
            Browse files
          </button>
        </div>
        <input
          ref={inputRef}
          className="uploader__input"
          type="file"
          accept={ACCEPT_ATTRIBUTE}
          aria-label="Choose an image file"
          onChange={(event) => {
            accept(event.target.files);
            event.target.value = "";
          }}
        />
        {note ? <p className="uploader__note">{note}</p> : null}
      </div>
      {error ? (
        <div className="notice notice--error" role="alert" id={errorId}>
          <p className="notice__title">That file cannot be used</p>
          <p className="notice__detail">{error}</p>
        </div>
      ) : null}
    </div>
  );
}
