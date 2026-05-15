from dataclasses import asdict

from ontology.domain import MappingContext, UnresolvedRecord


class AttributionResolver:
    def resolve_department(
        self,
        context: MappingContext,
        direct_department_key: str | None,
        employee_source_key: str | None,
        cost_center_source_key: str | None,
    ) -> str | None:
        if direct_department_key and direct_department_key in context.departments:
            return context.departments[direct_department_key].id

        if employee_source_key and employee_source_key in context.employees:
            emp = context.employees[employee_source_key]
            if emp.department_id:
                return emp.department_id

        if cost_center_source_key and cost_center_source_key in context.cost_centers:
            cc = context.cost_centers[cost_center_source_key]
            if cc.code:  # mapped cost center exists
                return None

        return None

    def resolve_cost_center(
        self,
        context: MappingContext,
        employee_source_key: str | None,
    ) -> str | None:
        if employee_source_key and employee_source_key in context.employees:
            emp = context.employees[employee_source_key]
            return emp.cost_center_id
        return None
