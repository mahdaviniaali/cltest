import type { SitePageDetail, SiteSection } from "../../api/inspector";
import ExternalLink from "./ExternalLink";

interface Props {
  page: SitePageDetail | null;
  sections: SiteSection[];
  selectedSection: string | null;
  onSectionSelect: (section: string | null) => void;
}

function metaPreview(meta: Record<string, unknown>): string {
  try {
    const text = JSON.stringify(meta, null, 2);
    return text.length > 800 ? `${text.slice(0, 800)}…` : text;
  } catch {
    return String(meta);
  }
}

export default function PageDetailPanel({
  page,
  sections,
  selectedSection,
  onSectionSelect,
}: Props) {
  const activeSection = sections.find((s) => s.section_key === selectedSection);

  return (
    <div className="inspector-detail">
      <div className="sections-list">
        <h3>بخش‌های سایت ({sections.length})</h3>
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

      {activeSection && (
        <div className="section-detail panel-inner">
          <h4>{activeSection.label}</h4>
          <dl className="detail-grid">
            <dt>صفحات</dt>
            <dd>{activeSection.page_count.toLocaleString("fa-IR")}</dd>
            <dt>امتیاز</dt>
            <dd>{activeSection.useful_score.toFixed(1)}</dd>
            <dt>الگوها</dt>
            <dd className="mono">{activeSection.url_patterns.slice(0, 3).join(", ") || "—"}</dd>
          </dl>
          {activeSection.root_urls.length > 0 && (
            <>
              <h5>URLهای ریشه</h5>
              <ul className="link-list">
                {activeSection.root_urls.map((url) => (
                  <li key={url}>
                    <ExternalLink href={url}>{url}</ExternalLink>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}

      {page ? (
        <div className="page-detail">
          <div className="page-detail-header">
            <h3>{page.title || page.url}</h3>
            <ExternalLink href={page.url} className="link-button external-open-btn">
              مشاهده در bama.ir ↗
            </ExternalLink>
          </div>
          <p className="muted page-url-line">
            <ExternalLink href={page.url}>{page.url}</ExternalLink>
          </p>
          <dl className="detail-grid">
            <dt>نوع</dt>
            <dd>{page.page_type}</dd>
            <dt>بخش</dt>
            <dd>{page.section || "—"}</dd>
            <dt>الگو</dt>
            <dd className="mono">{page.url_pattern}</dd>
            <dt>عمق</dt>
            <dd>{page.depth}</dd>
            <dt>وضعیت</dt>
            <dd>{page.status}</dd>
            <dt>parent</dt>
            <dd className="mono">{page.parent_page_key?.slice(0, 16) ?? "—"}</dd>
          </dl>
          {page.excerpt && <p>{page.excerpt}</p>}
          {page.meta && Object.keys(page.meta).length > 0 && (
            <>
              <h4>Meta</h4>
              <pre className="meta-block">{metaPreview(page.meta)}</pre>
            </>
          )}
          {page.outbound_links.length > 0 && (
            <>
              <h4>لینک‌های خروجی ({page.outbound_links.length})</h4>
              <ul className="link-list">
                {page.outbound_links.slice(0, 30).map((link) => (
                  <li key={link.page_key}>
                    <span className="tree-type">{link.relation_type}</span>{" "}
                    <ExternalLink href={link.url}>{link.url || link.page_key}</ExternalLink>
                  </li>
                ))}
                {page.outbound_links.length > 30 && (
                  <li className="muted">+ {page.outbound_links.length - 30} لینک دیگر</li>
                )}
              </ul>
            </>
          )}
        </div>
      ) : (
        <p className="muted">یک صفحه از درخت یا نقشه انتخاب کنید.</p>
      )}
    </div>
  );
}
