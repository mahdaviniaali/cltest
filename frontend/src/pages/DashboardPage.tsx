import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import SearchForm, { SearchSummary } from "../components/SearchForm";
import { useAuth } from "../context/AuthContext";
import type { Search, SearchCreateResponse, SearchInput } from "../types";

export default function DashboardPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [searches, setSearches] = useState<Search[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState<Search | null>(null);
  const [showForm, setShowForm] = useState(false);

  const loadSearches = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await api.listSearches();
      setSearches(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "خطا در بارگذاری");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadSearches();
  }, [loadSearches]);

  async function handleCreate(data: SearchInput) {
    const created: SearchCreateResponse = await api.createSearch(data);
    setShowForm(false);
    await loadSearches();
    if (created.is_crawling && created.job_id) {
      navigate(`/searches/${created.id}`);
      return;
    }
    navigate(`/searches/${created.id}`);
  }

  async function handleUpdate(data: SearchInput) {
    if (!editing) return;
    await api.updateSearch(editing.id, data);
    setEditing(null);
    await loadSearches();
  }

  async function handleDelete(id: number) {
    if (!confirm("این فیلتر حذف شود؟")) return;
    await api.deleteSearch(id);
    await loadSearches();
  }

  async function handleToggle(id: number) {
    await api.toggleSearch(id);
    await loadSearches();
  }

  return (
    <div className="dashboard">
      <header className="topbar">
        <div>
          <h1>فیلترهای من</h1>
          <p className="muted">{user?.full_name || user?.email}</p>
        </div>
        <div className="actions">
          <Link to="/admin/inspector" className="link-button">
            Site Inspector
          </Link>
          <button onClick={() => { setEditing(null); setShowForm(true); }}>+ فیلتر جدید</button>
          <button className="secondary" onClick={logout}>
            خروج
          </button>
        </div>
      </header>

      {(showForm || editing) && (
        <SearchForm
          initial={editing ?? undefined}
          onSubmit={editing ? handleUpdate : handleCreate}
          onCancel={() => {
            setShowForm(false);
            setEditing(null);
          }}
        />
      )}

      <section className="panel">
        {loading && <p className="muted">در حال بارگذاری...</p>}
        {error && <p className="error">{error}</p>}
        {!loading && searches.length === 0 && (
          <p className="muted">هنوز فیلتری تعریف نکرده‌اید.</p>
        )}
        <ul className="search-list">
          {searches.map((search) => (
            <li key={search.id} className={search.enabled ? "" : "disabled"}>
              <div className="search-item">
                <div>
                  <div className="badge-row">
                    <span className={`badge ${search.enabled ? "on" : "off"}`}>
                      {search.enabled ? "فعال" : "غیرفعال"}
                    </span>
                  </div>
                  <SearchSummary search={search} />
                </div>
                <div className="actions">
                  <Link to={`/searches/${search.id}`} className="link-button">
                    نتایج
                  </Link>
                  <button className="secondary" onClick={() => handleToggle(search.id)}>
                    {search.enabled ? "غیرفعال" : "فعال"}
                  </button>
                  <button className="secondary" onClick={() => { setShowForm(false); setEditing(search); }}>
                    ویرایش
                  </button>
                  <button className="danger" onClick={() => void handleDelete(search.id)}>
                    حذف
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
