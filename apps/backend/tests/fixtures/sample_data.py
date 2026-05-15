from pydantic import BaseModel


class SourceDepartmentRow(BaseModel):
    source_key: str
    name: str
    parent_key: str | None = None
    status: str = "active"


class SourceEmployeeRow(BaseModel):
    source_key: str
    full_name: str
    department_key: str
    cost_center_key: str | None = None


SAMPLE_DEPARTMENTS = [
    SourceDepartmentRow(source_key="D001", name="Engineering"),
    SourceDepartmentRow(source_key="D002", name="Marketing"),
    SourceDepartmentRow(source_key="D003", name="Sales"),
]

SAMPLE_EMPLOYEES = [
    SourceEmployeeRow(source_key="E001", full_name="Alice Tan", department_key="D001"),
    SourceEmployeeRow(source_key="E002", full_name="Bob Lim", department_key="D002"),
]
