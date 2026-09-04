import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { MonthNavigator } from "./MonthNavigator";

describe("MonthNavigator", () => {
  it("avanza al mes siguiente", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();

    render(<MonthNavigator year={2026} month={8} onChange={onChange} />);
    await user.click(screen.getByRole("button", { name: "Mes siguiente" }));

    expect(onChange).toHaveBeenCalledWith(2026, 9);
  });

  it("retrocede al mes anterior", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();

    render(<MonthNavigator year={2026} month={8} onChange={onChange} />);
    await user.click(screen.getByRole("button", { name: "Mes anterior" }));

    expect(onChange).toHaveBeenCalledWith(2026, 7);
  });

  it("pasa al año siguiente cuando avanza desde diciembre", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();

    render(<MonthNavigator year={2026} month={12} onChange={onChange} />);
    await user.click(screen.getByRole("button", { name: "Mes siguiente" }));

    expect(onChange).toHaveBeenCalledWith(2027, 1);
  });

  it("pasa al año anterior cuando retrocede desde enero", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();

    render(<MonthNavigator year={2026} month={1} onChange={onChange} />);
    await user.click(screen.getByRole("button", { name: "Mes anterior" }));

    expect(onChange).toHaveBeenCalledWith(2025, 12);
  });
});
