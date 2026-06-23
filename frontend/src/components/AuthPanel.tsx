import React, { FormEvent, useEffect, useState } from 'react';
import { api, AuthUser } from '../api';

const TOKEN_STORAGE_KEY = 'healthcare_ai_agent_token';

interface AuthPanelProps {
  onAuthChange?: (user: AuthUser | null, token: string | null) => void;
}

export const AuthPanel: React.FC<AuthPanelProps> = ({ onAuthChange }) => {
  const [mode, setMode] = useState<'guest' | 'login' | 'register'>('guest');
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_STORAGE_KEY));
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);

  const [fullName, setFullName] = useState('Demo User');
  const [email, setEmail] = useState('testuser@example.com');
  const [password, setPassword] = useState('password123');
  const [profileName, setProfileName] = useState('');

  const [isLoading, setIsLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string>('');

  useEffect(() => {
    const loadCurrentUser = async () => {
      if (!token) {
        setCurrentUser(null);
        onAuthChange?.(null, null);
        return;
      }

      try {
        const user = await api.getCurrentUser(token);
        setCurrentUser(user);
        setProfileName(user.full_name);
        onAuthChange?.(user, token);
      } catch (error) {
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        setToken(null);
        setCurrentUser(null);
        onAuthChange?.(null, null);
      }
    };

    loadCurrentUser();
  }, [token, onAuthChange]);

  const clearMessages = () => {
    setStatusMessage('');
    setErrorMessage('');
  };

  const handleRegister = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    clearMessages();
    setIsLoading(true);

    try {
      const response = await api.register(fullName, email, password);
      setStatusMessage(`Registered ${response.user.full_name}. You can sign in now.`);
      setMode('login');
    } catch (error) {
      setErrorMessage('Registration failed. The email may already exist.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    clearMessages();
    setIsLoading(true);

    try {
      const response = await api.login(email, password);
      localStorage.setItem(TOKEN_STORAGE_KEY, response.access_token);
      setToken(response.access_token);
      setStatusMessage('Signed in successfully.');
      setMode('guest');
    } catch (error) {
      setErrorMessage('Sign in failed. Please check the email and password.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateProfile = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    clearMessages();

    if (!token) {
      setErrorMessage('You must be signed in to update your profile.');
      return;
    }

    setIsLoading(true);

    try {
      const response = await api.updateProfile(token, profileName);
      setCurrentUser(response.user);
      setProfileName(response.user.full_name);
      setStatusMessage('Profile updated successfully.');
      onAuthChange?.(response.user, token);
    } catch (error) {
      setErrorMessage('Profile update failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    setToken(null);
    setCurrentUser(null);
    setMode('guest');
    setStatusMessage('Logged out. You can continue chatting as a guest.');
    setErrorMessage('');
    onAuthChange?.(null, null);
  };

  if (currentUser) {
    return (
      <div className="card border-0 shadow-sm rounded-4">
        <div className="card-body p-3">
          <div className="d-flex align-items-start justify-content-between gap-2 mb-3">
            <div>
              <p className="text-uppercase text-secondary small fw-semibold mb-1">
                User Account
              </p>
              <h2 className="h6 fw-bold mb-1">{currentUser.full_name}</h2>
              <p className="small text-secondary mb-0">{currentUser.email}</p>
            </div>

            <span className="badge rounded-pill text-bg-success">
              {currentUser.role}
            </span>
          </div>

          <form onSubmit={handleUpdateProfile}>
            <label className="form-label small fw-semibold" htmlFor="profileName">
              Full name
            </label>
            <input
              id="profileName"
              className="form-control form-control-sm mb-2"
              value={profileName}
              onChange={(event) => setProfileName(event.target.value)}
              required
            />

            <div className="d-grid gap-2">
              <button
                className="btn btn-sm btn-primary"
                type="submit"
                disabled={isLoading}
              >
                {isLoading ? 'Updating...' : 'Update profile'}
              </button>

              <button
                className="btn btn-sm btn-outline-secondary"
                type="button"
                onClick={handleLogout}
              >
                Logout
              </button>
            </div>
          </form>

          {statusMessage && (
            <div className="alert alert-success py-2 px-3 mt-3 mb-0 small">
              {statusMessage}
            </div>
          )}

          {errorMessage && (
            <div className="alert alert-danger py-2 px-3 mt-3 mb-0 small">
              {errorMessage}
            </div>
          )}
        </div>
      </div>
    );
  }

  if (mode === 'guest') {
    return (
      <div className="card border-0 shadow-sm rounded-4">
        <div className="card-body p-3">
          <div className="d-flex align-items-start justify-content-between gap-2 mb-3">
            <div>
              <p className="text-uppercase text-secondary small fw-semibold mb-1">
                User Account
              </p>
              <h2 className="h6 fw-bold mb-1">Guest mode</h2>
              <p className="small text-secondary mb-0">
                You can chat with the AI Agent without signing in.
              </p>
            </div>

            <span className="badge rounded-pill text-bg-light border text-secondary">
              Guest
            </span>
          </div>

          <div className="d-grid gap-2">
            <button
              className="btn btn-sm btn-primary"
              type="button"
              onClick={() => {
                clearMessages();
                setMode('login');
              }}
            >
              Sign in
            </button>

            <button
              className="btn btn-sm btn-outline-primary"
              type="button"
              onClick={() => {
                clearMessages();
                setMode('register');
              }}
            >
              Register
            </button>
          </div>

          {statusMessage && (
            <div className="alert alert-success py-2 px-3 mt-3 mb-0 small">
              {statusMessage}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="card border-0 shadow-sm rounded-4">
      <div className="card-body p-3">
        <div className="d-flex align-items-center justify-content-between mb-3">
          <div>
            <p className="text-uppercase text-secondary small fw-semibold mb-1">
              User Account
            </p>
            <h2 className="h6 fw-bold mb-0">
              {mode === 'login' ? 'Sign in' : 'Register'}
            </h2>
          </div>

          <span className="badge rounded-pill text-bg-light border text-secondary">
            JWT
          </span>
        </div>

        <form onSubmit={mode === 'login' ? handleLogin : handleRegister}>
          {mode === 'register' && (
            <>
              <label className="form-label small fw-semibold" htmlFor="fullName">
                Full name
              </label>
              <input
                id="fullName"
                className="form-control form-control-sm mb-2"
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                required
              />
            </>
          )}

          <label className="form-label small fw-semibold" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            className="form-control form-control-sm mb-2"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />

          <label className="form-label small fw-semibold" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            className="form-control form-control-sm mb-3"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />

          <div className="d-grid gap-2">
            <button
              className="btn btn-sm btn-primary"
              type="submit"
              disabled={isLoading}
            >
              {isLoading
                ? 'Please wait...'
                : mode === 'login'
                  ? 'Sign in'
                  : 'Create account'}
            </button>

            <button
              className="btn btn-sm btn-outline-secondary"
              type="button"
              onClick={() => {
                clearMessages();
                setMode('guest');
              }}
            >
              Continue as guest
            </button>
          </div>
        </form>

        {statusMessage && (
          <div className="alert alert-success py-2 px-3 mt-3 mb-0 small">
            {statusMessage}
          </div>
        )}

        {errorMessage && (
          <div className="alert alert-danger py-2 px-3 mt-3 mb-0 small">
            {errorMessage}
          </div>
        )}
      </div>
    </div>
  );
};