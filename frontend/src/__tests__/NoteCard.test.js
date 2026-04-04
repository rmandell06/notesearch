import { render, screen, fireEvent } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import NoteCard from "../components/NoteCard";

const note = {
  id: "42",
  title: "Test note title",
  preview: "This is a short preview of the note content.",
  date: "Mar 30, 2026",
};

function renderCard(props = {}, { initialPath = "/" } = {}) {
  const router = createMemoryRouter(
    [
      { path: "/", element: <NoteCard note={note} {...props} /> },
      { path: "/note/:id", element: <div>Note Viewer Page</div> },
    ],
    { initialEntries: [initialPath] }
  );
  return render(<RouterProvider router={router} />);
}

describe("NoteCard", () => {
  it("displays the note title", () => {
    renderCard();
    expect(screen.getByText("Test note title")).toBeInTheDocument();
  });

  it("displays the preview snippet", () => {
    renderCard();
    expect(screen.getByText("This is a short preview of the note content.")).toBeInTheDocument();
  });

  it("displays the date", () => {
    renderCard();
    expect(screen.getByText("Mar 30, 2026")).toBeInTheDocument();
  });

  it("navigates to the note viewer page on click", () => {
    renderCard();
    fireEvent.click(screen.getByRole("article"));
    expect(screen.getByText("Note Viewer Page")).toBeInTheDocument();
  });

  it("shows relevance badge when showRelevance is true and relevance is set", () => {
    renderCard({ note: { ...note, relevance: 0.87 }, showRelevance: true });
    expect(screen.getByText("87% match")).toBeInTheDocument();
  });

  it("does not show relevance badge by default", () => {
    renderCard({ note: { ...note, relevance: 0.87 } });
    expect(screen.queryByText("87% match")).not.toBeInTheDocument();
  });
});
