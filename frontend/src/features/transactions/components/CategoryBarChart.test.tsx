import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CategoryBarChart } from "./CategoryBarChart";

describe("CategoryBarChart", () => {
  it("muestra un mensaje cuando no hay datos", () => {
    render(<CategoryBarChart data={[]} />);

    expect(screen.getByText("Sin gastos clasificados este mes.")).toBeInTheDocument();
  });

  it("ordena las categorías de mayor a menor gasto", () => {
    render(
      <CategoryBarChart
        data={[
          { category_id: 1, category_name: "Ocio", total: "10.00" },
          { category_id: 2, category_name: "Comida", total: "50.00" },
        ]}
      />,
    );

    const labels = screen.getAllByText(/Ocio|Comida/).map((el) => el.textContent);
    expect(labels).toEqual(["Comida", "Ocio"]);
  });
});
