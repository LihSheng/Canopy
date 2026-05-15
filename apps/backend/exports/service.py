from api.schemas.exports import ExportRequest, ExportResponse


def request_export(request: ExportRequest) -> ExportResponse:
    return ExportResponse(
        accepted=True,
        download_url=None,
        status="queued",
    )
