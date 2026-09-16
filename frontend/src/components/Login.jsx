import React, { useState } from 'react';
import { FiUser, FiLock, FiMail, FiLogIn, FiUserPlus, FiShield, FiArrowRight } from 'react-icons/fi';
import useAuthStore from '../store/authStore';

const Login = () => {
  const [mode, setMode] = useState('login'); // 'login' | 'register-choice' | 'register-user' | 'register-admin'
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [twoFactorCode, setTwoFactorCode] = useState('');
  const { login, register, verifyTwoFactor, pendingTwoFactorToken, authLoading, authError, clearAuthError } = useAuthStore();

  const isRegisterMode = mode !== 'login' && mode !== 'register-choice';
  const isAdminRegister = mode === 'register-admin';
  const isRegisterChoice = mode === 'register-choice';

  const handleSubmit = async (e) => {
    e.preventDefault();
    clearAuthError();
    if (mode === 'login') {
      await login(username, password);
    } else {
      await register(username, email, password, isAdminRegister ? 'admin' : 'analyst');
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
    <div className="flex h-screen items-center justify-center bg-[#1d2a35] px-4">
      <div className="w-full max-w-[540px] rounded-[28px] bg-[#2d3d4d] shadow-[0_20px_50px_rgba(15,23,42,0.45)] p-6 md:p-7">
        <div className="text-center mb-6">
          <h1 className="text-[2.5rem] md:text-[3rem] font-extrabold text-white tracking-tight leading-none">Customer Intelligence</h1>
          <p className="text-xl md:text-[1.9rem] font-medium text-gray-100 mt-4">
            {mode === 'login' ? 'Sign in to your account' : 'Create a new account'}
          </p>
        </div>

        {authError && (
          <div className="mb-4 bg-red-500/10 border border-red-500/40 text-red-400 text-sm rounded-lg px-4 py-3">
            {authError}
          </div>
        )}

        {isRegisterChoice ? (
          <div className="mt-6 space-y-4">
            <button
              type="button"
              onClick={() => { setMode('register-user'); clearAuthError(); }}
              className="w-full flex items-center justify-center gap-3 py-4 bg-[#0f7ae5] hover:bg-[#0d6fd0] text-white rounded-xl font-semibold text-xl transition-colors"
            >
              <FiUserPlus size={22} />
              Register as User
            </button>

            <button
              type="button"
              onClick={() => { setMode('register-admin'); clearAuthError(); }}
              className="w-full flex items-center justify-center gap-3 py-4 bg-[#0f7ae5] hover:bg-[#0d6fd0] text-white rounded-xl font-semibold text-xl transition-colors"
            >
              <FiShield size={22} />
              Register as Admin
            </button>

            <div className="text-center mt-4">
              <button
                type="button"
                onClick={() => { setMode('login'); clearAuthError(); }}
                className="text-blue-300 font-semibold hover:text-blue-200"
              >
                Back to Sign In
              </button>
            </div>
          </div>
        ) : (
          <>
            <form onSubmit={handleSubmit} className="space-y-3 mt-6">
              <div className="relative">
                <FiUser className="absolute left-4 top-4 text-gray-300" size={24} />
                <input
                  type="text"
                  placeholder="Username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  className="w-full pl-14 pr-4 py-4 bg-[#5d6f80] border border-transparent rounded-xl text-white placeholder-gray-200 text-[1.05rem] focus:outline-none focus:border-blue-400"
                />
              </div>

              {isRegisterMode && (
                <div className="relative">
                  <FiMail className="absolute left-4 top-4 text-gray-300" size={24} />
                  <input
                    type="email"
                    placeholder="Email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full pl-14 pr-4 py-4 bg-[#5d6f80] border border-transparent rounded-xl text-white placeholder-gray-200 text-[1.05rem] focus:outline-none focus:border-blue-400"
                  />
                </div>
              )}

              <div className="relative">
                <FiLock className="absolute left-4 top-4 text-gray-300" size={24} />
                <input
                  type="password"
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                  className="w-full pl-14 pr-4 py-4 bg-[#5d6f80] border border-transparent rounded-xl text-white placeholder-gray-200 text-[1.05rem] focus:outline-none focus:border-blue-400"
                />
              </div>

              <button
                type="submit"
                disabled={authLoading}
                className="w-full flex items-center justify-center gap-3 py-3 bg-[#0f7ae5] hover:bg-[#0d6fd0] disabled:opacity-50 text-white rounded-xl font-bold text-[1.45rem] transition-colors mt-2"
              >
                {mode === 'login' ? <FiArrowRight size={24} /> : <FiUserPlus size={24} />}
                {authLoading
                  ? 'Please wait...'
                  : mode === 'login'
                    ? 'Sign In'
                    : isAdminRegister
                      ? 'Create Admin Account'
                      : 'Create Account'}
              </button>
            </form>

            {mode === 'login' ? (
              <div className="mt-6 text-center">
                <p className="text-[1rem] text-gray-300 leading-relaxed">
                  Don’t have an account?{' '}
                  <button
                    type="button"
                    onClick={() => { setMode('register-choice'); clearAuthError(); }}
                    className="text-blue-300 font-semibold hover:text-blue-200"
                  >
                    Register
                  </button>
                </p>
                <p className="text-[0.9rem] text-gray-400 mt-4">
                  Demo credentials: admin / admin123
                </p>
              </div>
            ) : (
              <div className="mt-6 text-center">
                <p className="text-xl text-gray-200">
                  Already have an account?{' '}
                  <button
                    type="button"
                    onClick={() => { setMode('login'); clearAuthError(); }}
                    className="text-blue-300 font-semibold hover:text-blue-200"
                  >
                    Sign In
                  </button>
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default Login;
