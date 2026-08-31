import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { inspectorApi, type SiteMap, type SitePageDetail, type SiteSection, type SiteTreeNode } from "../api/inspector";
import CrawlEventFeed from "../components/inspector/CrawlEventFeed";
import PageDetailPanel from "../components/inspector/PageDetailPanel";
import SiteMapControl from "../components/inspector/SiteMapControl";
import SiteMapView from "../components/inspector/SiteMapView";
import SiteTreeView from "../components/inspector/SiteTreeView";
import { useSiteMapJob } from "../hooks/useSiteMapJob";

type ViewTab = "tree" | "map";

export default function InspectorPage() {
  const { job, events, loading, error, start, pause, resume, cancel } = useSiteMapJob();
  const [tab, setTab] = useState<ViewTab>("map");
  const [tree, setTree] = useState<SiteTreeNode[]>([]);
  const [siteMap, setSiteMap] = useState<SiteMap | null>(null);
  const [sections, setSections] = useState<SiteSection[]>([]);
  const [selectedSection, setSelectedSection] = useState<string | null>(null);
  const [selectedPageKey, setSelectedPageKey] = useState<string | null>(null);
  const [pageDetail, setPageDetail] = useState<SitePageDetail | null>(null);

  const refreshSiteData = useCallback(async () => {
    const [treeData, mapData, sectionData] = await Promise.all([
      inspectorApi.getTree(selectedSection ?? undefined),
      inspectorApi.getMap(selectedSection ?? undefined),
      inspectorApi.getSections(),
    ]);
    setTree(treeData);
    setSiteMap(mapData);
    setSections(sectionData);
  }, [selectedSection]);

  useEffect(() => {
    void refreshSiteData().catch(() => undefined);
    const id = window.setInterval(() => {
      void refreshSiteData().catch(() => undefined);
    }, 5000);
    return () => window.clearInterval(id);
  }, [refreshSiteData]);

  useEffect(() => {
    if (!selectedPageKey) {
      setPageDetail(null);
      return;
    }
    void inspectorApi
      .getPage(selectedPageKey)
      .then(setPageDetail)
      .catch(() => setPageDetail(null));
  }, [selectedPageKey]);

  const levelProgress = useMemo(() => {
    if (!job) return { pages: 0, sections: [] as string[] };
    const completed = [...events].reverse().find((e) => e.event_type === "level_completed");
    const completedDepth = completed ? Number(completed.payload.depth ?? -1) : -1;
    if (completed && completedDepth === job.current_depth) {
      return {
        pages: Number(completed.payload.pages_at_level ?? 0),
        sections: (completed.payload.sections_seen as string[]) ?? [],
      };
    }
    const sections = new Set<string>();
    let pages = 0;
    for (const event of events) {
      if (event.event_type !== "page_fetched") continue;
      if (Number(event.payload.depth) !== job.current_depth) continue;
      pages += 1;
      const section = event.payload.section;
      if (typeof section === "string" && section) sections.add(section);
    }
    return { pages, sections: [...sections] };
  }, [events, job]);

  return (
    <div className="inspector-page">
      <header className="topbar">
        <div>
          <h1>Site Inspector</h1>
          <p className="muted">مشاهده ساختار bama.ir، نقشه سایت و progress کرawl</p>
        </div>
        <Link to="/" className="link-button">
          بازگشت به داشبورد
        </Link>
      </header>

      <SiteMapControl
        job={job}
        loading={loading}
        currentLevelPages={levelProgress.pages}
        sectionsAtLevel={levelProgress.sections}
        onStart={(maxPages, maxDepth) => void start(maxPages, maxDepth)}
        onPause={() => void pause()}
        onResume={() => void resume()}
        onCancel={() => void cancel()}
      />

      {error && <p className="error">{error}</p>}

      <div className="inspector-grid">
        <aside className="inspector-sidebar">
          <PageDetailPanel
            page={pageDetail}
            sections={sections}
            selectedSection={selectedSection}
            onSectionSelect={setSelectedSection}
          />
        </aside>

        <main className="inspector-main">
          <div className="tab-row">
            <button
              type="button"
              className={tab === "tree" ? "" : "secondary"}
              onClick={() => setTab("tree")}
            >
              درخت URL
            </button>
            <button
              type="button"
              className={tab === "map" ? "" : "secondary"}
              onClick={() => setTab("map")}
            >
              نقشه سایت
            </button>
          </div>
          {tab === "tree" ? (
            <SiteTreeView
              nodes={tree}
              selectedKey={selectedPageKey}
              onSelect={setSelectedPageKey}
            />
          ) : (
            <SiteMapView
              siteMap={siteMap}
              selectedKey={selectedPageKey}
              onSelect={setSelectedPageKey}
            />
          )}
        </main>

        <aside className="inspector-events">
          <h3>رویدادهای زنده</h3>
          <CrawlEventFeed events={events} />
        </aside>
      </div>
    </div>
  );
}
