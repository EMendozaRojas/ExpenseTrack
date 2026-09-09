import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { Attachment } from "./types";
import * as attachmentsApi from "./api";
import { AttachmentsPanel } from "./AttachmentsPanel";

vi.mock("./api");
vi.mock("../auth/useAuth", () => ({
  useAuth: () => ({ token: "test-token", user: { id: 1, email: "demo@example.com" } }),
}));

const attachments: Attachment[] = [
  {
    id: 1,
    transaction_id: 7,
    filename: "recibo.png",
    mime_type: "image/png",
    size_bytes: 2048,
    created_at: "2026-03-01T00:00:00Z",
  },
];

function renderPanel() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <AttachmentsPanel transactionId={7} />
    </QueryClientProvider>,
  );
}

describe("AttachmentsPanel", () => {
  beforeEach(() => {
    vi.mocked(attachmentsApi.listAttachments).mockResolvedValue(attachments);
    vi.mocked(attachmentsApi.uploadAttachment).mockReset();
    vi.mocked(attachmentsApi.deleteAttachment).mockReset();
  });

  it("muestra los adjuntos existentes", async () => {
    renderPanel();

    expect(await screen.findByText("recibo.png")).toBeInTheDocument();
    expect(screen.getByText("2 KB")).toBeInTheDocument();
  });

  it("muestra un mensaje cuando no hay adjuntos", async () => {
    vi.mocked(attachmentsApi.listAttachments).mockResolvedValue([]);
    renderPanel();

    expect(await screen.findByText("Sin recibos adjuntos.")).toBeInTheDocument();
  });

  it("borra un adjunto", async () => {
    const user = userEvent.setup();
    vi.mocked(attachmentsApi.deleteAttachment).mockResolvedValue(undefined);

    renderPanel();
    await screen.findByText("recibo.png");

    await user.click(screen.getByRole("button", { name: "Borrar" }));

    expect(attachmentsApi.deleteAttachment).toHaveBeenCalledWith("test-token", 1);
  });
});
