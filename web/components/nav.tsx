"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { CameraIcon, HelpIcon, HomeIcon, ScanIcon } from "./icons";

export interface NavItem {
  href: string;
  label: string;
  icon: (props: { className?: string }) => React.ReactElement;
}

export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Home", icon: HomeIcon },
  { href: "/detect", label: "Detect", icon: ScanIcon },
  { href: "/camera", label: "Camera", icon: CameraIcon },
  { href: "/help", label: "Help", icon: HelpIcon },
];

function isActive(pathname: string | null, href: string): boolean {
  if (!pathname) return false;
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

function NavList({ pathname, className }: { pathname: string | null; className?: string }) {
  return (
    <ul className={className ?? "rail__nav"} style={{ listStyle: "none" }}>
      {NAV_ITEMS.map(({ href, label, icon: Icon }) => (
        <li key={href}>
          <Link
            href={href}
            className="nav-link"
            aria-current={isActive(pathname, href) ? "page" : undefined}
          >
            <Icon />
            <span>{label}</span>
          </Link>
        </li>
      ))}
    </ul>
  );
}

export function RailNav({ modelStatus }: { modelStatus: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <header className="rail">
      <div className="rail__brand">
        <span className="rail__wordmark">JUDEtector</span>
        <span className="rail__tagline">Single-subject detection</span>
      </div>
      <nav aria-label="Sections">
        <p className="rail__section-label">Workspace</p>
        <NavList pathname={pathname} />
      </nav>
      <div className="rail__footer">{modelStatus}</div>
    </header>
  );
}

export function TopNav({ modelStatus }: { modelStatus: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <header className="topbar">
      <div className="topbar__row">
        <span className="rail__wordmark">JUDEtector</span>
        {modelStatus}
      </div>
      <nav aria-label="Sections">
        <NavList pathname={pathname} className="topbar__nav" />
      </nav>
    </header>
  );
}
