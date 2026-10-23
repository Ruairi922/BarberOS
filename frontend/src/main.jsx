import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { LockKeyhole, LogOut, ArrowLeft } from 'lucide-react';

import {
  getShop,
  getAdminServices,
  loginAdmin,
  clearAdminToken,
} from './api';

import Storefront from './pages/Storefront';
import Dashboard from './pages/Dashboard';

import './style.css';
import './blue-refresh.css';

function App() {
  const isAdmin = window.location.pathname.replace(/\/$/, '') === '/admin';

  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [authenticated, setAuthenticated] = useState(false);
  const [username, setUsername] = useState('Aaron');
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [loadingLogin, setLoadingLogin] = useState(false);

  const reload = async () => {
    try {
      const result = await getShop();
      setData(result);
      setError('');
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  useEffect(() => {
    reload().catch(() => {});
  }, []);

  const login = async (event) => {
    event.preventDefault();

    setLoginError('');
    setLoadingLogin(true);

    try {
      await loginAdmin(username.trim(), password);
      await getAdminServices();

      setAuthenticated(true);
      setPassword('');
    } catch (err) {
      clearAdminToken();
      setLoginError('Invalid credentials or admin login unavailable.');
    } finally {
      setLoadingLogin(false);
    }
  };

  const logout = () => {
    clearAdminToken();
    setAuthenticated(false);
    setPassword('');
  };

  if (error || !data) {
    return (
      <div className="loading-page">
        <b>AB<span>.</span></b>
        <p>{error || 'Loading BarberOS…'}</p>

        <button onClick={() => reload().catch(() => {})}>
          Retry connection
        </button>
      </div>
    );
  }

  if (isAdmin) {
    if (!authenticated) {
      return (
        <div className="admin-login-screen">
          <form className="admin-login-card" onSubmit={login}>
            <a href="/" className="admin-back-link">
              <ArrowLeft size={16} />
              Back to website
            </a>

            <div className="admin-login-mark">
              AB<span>.</span>
            </div>

            <div className="admin-login-icon">
              <LockKeyhole size={21} />
            </div>

            <h1>Admin Login</h1>

            <p>
              Aaron Binions
              <br />
              BarberOS Management
            </p>

            <label htmlFor="admin-username">USERNAME</label>
            <input id="admin-username" type="text" autoComplete="username"
              value={username} onChange={(e) => setUsername(e.target.value)} required />

            <label htmlFor="admin-password" style={{ marginTop: 15 }}>PASSWORD</label>
            <input id="admin-password" type="password" autoComplete="current-password"
              placeholder="Enter your password" value={password}
              onChange={(e) => setPassword(e.target.value)} required />

            {loginError && (
              <div className="admin-login-error" role="alert">
                {loginError}
              </div>
            )}

            <button
              type="submit"
              disabled={loadingLogin || !username.trim() || !password}
            >
              {loadingLogin ? 'Checking…' : 'Sign in'}
            </button>

            <small>Private management access</small>
          </form>
        </div>
      );
    }

    return (
      <div>
        <div className="admin-session-bar">
          <span>BarberOS — Aaron's Dashboard</span>

          <button onClick={logout}>
            <LogOut size={15} />
            Sign out
          </button>
        </div>

        <Dashboard data={data} refresh={reload} />
      </div>
    );
  }

  return <Storefront data={data} />;
}

createRoot(document.getElementById('root')).render(<App />);