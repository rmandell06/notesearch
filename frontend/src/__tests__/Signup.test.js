import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import Signup from "../pages/Signup";
import { AuthProvider } from "../AuthContext";
import * as api from "../api";

jest.mock("../api");

function renderSignup() {
  const router = createMemoryRouter(
    [
      { path: "/signup", element: <Signup /> },
      { path: "/", element: <div>Home Page</div> },
      { path: "/login", element: <div>Login Page</div> },
    ],
    { initialEntries: ["/signup"] }
  );
  return render(
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  );
}

afterEach(() => jest.resetAllMocks());

describe("Signup", () => {
  it("renders email and password fields", () => {
    renderSignup();
    expect(screen.getByPlaceholderText("you@example.com")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("••••••••")).toBeInTheDocument();
  });

  it("calls signupUser with entered email and password on submit", async () => {
    api.signupUser.mockResolvedValue({ access_token: "tok", user: { email: "new@user.com" } });
    renderSignup();
    await userEvent.type(screen.getByPlaceholderText("you@example.com"), "new@user.com");
    await userEvent.type(screen.getByPlaceholderText("••••••••"), "mypassword");
    fireEvent.submit(screen.getByPlaceholderText("you@example.com").closest("form"));
    await waitFor(() => expect(api.signupUser).toHaveBeenCalledWith("new@user.com", "mypassword"));
  });

  it("shows error when signup fails", async () => {
    api.signupUser.mockRejectedValue(new Error("Email already taken"));
    renderSignup();
    await userEvent.type(screen.getByPlaceholderText("you@example.com"), "taken@email.com");
    await userEvent.type(screen.getByPlaceholderText("••••••••"), "pass");
    fireEvent.submit(screen.getByPlaceholderText("you@example.com").closest("form"));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Email already taken"));
  });

  it("navigates to home on successful signup", async () => {
    api.signupUser.mockResolvedValue({ access_token: "tok", user: { email: "new@user.com" } });
    renderSignup();
    await userEvent.type(screen.getByPlaceholderText("you@example.com"), "new@user.com");
    await userEvent.type(screen.getByPlaceholderText("••••••••"), "pass");
    fireEvent.submit(screen.getByPlaceholderText("you@example.com").closest("form"));
    await waitFor(() => expect(screen.getByText("Home Page")).toBeInTheDocument());
  });

  it("has a link back to the login page", () => {
    renderSignup();
    expect(screen.getByText("log in")).toBeInTheDocument();
  });
});
