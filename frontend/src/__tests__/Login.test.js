import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import Login from "../pages/Login";
import { AuthProvider } from "../AuthContext";
import * as api from "../api";

jest.mock("../api");

function renderLogin() {
  const router = createMemoryRouter(
    [
      { path: "/login", element: <Login /> },
      { path: "/", element: <div>Home Page</div> },
      { path: "/signup", element: <div>Signup Page</div> },
    ],
    { initialEntries: ["/login"] }
  );
  return render(
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  );
}

afterEach(() => jest.resetAllMocks());

describe("Login", () => {
  it("renders email and password fields", () => {
    api.loginUser.mockReturnValue(new Promise(() => {}));
    renderLogin();
    expect(screen.getByPlaceholderText("you@example.com")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("••••••••")).toBeInTheDocument();
  });

  it("calls loginUser with entered email and password on submit", async () => {
    api.loginUser.mockResolvedValue({ access_token: "tok", user: { email: "a@b.com" } });
    renderLogin();
    await userEvent.type(screen.getByPlaceholderText("you@example.com"), "a@b.com");
    await userEvent.type(screen.getByPlaceholderText("••••••••"), "secret123");
    fireEvent.submit(screen.getByPlaceholderText("you@example.com").closest("form"));
    await waitFor(() => expect(api.loginUser).toHaveBeenCalledWith("a@b.com", "secret123"));
  });

  it("shows loading state while request is in flight", async () => {
    api.loginUser.mockReturnValue(new Promise(() => {}));
    renderLogin();
    await userEvent.type(screen.getByPlaceholderText("you@example.com"), "a@b.com");
    await userEvent.type(screen.getByPlaceholderText("••••••••"), "pass");
    fireEvent.submit(screen.getByPlaceholderText("you@example.com").closest("form"));
    await waitFor(() => expect(screen.getByText("logging in...")).toBeInTheDocument());
  });

  it("shows error message when login fails", async () => {
    api.loginUser.mockRejectedValue(new Error("Invalid credentials"));
    renderLogin();
    await userEvent.type(screen.getByPlaceholderText("you@example.com"), "a@b.com");
    await userEvent.type(screen.getByPlaceholderText("••••••••"), "wrong");
    fireEvent.submit(screen.getByPlaceholderText("you@example.com").closest("form"));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Invalid credentials"));
  });

  it("navigates to home on successful login", async () => {
    api.loginUser.mockResolvedValue({ access_token: "tok", user: { email: "a@b.com" } });
    renderLogin();
    await userEvent.type(screen.getByPlaceholderText("you@example.com"), "a@b.com");
    await userEvent.type(screen.getByPlaceholderText("••••••••"), "pass");
    fireEvent.submit(screen.getByPlaceholderText("you@example.com").closest("form"));
    await waitFor(() => expect(screen.getByText("Home Page")).toBeInTheDocument());
  });

  it("has a link to the signup page", () => {
    api.loginUser.mockReturnValue(new Promise(() => {}));
    renderLogin();
    expect(screen.getByText("sign up")).toBeInTheDocument();
  });
});
