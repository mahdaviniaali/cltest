import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import AdPreviewPanel, { useDataRefresh } from "../components/AdPreviewPanel";
import { SearchSummary } from "../components/SearchForm";
import type { DataPreview, Search } from "../types";

export default function SearchResultsPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const searchId = Number(id);

  const [search, setSearch] = useState<Search | null>(null);
  const [preview, setPreview] = useState<DataPreview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadResults = useCallback(async () => {
    if (!searchId) return;
    setLoading(true);
    setError("");
    try {
      const [searchData, previewData] = await Promise.all([
        api.listSearches().then((list) => list.find((s) => s.id === searchId) ?? null),
        api.getSearchResults(searchId),
      ]);
      if (!searchData) {
        setError("فیلتر یافت نشد");
        return;
      }
      setSearch(searchData);
      setPreview(previewData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "خطا در بارگذاری");
    } finally {
      setLoading(false);
    }
  }, [searchId]);

  useEffect(() => {
    void loadResults();
  }, [loadResults]);

  const { refreshing, triggerRefresh } = useDataRefresh(() => {
    void loadResults();
  });

  return (
    <div className="dashboard">
      <header className="topbar">
        <div>
          <button className="secondary" onClick={() => navigate("/")}>
            ← بازگشت
          </button>
          <h1>نتایج فیلتر</h1>
          {search && <SearchSummary search={search} />}
        </div>
      </header>

      {loading && <p className="muted">در حال بارگذاری...</p>}
      {error && <p className="error">{error}</p>}

      {!loading && !error && preview && (
        <AdPreviewPanel
          preview={preview}
          loading={false}
          onRefresh={() => void triggerRefresh()}
          refreshing={refreshing}
        />
      )}

      {search && (
        <p className="muted">
          <Link to="/">مدیریت فیلترها</Link>
        </p>
      )}
    </div>
  );
}
