import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { inspectorApi, type SiteGraph, type SitePageDetail, type SiteSection, type SiteTreeNode } from "../api/inspector";
import CrawlEventFeed from "../components/inspector/CrawlEventFeed";
import PageDetailPanel from "../components/inspector/PageDetailPanel";
import SiteGraphView from "../components/inspector/SiteGraphView";
import SiteMapControl from "../components/inspector/SiteMapControl";
import SiteTreeView from "../components/inspector/SiteTreeView";
import { useSiteMapJob } from "../hooks/useSiteMapJob";

type ViewTab = "tree" | "graph";

export default function InspectorPage() {
  const { job, events, loading, error, start, pause, resume, cancel } = useSiteMapJob();
  const [tab, setTab] = useState<ViewTab>("tree");
  const [tree, setTree] = useState<SiteTreeNode[]>([]);
  const [graph, setGraph] = useState<SiteGraph | null>(null);
  const [sections, setSections] = useState<SiteSection[]>([]);
  const [selectedSection, setSelectedSection] = useState<string | null>(null);
  const [selectedPageKey, setSelectedPageKey] = useState<string | null>(null);
  const [pageDetail, setPageDetail] = useState<SitePageDetail | null>(null);

  const refreshSiteData = useCallback(async () => {
    const [treeData, graphData, sectionData] = await Promise.all([
      inspectorApi.getTree(selectedSection ?? undefined),
      inspectorApi.getGraph(selectedSection ?? undefined, 300),
      inspectorApi.getSections(),
    ]);
    setTree(treeData);
    setGraph(graphData);
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

  return (
    <div className="inspector-page">
      <header className="topbar">
        <div>
          <h1>Site Inspector</h1>
          <p className="muted">مشاهده ساختار bama.ir، گراف لینک‌ها و progress کرawl</p>
        </div>
        <Link to="/" className="link-button">
          بازگشت به داشبورد
        </Link>
      </header>

      <SiteMapControl
        job={job}
        loading={loading}
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
              className={tab === "graph" ? "" : "secondary"}
              onClick={() => setTab("graph")}
            >
              گراف
            </button>
          </div>
          {tab === "tree" ? (
            <SiteTreeView
              nodes={tree}
              selectedKey={selectedPageKey}
              onSelect={setSelectedPageKey}
            />
          ) : (
            <SiteGraphView
              graph={graph}
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
