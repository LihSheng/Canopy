import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TotalPayrollCard } from "@/components/dashboard/total-payroll-card";
import { TotalClaimsCard } from "@/components/dashboard/total-claims-card";
import { TopDepartmentsCard } from "@/components/dashboard/top-departments-card";
import { AnomalyHighlightsCard } from "@/components/dashboard/anomaly-highlights-card";

describe("TotalPayrollCard", () => {
  it("renders formatted currency value", () => {
    render(<TotalPayrollCard value={1500000} />);
    expect(screen.getByText("$1,500,000")).toBeInTheDocument();
  });

  it("shows positive change percentage", () => {
    render(<TotalPayrollCard value={100000} changePct={5.2} />);
    expect(screen.getByText("+5.2% vs last month")).toBeInTheDocument();
  });

  it("shows negative change percentage", () => {
    render(<TotalPayrollCard value={100000} changePct={-3.1} />);
    expect(screen.getByText("-3.1% vs last month")).toBeInTheDocument();
  });

  it("renders skeleton when loading", () => {
    const { container } = render(<TotalPayrollCard value={0} loading />);
    expect(container.querySelector(".animate-pulse")).toBeTruthy();
  });
});

describe("TotalClaimsCard", () => {
  it("renders formatted currency value", () => {
    render(<TotalClaimsCard value={250000} />);
    expect(screen.getByText("$250,000")).toBeInTheDocument();
  });

  it("shows change when loading is false", () => {
    render(<TotalClaimsCard value={100000} changePct={10} />);
    expect(screen.getByText("+10.0% vs last month")).toBeInTheDocument();
  });

  it("renders skeleton when loading", () => {
    const { container } = render(<TotalClaimsCard value={0} loading />);
    expect(container.querySelector(".animate-pulse")).toBeTruthy();
  });
});

describe("TopDepartmentsCard", () => {
  it("renders department names and amounts", () => {
    render(
      <TopDepartmentsCard
        departments={[
          { id: "1", name: "Engineering", total_spend: 500000, payroll_spend: 400000, claims_spend: 100000, change_pct: 2.5 },
          { id: "2", name: "Sales", total_spend: 300000, payroll_spend: 200000, claims_spend: 100000, change_pct: -1.2 },
        ]}
      />,
    );
    expect(screen.getByText("Engineering")).toBeInTheDocument();
    expect(screen.getByText("Sales")).toBeInTheDocument();
    expect(screen.getByText("$500,000")).toBeInTheDocument();
  });

  it("shows empty message when no departments", () => {
    render(<TopDepartmentsCard departments={[]} />);
    expect(screen.getByText("No data")).toBeInTheDocument();
  });

  it("renders skeleton when loading", () => {
    const { container } = render(<TopDepartmentsCard departments={[]} loading />);
    expect(container.querySelector(".animate-pulse")).toBeTruthy();
  });
});

describe("AnomalyHighlightsCard", () => {
  it("renders anomaly descriptions", () => {
    render(
      <AnomalyHighlightsCard
        anomalies={[
          {
            id: "1",
            department_id: "d1",
            department_name: "Engineering",
            period: "2024-01",
            description: "Unusual payroll increase",
            severity: "high",
            change_pct: 15,
          },
        ]}
      />,
    );
    expect(screen.getByText("Engineering")).toBeInTheDocument();
    expect(screen.getByText("Unusual payroll increase")).toBeInTheDocument();
  });

  it("shows empty message when no anomalies", () => {
    render(<AnomalyHighlightsCard anomalies={[]} />);
    expect(screen.getByText("No anomalies detected")).toBeInTheDocument();
  });

  it("renders skeleton when loading", () => {
    const { container } = render(<AnomalyHighlightsCard anomalies={[]} loading />);
    expect(container.querySelector(".animate-pulse")).toBeTruthy();
  });
});
