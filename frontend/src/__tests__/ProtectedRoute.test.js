import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import ProtectedRoute from "../components/ProtectedRoute";
import * as AuthContext from "../AuthContext";

jest.mock("../AuthContext");

function renderProtected(token) {
  AuthContext.useAuth.mockReturnValue({ token, user: null, login: jest.fn(), logout: jest.fn() });

  const router = createMemoryRouter(
    [
      {
        path: "/",
        element: (
          <ProtectedRoute>
            <div>Protected Content</div>
          </ProtectedRoute>
        ),
      },
      { path: "/login", element: <div>Login Page</div> },
    ],
    { initialEntries: ["/"] }
  );
  return render(<RouterProvider router={router} />);
}

afterEach(() => jest.resetAllMocks());

describe("ProtectedRoute", () => {
  it("redirects to /login when no user is logged in", () => {
    renderProtected(null);
    expect(screen.getByText("Login Page")).toBeInTheDocument();
  });

  it("renders children when user is logged in", () => {
    renderProtected("valid-token");
    expect(screen.getByText("Protected Content")).toBeInTheDocument();
  });
});
