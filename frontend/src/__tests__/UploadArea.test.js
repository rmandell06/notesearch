import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import UploadArea from "../components/UploadArea";
import * as api from "../api";

jest.mock("../api");

afterEach(() => jest.resetAllMocks());

describe("UploadArea", () => {
  it("renders the upload area", () => {
    render(<UploadArea />);
    expect(screen.getByRole("region", { name: /file upload area/i })).toBeInTheDocument();
  });

  it("shows uploaded filename after selecting a file", async () => {
    api.uploadFile.mockResolvedValue({ id: "1" });
    render(<UploadArea />);
    const input = screen.getByTestId("file-input");
    fireEvent.change(input, { target: { files: [new File(["hello"], "meeting-notes.txt", { type: "text/plain" })] } });
    expect(screen.getByTestId("file-name")).toHaveTextContent("meeting-notes.txt");
  });

  it("shows multiple uploaded filenames", async () => {
    api.uploadFile.mockResolvedValue({ id: "1" });
    render(<UploadArea />);
    const input = screen.getByTestId("file-input");
    const files = [
      new File(["a"], "note-a.md", { type: "text/markdown" }),
      new File(["b"], "note-b.md", { type: "text/markdown" }),
    ];
    fireEvent.change(input, { target: { files } });
    const names = screen.getAllByTestId("file-name");
    expect(names).toHaveLength(2);
    expect(names[0]).toHaveTextContent("note-a.md");
    expect(names[1]).toHaveTextContent("note-b.md");
  });

  it("removes a file when the remove button is clicked", async () => {
    api.uploadFile.mockResolvedValue({ id: "1" });
    render(<UploadArea />);
    const input = screen.getByTestId("file-input");
    fireEvent.change(input, { target: { files: [new File(["x"], "removable.txt", { type: "text/plain" })] } });
    const removeBtn = screen.getByRole("button", { name: /remove removable\.txt/i });
    fireEvent.click(removeBtn);
    expect(screen.queryByTestId("file-name")).not.toBeInTheDocument();
  });

  it("calls uploadFile with the selected file", async () => {
    api.uploadFile.mockResolvedValue({ id: "abc" });
    render(<UploadArea />);
    const file = new File(["content"], "research.md", { type: "text/markdown" });
    fireEvent.change(screen.getByTestId("file-input"), { target: { files: [file] } });
    await waitFor(() => expect(api.uploadFile).toHaveBeenCalledWith(file));
  });

  it("shows uploading status while request is in flight", async () => {
    api.uploadFile.mockReturnValue(new Promise(() => {}));
    render(<UploadArea />);
    fireEvent.change(screen.getByTestId("file-input"), {
      target: { files: [new File(["x"], "pending.txt")] },
    });
    await waitFor(() =>
      expect(screen.getByTestId("file-status-0")).toHaveTextContent("uploading...")
    );
  });

  it("shows done status after successful upload", async () => {
    api.uploadFile.mockResolvedValue({ id: "new" });
    render(<UploadArea />);
    fireEvent.change(screen.getByTestId("file-input"), {
      target: { files: [new File(["x"], "success.txt")] },
    });
    await waitFor(() =>
      expect(screen.getByTestId("file-status-0")).toHaveTextContent("done")
    );
  });

  it("shows error status when upload fails", async () => {
    api.uploadFile.mockRejectedValue(new Error("413 too large"));
    render(<UploadArea />);
    fireEvent.change(screen.getByTestId("file-input"), {
      target: { files: [new File(["x"], "huge.pdf")] },
    });
    await waitFor(() =>
      expect(screen.getByTestId("file-status-0")).toHaveTextContent("413 too large")
    );
  });
});
