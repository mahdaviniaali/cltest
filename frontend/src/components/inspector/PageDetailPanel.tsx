import type { SitePageDetail, SiteSection } from "../../api/inspector";

interface Props {
  page: SitePageDetail | null;
  sections: SiteSection[];
  selectedSection: string | null;
  onSectionSelect: (section: string | null) => void;
}

export default function PageDetailPanel({
  page,
  sections,
  selectedSection,
  onSectionSelect,
}: Props) {
  return (
    <div className="inspector-detail">
      <div className="sections-list">
        <h3>بخش‌های سایت</h3>
        <button
          type="button"
          className={`section-chip ${selectedSection === null ? "active" : ""}`}
          onClick={() => onSectionSelect(null)}
        >
          همه
        </button>
        {sections.map((s) => (
          <button
            key={s.section_key}
            type="button"
            className={`section-chip ${selectedSection === s.section_key ? "active" : ""}`}
            onClick={() => onSectionSelect(s.section_key)}
          >
            {s.label} ({s.page_count})
          </button>
        ))}
      </div>
      {page ? (
        <div className="page-detail">
          <h3>{page.title || page.url}</h3>
          <p className="muted">{page.url}</p>
          <dl className="detail-grid">
            <dt>نوع</dt>
            <dd>{page.page_type}</dd>
            <dt>بخش</dt>
            <dd>{page.section || "—"}</dd>
            <dt>الگو</dt>
            <dd>{page.url_pattern}</dd>
            <dt>عمق</dt>
            <dd>{page.depth}</dd>
            <dt>وضعیت</dt>
            <dd>{page.status}</dd>
          </dl>
          {page.excerpt && <p>{page.excerpt}</p>}
          {page.outbound_links.length > 0 && (
            <>
              <h4>لینک‌های خروجی ({page.outbound_links.length})</h4>
              <ul className="link-list">
                {page.outbound_links.slice(0, 20).map((link) => (
                  <li key={link.page_key}>
                    <span className="tree-type">{link.relation_type}</span> {link.url || link.page_key}
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      ) : (
        <p className="muted">یک صفحه از درخت یا گراف انتخاب کنید.</p>
      )}
    </div>
  );
}
