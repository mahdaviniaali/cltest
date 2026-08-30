import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await register(email, password, fullName || undefined);
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? String(err.message) : "خطا در ثبت‌نام");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-card">
      <h1>ثبت‌نام</h1>
      <p className="muted">حساب جدید بسازید و فیلتر آگهی تعریف کنید</p>
      <form onSubmit={handleSubmit} className="form">
        <label>
          نام (اختیاری)
          <input value={fullName} onChange={(e) => setFullName(e.target.value)} />
        </label>
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
          {submitting ? "در حال ثبت‌نام..." : "ثبت‌نام"}
        </button>
      </form>
      <p className="muted">
        قبلاً ثبت‌نام کرده‌اید؟ <Link to="/login">ورود</Link>
      </p>
    </div>
  );
}
