import { fireEvent, screen } from "@testing-library/react";

import { HomeView } from "@/components/home-view";

import { card, fileOf, modelInfo, modelInfoDegraded, renderWithSession } from "./helpers";

const { pushMock } = vi.hoisted(() => ({ pushMock: vi.fn() }));

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
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
  default: ({ href, children, ...rest }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

beforeEach(() => {
  pushMock.mockReset();
});

describe("home", () => {
  it("leads with one uploader and keeps the session panel compact", () => {
    renderWithSession(<HomeView modelInfo={modelInfo()} />);

    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Check a photo for the trained subject",
    );
    expect(screen.getByText("Choose an image to analyse")).toBeInTheDocument();
    expect(screen.getByText("No image yet. Choosing one here stages it for Detect — it is not analysed until you ask.")).toBeInTheDocument();
    expect(screen.getByText(/No analysis yet/)).toBeInTheDocument();
  });

  it("states the format and size limits where the file is chosen", () => {
    renderWithSession(<HomeView modelInfo={modelInfo()} />);
    expect(
      screen.getByText("Drag a file here, or use the button below. JPG, PNG, WEBP or BMP, up to 25 MB."),
    ).toBeInTheDocument();
  });

  it("stages the image and moves to Detect without analysing it", () => {
    renderWithSession(<HomeView modelInfo={modelInfo()} />);

    fireEvent.change(screen.getByLabelText("Choose an image file"), {
      target: { files: [fileOf("portrait.png")] },
    });

    expect(pushMock).toHaveBeenCalledWith("/detect");
    expect(screen.getByText("portrait.png")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open in Detect" })).toHaveAttribute("href", "/detect");
  });

  it("publishes the model's limitations on the page that starts analysis", () => {
    renderWithSession(<HomeView modelInfo={modelInfo()} />);
    expect(screen.getByText(card.limitations)).toBeInTheDocument();
    expect(screen.getByText("Subject-specific")).toBeInTheDocument();
  });

  it("shows the unavailable state instead of an empty promise", () => {
    renderWithSession(<HomeView modelInfo={modelInfoDegraded()} />);
    expect(screen.getByText("Analysis is unavailable")).toBeInTheDocument();
    expect(screen.getByText(/no result will be invented/i)).toBeInTheDocument();
  });
});
