import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Lock, Eye, EyeOff, LogIn, ShieldAlert, Laptop } from 'lucide-react';
import { useAssetManager } from '../hooks/useAssetManager';
import QuadrantLogo from '../components/QuadrantLogo';
import logoImg from '../assets/logo.png';

// import slide1 from '../assets/slide1.jpg';
// import slide2 from '../assets/slide2.jpg';
// import slide3 from '../assets/slide3.jpg';
// import bg from '../assets/BG.png';
import loginBg from '../assets/login-bg.jpg';

const Login = () => {
  const { loginUser } = useAssetManager();
  const navigate = useNavigate();

  // Background slideshow state
  const bgImages = [loginBg];
  const [activeBgIndex, setActiveBgIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveBgIndex((prev) => (prev + 1) % bgImages.length);
    }, 5500);
    return () => clearInterval(timer);
  }, []);

  // Form states
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('Admin'); // Admin | Employee
  const [showPassword, setShowPassword] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setErrorMsg('');

    const trimmedUser = username.trim();
    if (!trimmedUser) {
      setErrorMsg('Username is required.');
      return;
    }

    setIsLoggingIn(true);

    setTimeout(async () => {
      try {
        const result = await loginUser(trimmedUser, password);
        if (result.success) {
          if (result.user.role === 'Admin') {
            navigate('/');
          } else {
            navigate('/employee');
          }
        } else {
          setErrorMsg(result.message);
          setIsLoggingIn(false);
        }
      } catch (err) {
        setErrorMsg("Network error or server offline");
        setIsLoggingIn(false);
      }
    }, 800);
  };

  const handleSandboxLogin = async (sandboxUsername, sandboxPassword, sandboxRole) => {
    setErrorMsg('');
    try {
      const result = await loginUser(sandboxUsername, sandboxPassword, sandboxRole);
      if (result.success) {
        if (result.user.role === 'Admin') {
          navigate('/');
        } else {
          navigate('/employee');
        }
      } else {
        setErrorMsg(result.message);
      }
    } catch (err) {
      setErrorMsg("Network error or server offline");
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-center lg:justify-start items-center lg:items-end p-4 lg:pr-72 lg:pt-8 relative overflow-hidden font-sans">
      {/* Background Slideshow Images */}
      {bgImages.map((src, index) => (
        <div
          key={index}
          className="absolute inset-0 bg-cover transition-opacity duration-1000 ease-in-out pointer-events-none"
          style={{
            backgroundImage: `url(${src})`,
            backgroundPosition: 'center bottom',
            opacity: activeBgIndex === index ? 1.0 : 0
          }}
        />
      ))}
      {/* Light overlay to keep background bright but readable */}
      <div className="absolute inset-0 bg-white/10 z-0 pointer-events-none" />



      {/* Main card — white frosted glass to match bright background */}
      <div className="w-full max-w-md backdrop-blur-xl bg-white/80 border border-white/60 rounded-[2.5rem] p-8 shadow-2xl shadow-slate-300/40 space-y-6 relative z-10 animate-fade-in">
        {/* Logo and title */}
        <div className="flex flex-col items-center space-y-3">
          <div className="shrink-0 overflow-hidden rounded-2xl bg-white border border-slate-200 shadow-md shadow-slate-200/60">
            <QuadrantLogo className="h-16 w-16 object-cover" />
          </div>
          <div className="text-center">
            <h2 className="text-xl font-bold text-slate-800 tracking-tight">Quadrant IT Services</h2>
            <p className="text-xs text-slate-500 font-semibold mt-1">Asset Management Portal</p>
          </div>
        </div>


        {/* Error notification */}
        {errorMsg && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-2xl flex items-start gap-2.5 text-xs text-rose-600 animate-shake">
            <ShieldAlert className="h-4 w-4 shrink-0 mt-0.5" />
            <span className="font-semibold leading-relaxed">{errorMsg}</span>
          </div>
        )}

        {/* Credentials Form */}
        <form onSubmit={handleSubmit} className="space-y-4" autoComplete="off">
          {/* Hidden dummy inputs to block aggressive browser autofill */}
          <input type="text" name="prevent_autofill_user" id="prevent_autofill_user" style={{ display: 'none' }} tabIndex="-1" autoComplete="off" />
          <input type="password" name="prevent_autofill_pass" id="prevent_autofill_pass" style={{ display: 'none' }} tabIndex="-1" autoComplete="new-password" />

          <div className="space-y-1">
            <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider pl-1">Email Address</label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3.5 text-slate-400 flex items-center pointer-events-none">
                <User className="h-4 w-4" />
              </span>
              <input
                type="text"
                name="qits_login_email"
                id="qits_login_email"
                autoComplete="off"
                value={username}
                onChange={e => setUsername(e.target.value)}
                placeholder="Email"
                className="w-full pl-10 pr-4 py-3 border border-slate-200 bg-white rounded-2xl text-xs text-slate-800 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 transition-all font-medium shadow-sm"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider pl-1">Password</label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3.5 flex text-slate-400 items-center pointer-events-none">
                <Lock className="h-4 w-4" />
              </span>
              <input
                type={showPassword ? 'text' : 'password'}
                name="qits_login_password"
                id="qits_login_password"
                autoComplete="new-password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="Password"
                className="w-full pl-10 pr-10 py-3 border border-slate-200 bg-white rounded-2xl text-xs text-slate-800 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 transition-all font-medium shadow-sm"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoggingIn}
            className={`w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-xs rounded-2xl shadow-lg shadow-blue-500/25 flex items-center justify-center gap-1.5 transition-all mt-6 ${isLoggingIn ? 'opacity-80 scale-[0.98]' : 'active:scale-95'
              }`}
          >
            {isLoggingIn ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Signing in...</span>
              </>
            ) : (
              <>
                <LogIn className="h-4 w-4" />
                <span>Sign In</span>
              </>
            )}
          </button>
        </form>

      </div>
    </div>
  );
};

export default Login;
