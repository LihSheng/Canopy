import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ToastProvider, useToast } from "@/components/shared/toast";

const ToastTrigger = () => {
  const toast = useToast();

  return (
    <button type="button" onClick={() => toast.success("Saved", "Toast works")}>
      Trigger Toast
    </button>
  );
}

describe("Toast", () => {
  it("renders a shared success toast", async () => {
    render(
      <ToastProvider>
        <ToastTrigger />
      </ToastProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Trigger Toast" }));

    await waitFor(() => {
      expect(screen.getByRole("status")).toBeInTheDocument();
      expect(screen.getByText("Saved")).toBeInTheDocument();
      expect(screen.getByText("Toast works")).toBeInTheDocument();
    });
  });
});
