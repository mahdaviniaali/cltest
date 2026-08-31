import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { inspectorApi, type SiteMap, type SitePageDetail, type SiteSection, type SiteTreeNode, type StatsOverview } from "../api/inspector";
import { taxonomyApi } from "../api/taxonomy";
import CrawlEventFeed from "../components/inspector/CrawlEventFeed";
import InspectorOverviewBar from "../components/inspector/InspectorOverviewBar";
import InspectorStatsView from "../components/inspector/InspectorStatsView";
import InspectorTasksView from "../components/inspector/InspectorTasksView";
import PageDetailPanel from "../components/inspector/PageDetailPanel";
import SiteMapControl from "../components/inspector/SiteMapControl";
import SiteMapView from "../components/inspector/SiteMapView";
import SiteTreeView from "../components/inspector/SiteTreeView";
import { useSiteMapJob } from "../hooks/useSiteMapJob";

type ViewTab = "tree" | "map" | "stats" | "tasks";

export default function InspectorPage() {
  const { jobs, job, events, loading, error, start, pause, resume, cancel, selectJob } = useSiteMapJob();
  const [tab, setTab] = useState<ViewTab>("map");
  const [tree, setTree] = useState<SiteTreeNode[]>([]);
  const [siteMap, setSiteMap] = useState<SiteMap | null>(null);
  const [sections, setSections] = useState<SiteSection[]>([]);
  const [overview, setOverview] = useState<StatsOverview | null>(null);
  const [overviewLoading, setOverviewLoading] = useState(true);
  const [selectedSection, setSelectedSection] = useState<string | null>(null);
  const [selectedPageKey, setSelectedPageKey] = useState<string | null>(null);
  const [pageDetail, setPageDetail] = useState<SitePageDetail | null>(null);
  const [siteDataError, setSiteDataError] = useState("");
  const [harvestLoading, setHarvestLoading] = useState(false);
  const [harvestMessage, setHarvestMessage] = useState("");

  const refreshSiteData = useCallback(async () => {
    const [treeData, mapData, sectionData] = await Promise.all([
      inspectorApi.getTree(selectedSection ?? undefined),
      inspectorApi.getMap(selectedSection ?? undefined),
      inspectorApi.getSections(),
    ]);
    setTree(treeData);
    setSiteMap(mapData);
    setSections(sectionData);
    setSiteDataError("");
  }, [selectedSection]);

  const refreshOverview = useCallback(async () => {
    try {
      const data = await inspectorApi.getStatsOverview();
      setOverview(data);
    } catch {
      /* overview bar is optional */
    } finally {
      setOverviewLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshSiteData().catch((err) => {
      setSiteDataError(err instanceof Error ? err.message : "خطا در بارگذاری داده سایت");
    });
    const id = window.setInterval(() => {
      void refreshSiteData().catch((err) => {
        setSiteDataError(err instanceof Error ? err.message : "خطا در بارگذاری داده سایت");
      });
    }, 5000);
    return () => window.clearInterval(id);
  }, [refreshSiteData]);

  useEffect(() => {
    void refreshOverview();
    const id = window.setInterval(() => void refreshOverview(), 10000);
    return () => window.clearInterval(id);
  }, [refreshOverview]);

  useEffect(() => {
    setSelectedPageKey(null);
  }, [selectedSection]);

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

  async function harvestCatalog() {
    setHarvestLoading(true);
    setHarvestMessage("");
    try {
      const result = await taxonomyApi.harvest();
      setHarvestMessage(`کاتالوگ: ${result.brands} برند، ${result.models} مدل`);
      await refreshSiteData();
      await refreshOverview();
    } catch (err) {
      setHarvestMessage(err instanceof Error ? err.message : "کشف برند و مدل ناموفق بود");
    } finally {
      setHarvestLoading(false);
    }
  }

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
    const sectionsSeen = new Set<string>();
    let pages = 0;
    for (const event of events) {
      if (event.event_type !== "page_fetched") continue;
      if (Number(event.payload.depth) !== job.current_depth) continue;
      pages += 1;
      const section = event.payload.section;
      if (typeof section === "string" && section) sectionsSeen.add(section);
    }
    return { pages, sections: [...sectionsSeen] };
  }, [events, job]);

  const siteNodeCount = siteMap?.nodes.reduce((sum, n) => sum + n.page_count, 0) ?? 0;

  return (
    <div className="inspector-page">
      <header className="topbar">
        <div>
          <h1>Site Inspector</h1>
          <p className="muted">مشاهده ساختار bama.ir، نقشه سایت، آمار و تسک‌های در حال اجرا</p>
        </div>
        <Link to="/" className="link-button">
          بازگشت به داشبورد
        </Link>
      </header>

      <InspectorOverviewBar overview={overview} siteNodeCount={siteNodeCount} loading={overviewLoading} />

      <SiteMapControl
        job={job}
        jobs={jobs}
        loading={loading}
        currentLevelPages={levelProgress.pages}
        sectionsAtLevel={levelProgress.sections}
        onStart={(maxPages, maxDepth) => void start(maxPages, maxDepth)}
        onPause={() => void pause()}
        onResume={() => void resume()}
        onCancel={() => void cancel()}
        onSelectJob={(jobId) => void selectJob(jobId)}
        onHarvest={() => void harvestCatalog()}
        harvestLoading={harvestLoading}
      />

      {error && <p className="error">{error}</p>}
      {siteDataError && <p className="error">{siteDataError}</p>}
      {harvestMessage && <p className="muted">{harvestMessage}</p>}

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
              {tree.length > 0 && <span className="tab-badge">{tree.length}</span>}
            </button>
            <button
              type="button"
              className={tab === "map" ? "" : "secondary"}
              onClick={() => setTab("map")}
            >
              نقشه سایت
              {siteMap && siteMap.nodes.length > 0 && (
                <span className="tab-badge">{siteMap.nodes.length}</span>
              )}
            </button>
            <button type="button" className={tab === "stats" ? "" : "secondary"} onClick={() => setTab("stats")}>
              آمار
            </button>
            <button type="button" className={tab === "tasks" ? "" : "secondary"} onClick={() => setTab("tasks")}>
              تسک‌ها
              {overview && overview.crawl_health.running > 0 && (
                <span className="tab-badge running">{overview.crawl_health.running}</span>
              )}
            </button>
          </div>
          {tab === "stats" ? (
            <InspectorStatsView />
          ) : tab === "tasks" ? (
            <InspectorTasksView />
          ) : tab === "tree" ? (
            <SiteTreeView nodes={tree} selectedKey={selectedPageKey} onSelect={setSelectedPageKey} />
          ) : (
            <SiteMapView siteMap={siteMap} selectedKey={selectedPageKey} onSelect={setSelectedPageKey} />
          )}
        </main>

        <aside className="inspector-events">
          <div className="events-head">
            <h3>رویدادهای زنده</h3>
            {job && <span className="muted mono">{job.job_id.slice(0, 10)}…</span>}
          </div>
          <CrawlEventFeed events={events} />
        </aside>
      </div>
    </div>
  );
}
