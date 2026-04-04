import { render, screen, fireEvent } from "@testing-library/react";
import UploadArea from "../components/UploadArea";

describe("UploadArea", () => {
  it("renders the upload area", () => {
    render(<UploadArea />);
    expect(screen.getByRole("region", { name: /file upload area/i })).toBeInTheDocument();
  });

  it("shows uploaded filename after selecting a file", () => {
    render(<UploadArea />);
    const input = screen.getByTestId("file-input");
    const file = new File(["hello"], "meeting-notes.txt", { type: "text/plain" });
    fireEvent.change(input, { target: { files: [file] } });
    expect(screen.getByTestId("file-name")).toHaveTextContent("meeting-notes.txt");
  });

  it("shows multiple uploaded filenames", () => {
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

  it("removes a file when the remove button is clicked", () => {
    render(<UploadArea />);
    const input = screen.getByTestId("file-input");
    const file = new File(["x"], "removable.txt", { type: "text/plain" });
    fireEvent.change(input, { target: { files: [file] } });
    const removeBtn = screen.getByRole("button", { name: /remove removable\.txt/i });
    fireEvent.click(removeBtn);
    expect(screen.queryByTestId("file-name")).not.toBeInTheDocument();
  });
});
