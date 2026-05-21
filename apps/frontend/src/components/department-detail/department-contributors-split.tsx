import type { ContributorItem } from "./department-detail-mappers";
import { DepartmentContributorPanel, DepartmentContributorPanelSkeleton } from "./department-contributor-panel";

type Props = {
  topEmployees: ContributorItem[];
  topClaimTypes: ContributorItem[];
};

export const DepartmentContributorsSplit = ({ topEmployees, topClaimTypes }: Props) => {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <DepartmentContributorPanel title="Top Employees" items={topEmployees} />
      <DepartmentContributorPanel title="Top Claim Types" items={topClaimTypes} />
    </div>
  );
}

export const DepartmentContributorsSplitSkeleton = () => {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <DepartmentContributorPanelSkeleton />
      <DepartmentContributorPanelSkeleton />
    </div>
  );
}
