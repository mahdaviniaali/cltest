from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.site_map import SiteMapGroup


class SiteMapGroupRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert(
        self,
        *,
        group_key: str,
        parent_group_key: str | None,
        group_kind: str,
        label: str,
        section: str | None,
        path_prefix: str | None,
        url_pattern: str | None,
        page_type: str | None,
        page_count: int,
        weight: int,
        inbound_link_count: int = 0,
        representative_page_key: str | None,
        representative_url: str | None,
        depth: int,
        sort_order: int,
    ) -> SiteMapGroup:
        now = datetime.now(timezone.utc)
        row = self._session.get(SiteMapGroup, group_key)
        if row is None:
            row = SiteMapGroup(
                group_key=group_key,
                parent_group_key=parent_group_key,
                group_kind=group_kind,
                label=label,
                section=section,
                path_prefix=path_prefix,
                url_pattern=url_pattern,
                page_type=page_type,
                page_count=page_count,
                weight=weight,
                inbound_link_count=inbound_link_count,
                representative_page_key=representative_page_key,
                representative_url=representative_url,
                depth=depth,
                sort_order=sort_order,
                updated_at=now,
            )
            self._session.add(row)
        else:
            row.parent_group_key = parent_group_key
            row.group_kind = group_kind
            row.label = label
            row.section = section
            row.path_prefix = path_prefix
            row.url_pattern = url_pattern
            row.page_type = page_type
            row.page_count = page_count
            row.weight = weight
            row.inbound_link_count = inbound_link_count
            row.representative_page_key = representative_page_key
            row.representative_url = representative_url
            row.depth = depth
            row.sort_order = sort_order
            row.updated_at = now
        self._session.flush()
        return row

    def list_all(self, *, section: str | None = None) -> list[SiteMapGroup]:
        query = self._session.query(SiteMapGroup)
        if section is not None:
            query = query.filter(SiteMapGroup.section == section)
        return list(
            query.order_by(SiteMapGroup.depth.asc(), SiteMapGroup.sort_order.asc()).all()
        )

    def clear_all(self) -> None:
        self._session.query(SiteMapGroup).delete()
        self._session.flush()
