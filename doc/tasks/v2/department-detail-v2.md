# Department Detail V2 Module Tasks

## Goal

Deliver the full-page department investigation flow with summary header, trend
hero panel, smaller AI summary, contributor split view, and related-anomalies
CTA.

## Tasks

- [ ] Create department detail page as a nested page inside the shared shell.
- [ ] Add breadcrumb rendering for the nested detail route only.
- [ ] Add visible time-range control in the detail header.
- [ ] Create summary header with department name, attention state, total spend, and change %.
- [ ] Create dominant trend and change panel.
- [ ] Create smaller department-level AI summary using sentence plus bullets structure.
- [ ] Create equal side-by-side contributor panels for top employees and top claim types.
- [ ] Add `View related anomalies` CTA.
- [ ] Route CTA to `Anomalies` with department and current time range pre-applied.
- [ ] Keep page as single long-scroll flow with no tabs and no detailed transaction table.

## Testing

- [ ] Add unit tests for department detail mapper.
- [ ] Add unit tests for contributor split rendering.
- [ ] Add integration test for time-range change refetching the whole page consistently.
- [ ] Add integration test for `View related anomalies` CTA carry-over behavior.
