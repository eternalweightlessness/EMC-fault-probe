from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from emc_core.domain.fault_case import FaultCase
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font


class ExcelCaseExporter:
    """把结构化故障案例导出为可直接交付的 xlsx 文件。"""

    def export(self, cases: Sequence[FaultCase], destination: Path) -> Path:
        if destination.suffix.lower() != ".xlsx":
            destination = destination.with_suffix(".xlsx")
        destination = destination.expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "EMC 故障案例"
        headers = list(FaultCase.FIELD_MAP)
        sheet.append(headers)
        for cell in sheet[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")

        for case in cases:
            mapping = case.to_mapping()
            sheet.append([mapping[header] for header in headers])
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions

        for column in sheet.columns:
            longest = max(len(str(cell.value or "")) for cell in column)
            sheet.column_dimensions[column[0].column_letter].width = min(longest + 2, 60)
            for cell in column:
                cell.alignment = Alignment(vertical="top", wrap_text=True)

        workbook.save(destination)
        return destination
