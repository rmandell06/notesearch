import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import SearchBar from "../components/SearchBar";

describe("SearchBar", () => {
  it("renders the search input", () => {
    render(<SearchBar onSearch={() => {}} />);
    expect(screen.getByRole("searchbox", { name: /search notes/i })).toBeInTheDocument();
  });

  it("accepts text input", async () => {
    render(<SearchBar onSearch={() => {}} />);
    const input = screen.getByRole("searchbox", { name: /search notes/i });
    await userEvent.type(input, "vector embeddings");
    expect(input).toHaveValue("vector embeddings");
  });

  it("calls onSearch with the typed query on submit", async () => {
    const onSearch = jest.fn();
    render(<SearchBar onSearch={onSearch} />);
    const input = screen.getByRole("searchbox", { name: /search notes/i });
    await userEvent.type(input, "semantic search");
    fireEvent.submit(input.closest("form"));
    expect(onSearch).toHaveBeenCalledWith("semantic search");
  });

  it("renders with an initial value", () => {
    render(<SearchBar onSearch={() => {}} initialValue="prior query" />);
    expect(screen.getByDisplayValue("prior query")).toBeInTheDocument();
  });

  it("clears the input when the clear button is clicked", async () => {
    render(<SearchBar onSearch={() => {}} />);
    const input = screen.getByRole("searchbox", { name: /search notes/i });
    await userEvent.type(input, "some text");
    const clearBtn = screen.getByRole("button", { name: /clear search/i });
    await userEvent.click(clearBtn);
    expect(input).toHaveValue("");
  });
});
