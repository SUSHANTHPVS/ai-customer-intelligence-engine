import React, { useState } from 'react';
import { FiUser, FiLock, FiMail, FiLogIn, FiUserPlus, FiShield } from 'react-icons/fi';
import useAuthStore from '../store/authStore';

const Login = () => {
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [twoFactorCode, setTwoFactorCode] = useState('');
  const { login, register, verifyTwoFactor, pendingTwoFactorToken, authLoading, authError, clearAuthError } = useAuthStore();

  const handleSubmit = async (e) => {
    e.preventDefault();
    clearAuthError();
    if (mode === 'login') {
      await login(username, password);
    } else {
      await register(username, email, password);
    }
  };

  const handleTwoFactorSubmit = async (e) => {
    e.preventDefault();
    clearAuthError();
    await verifyTwoFactor(twoFactorCode);
  };

  if (pendingTwoFactorToken) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-900">
        <div className="w-full max-w-md bg-gray-800 rounded-xl shadow-2xl p-8">
          <div className="text-center mb-8">
            <FiShield className="mx-auto text-blue-400 mb-2" size={32} />
            <h1 className="text-2xl font-bold text-white">Two-Factor Verification</h1>
            <p className="text-gray-400 mt-2">Enter the 6-digit code from your authenticator app</p>
          </div>

          {authError && (
            <div className="mb-4 bg-red-500/10 border border-red-500/40 text-red-400 text-sm rounded-lg px-4 py-3">
              {authError}
            </div>
          )}

          <form onSubmit={handleTwoFactorSubmit} className="space-y-4">
            <input
              type="text"
              inputMode="numeric"
              placeholder="000000"
              value={twoFactorCode}
              onChange={(e) => setTwoFactorCode(e.target.value)}
              maxLength={6}
              required
              className="w-full text-center tracking-[0.5em] text-lg py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
            <button
              type="submit"
              disabled={authLoading}
              className="w-full flex items-center justify-center gap-2 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg font-semibold transition-colors"
            >
              {authLoading ? 'Verifying...' : 'Verify & Sign In'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen items-center justify-center bg-gray-900">
      <div className="w-full max-w-md bg-gray-800 rounded-xl shadow-2xl p-8">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-white">Customer Intelligence</h1>
          <p className="text-gray-400 mt-2">
            {mode === 'login' ? 'Sign in to your account' : 'Create a new account'}
          </p>
        </div>

        {authError && (
          <div className="mb-4 bg-red-500/10 border border-red-500/40 text-red-400 text-sm rounded-lg px-4 py-3">
            {authError}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <FiUser className="absolute left-3 top-3.5 text-gray-500" />
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="w-full pl-10 pr-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
            />
          </div>

          {mode === 'register' && (
            <div className="relative">
              <FiMail className="absolute left-3 top-3.5 text-gray-500" />
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full pl-10 pr-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
              />
            </div>
          )}

          <div className="relative">
            <FiLock className="absolute left-3 top-3.5 text-gray-500" />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              className="w-full pl-10 pr-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
            />
          </div>

          <button
            type="submit"
            disabled={authLoading}
            className="w-full flex items-center justify-center gap-2 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg font-semibold transition-colors"
          >
            {mode === 'login' ? <FiLogIn /> : <FiUserPlus />}
            {authLoading ? 'Please wait...' : mode === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>

        <p className="text-center text-sm text-gray-400 mt-6">
          {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
          <button
            onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); clearAuthError(); }}
            className="text-blue-400 hover:text-blue-300 font-medium"
          >
            {mode === 'login' ? 'Register' : 'Sign In'}
          </button>
        </p>

        {mode === 'login' && (
          <p className="text-center text-xs text-gray-500 mt-4">
            Demo credentials: admin / admin123
          </p>
        )}
      </div>
    </div>
  );
};

export default Login;
