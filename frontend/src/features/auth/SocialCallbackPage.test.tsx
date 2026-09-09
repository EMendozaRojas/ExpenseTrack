import { render, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { SocialCallbackPage } from "./SocialCallbackPage";

const loginWithTokens = vi.fn();
const navigate = vi.fn();

vi.mock("./useAuth", () => ({
  useAuth: () => ({ loginWithTokens }),
}));

vi.mock("react-router", async () => {
  const actual = await vi.importActual<typeof import("react-router")>("react-router");
  return { ...actual, useNavigate: () => navigate };
});

describe("SocialCallbackPage", () => {
  beforeEach(() => {
    loginWithTokens.mockReset();
    navigate.mockReset();
  });

  it("guarda los tokens de la URL y navega a la página principal", async () => {
    window.history.pushState(
      {},
      "",
      "/auth/social-callback?access_token=abc&refresh_token=xyz",
    );

    render(
      <MemoryRouter>
        <SocialCallbackPage />
      </MemoryRouter>,
    );

    await waitFor(() => expect(loginWithTokens).toHaveBeenCalledWith("abc", "xyz"));
    expect(navigate).toHaveBeenCalledWith("/", { replace: true });
  });

  it("muestra un error si falta el access_token", async () => {
    window.history.pushState({}, "", "/auth/social-callback");

    const { findByText } = render(
      <MemoryRouter>
        <SocialCallbackPage />
      </MemoryRouter>,
    );

    await findByText(/No se recibió un token/);
    expect(loginWithTokens).not.toHaveBeenCalled();
  });
});
