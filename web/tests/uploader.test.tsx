import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { Uploader } from "@/components/uploader";

import { fileOf } from "./helpers";

function input(): HTMLInputElement {
  return screen.getByLabelText("Choose an image file") as HTMLInputElement;
}

describe("image selection", () => {
  it("hands a supported image to the caller and analyses nothing itself", async () => {
    const onSelect = vi.fn();
    render(<Uploader onSelect={onSelect} />);

    expect(onSelect).not.toHaveBeenCalled();

    await userEvent.upload(input(), fileOf("portrait.png"));

    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect.mock.calls[0][0].name).toBe("portrait.png");
  });

  it("accepts a file dropped on the zone", () => {
    const onSelect = vi.fn();
    render(<Uploader onSelect={onSelect} />);

    const zone = screen.getByText("Choose an image to analyse").closest(".uploader")!;
    fireEvent.dragOver(zone, { dataTransfer: { files: [fileOf("photo.jpg", { type: "image/jpeg" })] } });
    fireEvent.drop(zone, {
      dataTransfer: { files: [fileOf("photo.jpg", { type: "image/jpeg" })] },
    });

    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect.mock.calls[0][0].name).toBe("photo.jpg");
  });

  it("refuses an unsupported file type before anything is sent", () => {
    const onSelect = vi.fn();
    render(<Uploader onSelect={onSelect} />);

    fireEvent.change(input(), { target: { files: [fileOf("portrait.heic", { type: "image/heic" })] } });

    expect(onSelect).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent("That file type is not supported");
    expect(screen.getByRole("alert")).toHaveTextContent("JPG, PNG, WEBP or BMP");
  });

  it("refuses an image above 25 MB and states the limit", () => {
    const onSelect = vi.fn();
    render(<Uploader onSelect={onSelect} />);

    fireEvent.change(input(), {
      target: { files: [fileOf("huge.png", { size: 26 * 1024 * 1024 })] },
    });

    expect(onSelect).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent("The limit is 25 MB");
  });

  it("clears the refusal once a usable file is chosen", () => {
    const onSelect = vi.fn();
    render(<Uploader onSelect={onSelect} />);

    fireEvent.change(input(), { target: { files: [fileOf("notes.txt", { type: "text/plain" })] } });
    expect(screen.getByRole("alert")).toBeInTheDocument();

    fireEvent.change(input(), { target: { files: [fileOf("photo.png")] } });

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(onSelect).toHaveBeenCalledTimes(1);
  });
});
