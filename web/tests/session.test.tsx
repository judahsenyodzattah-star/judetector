import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { detectResponse, fileOf, renderWithSession } from "./helpers";
import { useSession } from "@/lib/session";

function Probe() {
  const session = useSession();
  return (
    <div>
      <span data-testid="staged">{session.staged?.name ?? "none"}</span>
      <span data-testid="result">{session.result ? String(session.result.count) : "none"}</span>
      <span data-testid="thresholds">
        {session.thresholds.confidence}/{session.thresholds.iou}
      </span>
      <button type="button" onClick={() => session.stage(fileOf("first.png"))}>
        stage first
      </button>
      <button type="button" onClick={() => session.stage(fileOf("second.png"))}>
        stage second
      </button>
      <button type="button" onClick={() => session.setResult(detectResponse)}>
        set result
      </button>
      <button type="button" onClick={() => session.reset()}>
        reset
      </button>
    </div>
  );
}

describe("session memory", () => {
  it("starts empty, with the API's default thresholds", () => {
    renderWithSession(<Probe />);
    expect(screen.getByTestId("staged")).toHaveTextContent("none");
    expect(screen.getByTestId("result")).toHaveTextContent("none");
    expect(screen.getByTestId("thresholds")).toHaveTextContent("0.25/0.45");
  });

  it("keeps one staged image and releases the previous preview", async () => {
    const create = vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:first");
    const revoke = vi.spyOn(URL, "revokeObjectURL");

    renderWithSession(<Probe />);
    await userEvent.click(screen.getByRole("button", { name: "stage first" }));
    expect(screen.getByTestId("staged")).toHaveTextContent("first.png");
    expect(create).toHaveBeenCalledTimes(1);

    await userEvent.click(screen.getByRole("button", { name: "stage second" }));
    expect(screen.getByTestId("staged")).toHaveTextContent("second.png");
    expect(revoke).toHaveBeenCalledWith("blob:first");
  });

  it("drops a result when a different image is staged", async () => {
    renderWithSession(<Probe />);
    await userEvent.click(screen.getByRole("button", { name: "set result" }));
    expect(screen.getByTestId("result")).toHaveTextContent("2");

    await userEvent.click(screen.getByRole("button", { name: "stage second" }));
    expect(screen.getByTestId("result")).toHaveTextContent("none");
  });

  it("writes nothing to browser storage", async () => {
    const local = vi.spyOn(Storage.prototype, "setItem");
    const session = vi.spyOn(Storage.prototype, "setItem");

    renderWithSession(<Probe />);
    await userEvent.click(screen.getByRole("button", { name: "stage first" }));
    await userEvent.click(screen.getByRole("button", { name: "set result" }));

    expect(local).not.toHaveBeenCalled();
    expect(session).not.toHaveBeenCalled();
    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
  });

  it("clears everything on reset", async () => {
    renderWithSession(<Probe />);
    await userEvent.click(screen.getByRole("button", { name: "stage first" }));
    await userEvent.click(screen.getByRole("button", { name: "set result" }));
    await userEvent.click(screen.getByRole("button", { name: "reset" }));

    expect(screen.getByTestId("staged")).toHaveTextContent("none");
    expect(screen.getByTestId("result")).toHaveTextContent("none");
    expect(screen.getByTestId("thresholds")).toHaveTextContent("0.25/0.45");
  });
});
