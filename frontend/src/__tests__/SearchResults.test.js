import { render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import SearchResults from "../pages/SearchResults";
import * as api from "../api";

jest.mock("../api");

function renderResults(query = "embeddings") {
  const router = createMemoryRouter(
    [{ path: "/search", element: <SearchResults /> }],
    { initialEntries: [`/search?q=${encodeURIComponent(query)}`] }
  );
  return render(<RouterProvider router={router} />);
}

afterEach(() => jest.resetAllMocks());

describe("SearchResults", () => {
  it("shows loading state while fetching", () => {
    api.searchNotes.mockReturnValue(new Promise(() => {}));
    renderResults();
    expect(screen.getByRole("status", { name: /loading/i })).toBeInTheDocument();
  });

  it("renders note cards when API returns results", async () => {
    api.searchNotes.mockResolvedValue({
      results: [
        { id: "1", title: "Vector search notes", preview: "cosine similarity...", date: "Mar 1, 2026", relevance: 0.92 },
        { id: "2", title: "Attention mechanism", preview: "transformer model...", date: "Mar 2, 2026", relevance: 0.85 },
      ],
    });
    renderResults("embeddings");
    await waitFor(() => expect(screen.getByText("Vector search notes")).toBeInTheDocument());
    expect(screen.getByText("Attention mechanism")).toBeInTheDocument();
    expect(screen.getByText(/2 results/i)).toBeInTheDocument();
  });

  it("shows error message when API call fails", async () => {
    api.searchNotes.mockRejectedValue(new Error("connection refused"));
    renderResults("embeddings");
    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    expect(screen.getByRole("alert")).toHaveTextContent("connection refused");
  });

  it("shows empty state when search returns no results", async () => {
    api.searchNotes.mockResolvedValue({ results: [] });
    renderResults("xyzzy");
    await waitFor(() => expect(screen.getByText(/no results/i)).toBeInTheDocument());
    expect(screen.getByText(/"xyzzy"/i)).toBeInTheDocument();
  });

  it("calls searchNotes with the query from the URL", async () => {
    api.searchNotes.mockResolvedValue({ results: [] });
    renderResults("attention is all you need");
    await waitFor(() => expect(api.searchNotes).toHaveBeenCalledWith("attention is all you need"));
  });

  it("displays the query in the results count", async () => {
    api.searchNotes.mockResolvedValue({
      results: [{ id: "1", title: "Test", preview: "...", date: "Mar 1, 2026", relevance: 0.8 }],
    });
    renderResults("transformers");
    await waitFor(() => expect(screen.getByText(/"transformers"/)).toBeInTheDocument());
  });
});
