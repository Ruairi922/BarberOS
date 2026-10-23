import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { LockKeyhole, LogOut, ArrowLeft } from 'lucide-react';

import {
  getShop,
  getAdminServices,
  setAdminToken,
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
  const [accessKey, setAccessKey] = useState('');
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
      setAdminToken(accessKey.trim());

      // Verifies the key against an authenticated backend endpoint.
      await getAdminServices();

      setAuthenticated(true);
      setAccessKey('');
    } catch (err) {
      clearAdminToken();
      setLoginError('Invalid access key or admin access unavailable.');
    } finally {
      setLoadingLogin(false);
    }
  };

  const logout = () => {
    clearAdminToken();
    setAuthenticated(false);
    setAccessKey('');
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

            <label htmlFor="admin-key">
              ACCESS KEY
            </label>

            <input
              id="admin-key"
              type="password"
              autoComplete="off"
              placeholder="Enter your access key"
              value={accessKey}
              onChange={(e) => setAccessKey(e.target.value)}
              required
            />

            {loginError && (
              <div className="admin-login-error" role="alert">
                {loginError}
              </div>
            )}

            <button
              type="submit"
              disabled={loadingLogin || !accessKey.trim()}
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