/**
 * Source-level guards for promises the interface makes.
 *
 * These are cheap and blunt on purpose: they fail when someone adds storage,
 * a fabricated stat or a breakpoint that skips a device class.
 */

import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

import { MAX_UPLOAD_BYTES } from "@/lib/limits";

/** Vitest runs with the package root as its working directory. */
const ROOT = process.cwd();

function walk(directory: string): string[] {
  return readdirSync(directory).flatMap((entry) => {
    const full = join(directory, entry);
    return statSync(full).isDirectory() ? walk(full) : [full];
  });
}

const SOURCE_FILES = ["app", "components", "lib"]
  .flatMap((directory) => walk(join(ROOT, directory)))
  .filter((file) => /\.(ts|tsx)$/.test(file));

describe("privacy", () => {
  it("never writes images or results to browser storage", () => {
    for (const file of SOURCE_FILES) {
      const source = readFileSync(file, "utf8");
      expect(source, file).not.toMatch(/localStorage|sessionStorage|indexedDB/);
    }
  });

  it("holds the upload limit at 25 MB", () => {
    expect(MAX_UPLOAD_BYTES).toBe(25 * 1024 * 1024);
  });
});

describe("no fabricated content", () => {
  const BANNED = [
    /accuracy/i,
    /\b99\.\d\s?%/,
    /state-of-the-art/i,
    /AI[- ]powered/i,
    /military-grade/i,
    /revolutionary/i,
    /trusted by/i,
  ];

  it("keeps marketing numbers and claims out of the interface", () => {
    for (const file of SOURCE_FILES) {
      const source = readFileSync(file, "utf8");
      for (const pattern of BANNED) {
        expect(source, `${file} matches ${pattern}`).not.toMatch(pattern);
      }
    }
  });

  it("ships no placeholder imagery", () => {
    for (const file of SOURCE_FILES) {
      const source = readFileSync(file, "utf8");
      expect(source, file).not.toMatch(/placehold\.|placeholder\.com|dummyimage|unsplash/i);
    }
  });
});

describe("responsive rules", () => {
  const css = readFileSync(join(ROOT, "app/globals.css"), "utf8");

  it("defines the tablet and mobile breakpoints explicitly", () => {
    expect(css).toMatch(/@media \(max-width: 1023px\)/);
    expect(css).toMatch(/@media \(max-width: 639px\)/);
    expect(css).toMatch(/@media \(min-width: 1024px\)/);
  });

  it("hides the rail and the top bar in mutually exclusive ranges", () => {
    expect(css).toMatch(/\.rail\s*\{\s*display: none;/);
    expect(css).toMatch(/\.topbar\s*\{\s*display: none;/);
  });

  it("respects a reduced-motion preference", () => {
    expect(css).toMatch(/prefers-reduced-motion/);
  });
});

describe("the upload path is documented, not assumed", () => {
  it("routes production uploads directly to the API", () => {
    const source = readFileSync(join(ROOT, "lib/api.ts"), "utf8");
    expect(source).toMatch(/454|4\.5 MB|VERCEL_BODY_LIMIT/);
    expect(source).toMatch(/NEXT_PUBLIC_API_BASE_URL/);
  });

  it("makes the proxy refuse rather than fail opaquely on Vercel", () => {
    const source = readFileSync(join(ROOT, "app/api/detect/route.ts"), "utf8");
    expect(source).toMatch(/VERCEL_BODY_LIMIT/);
    expect(source).toMatch(/upload_over_proxy_limit/);
  });
});
