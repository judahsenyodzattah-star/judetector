/** One icon family: 20px, 1.6 stroke, round caps. Hand-drawn paths, no icon package. */

import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

function Base({ children, ...props }: IconProps & { children: React.ReactNode }) {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      {...props}
    >
      {children}
    </svg>
  );
}

export function HomeIcon(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M4 10.5 12 4l8 6.5" />
      <path d="M6 9.5V20h12V9.5" />
      <path d="M10 20v-5h4v5" />
    </Base>
  );
}

export function ScanIcon(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M4 8V5.5A1.5 1.5 0 0 1 5.5 4H8" />
      <path d="M16 4h2.5A1.5 1.5 0 0 1 20 5.5V8" />
      <path d="M20 16v2.5a1.5 1.5 0 0 1-1.5 1.5H16" />
      <path d="M8 20H5.5A1.5 1.5 0 0 1 4 18.5V16" />
      <path d="M4 12h16" />
    </Base>
  );
}

export function CameraIcon(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M4 8.5A1.5 1.5 0 0 1 5.5 7h1.8l1.1-1.6h5.2L14.7 7h1.8A1.5 1.5 0 0 1 18 8.5v8A1.5 1.5 0 0 1 16.5 18h-11A1.5 1.5 0 0 1 4 16.5z" />
      <circle cx="11" cy="12.5" r="2.6" />
    </Base>
  );
}

export function HelpIcon(props: IconProps) {
  return (
    <Base {...props}>
      <circle cx="12" cy="12" r="8" />
      <path d="M9.6 9.4a2.4 2.4 0 1 1 3.4 2.4c-.7.4-1 1-1 1.7" />
      <path d="M12 16.6h.01" />
    </Base>
  );
}

export function UploadIcon(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M12 16V5" />
      <path d="m8 8.5 4-3.5 4 3.5" />
      <path d="M5 15v3a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-3" />
    </Base>
  );
}

export function DownloadIcon(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M12 5v10" />
      <path d="m8 11.5 4 3.5 4-3.5" />
      <path d="M5 19h14" />
    </Base>
  );
}

export function AlertIcon(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M12 4.8 20 19H4z" />
      <path d="M12 10v4" />
      <path d="M12 16.8h.01" />
    </Base>
  );
}

export function CheckIcon(props: IconProps) {
  return (
    <Base {...props}>
      <path d="m5 12.5 4.5 4.5L19 7" />
    </Base>
  );
}
