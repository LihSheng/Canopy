import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { EmployeeContributionTable } from "@/components/dashboard/employee-contribution-table";
import { ClaimDetailTable } from "@/components/dashboard/claim-detail-table";

describe("EmployeeContributionTable", () => {
  const employees = [
    { id: "1", name: "Alice", department: "Engineering", payroll: 80000, claims: 5000, total: 85000 },
    { id: "2", name: "Bob", department: "Engineering", payroll: 90000, claims: 2000, total: 92000 },
  ];

  it("renders employee rows", () => {
    render(<EmployeeContributionTable data={employees} />);
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("Bob")).toBeInTheDocument();
    expect(screen.getByText("$80,000")).toBeInTheDocument();
  });

  it("shows empty message when no data", () => {
    render(<EmployeeContributionTable data={[]} />);
    expect(screen.getByText("No employee data available")).toBeInTheDocument();
  });

  it("renders skeleton when loading", () => {
    const { container } = render(<EmployeeContributionTable data={[]} loading />);
    expect(container.querySelector(".animate-pulse")).toBeTruthy();
  });
});

describe("ClaimDetailTable", () => {
  const claims = [
    { id: "1", employee_name: "Alice", department: "Engineering", type: "Travel", amount: 1500, date: "2024-01-15" },
    { id: "2", employee_name: "Bob", department: "Sales", type: "Meals", amount: 200, date: "2024-01-20" },
  ];

  it("renders claim rows", () => {
    render(<ClaimDetailTable data={claims} />);
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("Travel")).toBeInTheDocument();
    expect(screen.getByText("$1,500")).toBeInTheDocument();
  });

  it("shows empty message when no claims", () => {
    render(<ClaimDetailTable data={[]} />);
    expect(screen.getByText("No claims found")).toBeInTheDocument();
  });

  it("renders skeleton when loading", () => {
    const { container } = render(<ClaimDetailTable data={[]} loading />);
    expect(container.querySelector(".animate-pulse")).toBeTruthy();
  });
});
