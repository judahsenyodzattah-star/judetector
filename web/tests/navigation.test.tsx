import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AppShell } from "@/components/app-shell";

import { mockViewport, modelInfo, modelInfoDegraded, renderWithSession } from "./helpers";

const { pathMock, pushMock } = vi.hoisted(() => ({
  pathMock: { current: "/detect" },
  pushMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => pathMock.current,
  useRouter: () => ({
    push: pushMock,
    replace: vi.fn(),
    prefetch: vi.fn(),
    refresh: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
  }),
}));

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...rest
  }: {
    href: string;
    children: React.ReactNode;
  } & React.AnchorHTMLAttributes<HTMLAnchorElement>) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

function shell(info = modelInfo()) {
  return renderWithSession(
    <AppShell modelInfo={info}>
      <p>workspace</p>
    </AppShell>,
  );
}

describe("navigation", () => {
  it("offers the four destinations in the rail on a desktop viewport", () => {
    mockViewport(1440);
    shell();

    const nav = screen.getByRole("navigation", { name: "Sections" });
    const links = within(nav).getAllByRole("link");
    expect(links.map((link) => link.textContent)).toEqual(["Home", "Detect", "Camera", "Help"]);
    expect(links.map((link) => link.getAttribute("href"))).toEqual([
      "/",
      "/detect",
      "/camera",
      "/help",
    ]);
  });

  it("marks only the current section as the current page", () => {
    mockViewport(1440);
    pathMock.current = "/detect";
    shell();

    const nav = screen.getByRole("navigation", { name: "Sections" });
    expect(within(nav).getByRole("link", { name: "Detect" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(within(nav).getByRole("link", { name: "Home" })).not.toHaveAttribute("aria-current");
  });

  it("treats nested routes as their section", () => {
    mockViewport(1440);
    pathMock.current = "/help/shortcuts";
    shell();

    const nav = screen.getByRole("navigation", { name: "Sections" });
    expect(within(nav).getByRole("link", { name: "Help" })).toHaveAttribute("aria-current", "page");
  });

  it("swaps the rail for a top bar on tablet and mobile", () => {
    mockViewport(820);
    const { container } = shell();

    expect(container.querySelector(".rail")).toBeNull();
    expect(container.querySelector(".topbar")).not.toBeNull();
    expect(screen.getByRole("navigation", { name: "Sections" })).toBeInTheDocument();
  });

  it("keeps the same destinations on mobile", () => {
    mockViewport(375);
    shell();

    const nav = screen.getByRole("navigation", { name: "Sections" });
    expect(within(nav).getAllByRole("link")).toHaveLength(4);
  });

  it("navigates with a link, not a scripted redirect", async () => {
    mockViewport(1440);
    shell();

    const nav = screen.getByRole("navigation", { name: "Sections" });
    await userEvent.click(within(nav).getByRole("link", { name: "Camera" }));

    expect(pushMock).not.toHaveBeenCalled();
    expect(within(nav).getByRole("link", { name: "Camera" })).toHaveAttribute("href", "/camera");
  });
});

describe("model status in the shell", () => {
  it("says the model is available only when the service says so", () => {
    mockViewport(1440);
    shell();
    expect(screen.getByText("Model available")).toBeInTheDocument();
  });

  it("says unavailable when the model is not loaded", () => {
    mockViewport(1440);
    shell(modelInfoDegraded());
    expect(screen.getByText("Model unavailable")).toBeInTheDocument();
  });

  it("says unknown rather than guessing when the service cannot be read", () => {
    mockViewport(1440);
    shell({ health: null, card: null, serviceReachable: false });
    expect(screen.getByText("Status unknown")).toBeInTheDocument();
  });
});
