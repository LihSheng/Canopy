import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { WorkflowStepper, buildWorkflowSteps } from "@/components/ingestion-v2/workflow-stepper";

describe("WorkflowStepper", () => {
  it("shows all five steps", () => {
    const steps = buildWorkflowSteps("started");
    render(<WorkflowStepper steps={steps} />);

    expect(screen.getByText("Upload")).toBeInTheDocument();
    expect(screen.getByText("Profile")).toBeInTheDocument();
    expect(screen.getByText("Map")).toBeInTheDocument();
    expect(screen.getByText("Process")).toBeInTheDocument();
    expect(screen.getByText("Publish")).toBeInTheDocument();
  });

  it("marks first step as current when status is started", () => {
    const steps = buildWorkflowSteps("started");
    render(<WorkflowStepper steps={steps} />);

    const uploadBtn = screen.getByLabelText("Upload - current");
    expect(uploadBtn).toBeInTheDocument();
    expect(screen.getByLabelText("Profile - pending")).toBeInTheDocument();
    expect(screen.getByLabelText("Map - pending")).toBeInTheDocument();
    expect(screen.getByLabelText("Process - pending")).toBeInTheDocument();
    expect(screen.getByLabelText("Publish - pending")).toBeInTheDocument();
  });

  it("marks completed steps correctly for published status", () => {
    const steps = buildWorkflowSteps("published");
    render(<WorkflowStepper steps={steps} />);

    expect(screen.getByLabelText("Upload - completed")).toBeInTheDocument();
    expect(screen.getByLabelText("Profile - completed")).toBeInTheDocument();
    expect(screen.getByLabelText("Map - completed")).toBeInTheDocument();
    expect(screen.getByLabelText("Process - completed")).toBeInTheDocument();
    expect(screen.getByLabelText("Publish - completed")).toBeInTheDocument();
  });

  it("marks intermediate steps correctly for profiled status", () => {
    const steps = buildWorkflowSteps("profiled");
    render(<WorkflowStepper steps={steps} />);

    expect(screen.getByLabelText("Upload - completed")).toBeInTheDocument();
    expect(screen.getByLabelText("Profile - current")).toBeInTheDocument();
    expect(screen.getByLabelText("Map - pending")).toBeInTheDocument();
    expect(screen.getByLabelText("Process - pending")).toBeInTheDocument();
    expect(screen.getByLabelText("Publish - pending")).toBeInTheDocument();
  });

  it("marks all pending when status is failed", () => {
    const steps = buildWorkflowSteps("failed");
    render(<WorkflowStepper steps={steps} />);

    expect(screen.getByLabelText("Upload - pending")).toBeInTheDocument();
    expect(screen.getByLabelText("Profile - pending")).toBeInTheDocument();
    expect(screen.getByLabelText("Map - pending")).toBeInTheDocument();
    expect(screen.getByLabelText("Process - pending")).toBeInTheDocument();
    expect(screen.getByLabelText("Publish - pending")).toBeInTheDocument();
  });

  it("handles null status gracefully", () => {
    const steps = buildWorkflowSteps(null);
    render(<WorkflowStepper steps={steps} />);

    expect(screen.getByLabelText("Upload - pending")).toBeInTheDocument();
    expect(screen.getByLabelText("Profile - pending")).toBeInTheDocument();
  });

  it("calls onNavigate when clicking a completed step", () => {
    const onNavigate = vi.fn();
    const steps = buildWorkflowSteps("published", onNavigate);
    render(<WorkflowStepper steps={steps} />);

    const completedBtn = screen.getByLabelText("Upload - completed");
    fireEvent.click(completedBtn);
    expect(onNavigate).toHaveBeenCalledWith("upload");
  });

  it("does not trigger click on current step", () => {
    const onNavigate = vi.fn();
    const steps = buildWorkflowSteps("started", onNavigate);
    render(<WorkflowStepper steps={steps} />);

    const currentBtn = screen.getByLabelText("Upload - current");
    fireEvent.click(currentBtn);
    expect(onNavigate).not.toHaveBeenCalled();
  });

  it("does not trigger click on pending step", () => {
    const onNavigate = vi.fn();
    const steps = buildWorkflowSteps("started", onNavigate);
    render(<WorkflowStepper steps={steps} />);

    const pendingBtn = screen.getByLabelText("Publish - pending");
    fireEvent.click(pendingBtn);
    expect(onNavigate).not.toHaveBeenCalled();
  });

  it("marks processed status correctly", () => {
    const steps = buildWorkflowSteps("processed");
    render(<WorkflowStepper steps={steps} />);

    expect(screen.getByLabelText("Upload - completed")).toBeInTheDocument();
    expect(screen.getByLabelText("Profile - completed")).toBeInTheDocument();
    expect(screen.getByLabelText("Map - completed")).toBeInTheDocument();
    expect(screen.getByLabelText("Process - completed")).toBeInTheDocument();
    expect(screen.getByLabelText("Publish - current")).toBeInTheDocument();
  });
});
