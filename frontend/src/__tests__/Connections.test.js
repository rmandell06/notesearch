import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import Connections from "../pages/Connections";
import * as api from "../api";

jest.mock("../api");

const MOCK_GRAPH = {
  nodes: [
    { id: "1", title: "Vector embeddings", group: 1 },
    { id: "2", title: "Attention mechanism", group: 1 },
    { id: "3", title: "Q2 planning", group: 2 },
  ],
  links: [
    { source: "1", target: "2", value: 0.85 },
    { source: "2", target: "3", value: 0.42 },
  ],
};

function renderConnections() {
  const router = createMemoryRouter(
    [
      { path: "/connections", element: <Connections /> },
      { path: "/note/:id", element: <div>Note Viewer</div> },
    ],
    { initialEntries: ["/connections"] }
  );
  return render(<RouterProvider router={router} />);
}

afterEach(() => jest.resetAllMocks());

describe("Connections", () => {
  it("shows loading state while fetching", () => {
    api.getConnections.mockReturnValue(new Promise(() => {}));
    renderConnections();
    expect(screen.getByRole("status", { name: /loading/i })).toBeInTheDocument();
  });

  it("renders graph nodes when API returns data", async () => {
    api.getConnections.mockResolvedValue(MOCK_GRAPH);
    renderConnections();
    await waitFor(() => expect(screen.getAllByTestId("graph-node")).toHaveLength(3));
    expect(screen.getByLabelText("Vector embeddings")).toBeInTheDocument();
    expect(screen.getByLabelText("Attention mechanism")).toBeInTheDocument();
    expect(screen.getByLabelText("Q2 planning")).toBeInTheDocument();
  });

  it("renders edges between nodes", async () => {
    api.getConnections.mockResolvedValue(MOCK_GRAPH);
    renderConnections();
    await waitFor(() => expect(screen.getAllByTestId("graph-edge")).toHaveLength(2));
  });

  it("falls back to mock data when API fails", async () => {
    api.getConnections.mockRejectedValue(new Error("backend offline"));
    renderConnections();
    await waitFor(() => expect(screen.getByTestId("graph-container")).toBeInTheDocument());
    expect(screen.getAllByTestId("graph-node").length).toBeGreaterThan(0);
  });

  it("shows empty state when API returns no nodes", async () => {
    api.getConnections.mockResolvedValue({ nodes: [], links: [] });
    renderConnections();
    await waitFor(() => expect(screen.getByText(/no connections yet/i)).toBeInTheDocument());
  });

  it("navigates to note viewer when a node is clicked", async () => {
    api.getConnections.mockResolvedValue(MOCK_GRAPH);
    renderConnections();
    await waitFor(() => expect(screen.getAllByTestId("graph-node")).toHaveLength(3));
    fireEvent.click(screen.getByLabelText("Vector embeddings"));
    expect(screen.getByText("Note Viewer")).toBeInTheDocument();
  });

  it("shows the node and edge count in the legend", async () => {
    api.getConnections.mockResolvedValue(MOCK_GRAPH);
    renderConnections();
    await waitFor(() => expect(screen.getByText(/3 notes · 2 connections/i)).toBeInTheDocument());
  });
});
