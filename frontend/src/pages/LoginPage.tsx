import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? String(err.message) : "خطا در ورود");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-card">
      <h1>ورود</h1>
      <p className="muted">به سیستم فیلتر آگهی باما خوش آمدید</p>
      <form onSubmit={handleSubmit} className="form">
        <label>
          ایمیل
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label>
          رمز عبور
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
          />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={submitting}>
          {submitting ? "در حال ورود..." : "ورود"}
        </button>
      </form>
      <p className="muted">
        حساب ندارید؟ <Link to="/register">ثبت‌نام</Link>
      </p>
    </div>
  );
}
