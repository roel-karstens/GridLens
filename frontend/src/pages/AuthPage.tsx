import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { supabase } from '../lib/supabase';

interface AuthPageProps {
  onAuthSuccess: (user: { id: string; email: string }) => void;
}

interface AuthFormInputs {
  email: string;
  password: string;
}

const DEV_MODE = import.meta.env.MODE === 'development';
const DEV_USER_ID = '5b4b4ba2-ad71-44c8-8e6a-fee9313eee5c';
const DEV_USER_EMAIL = 'dev@example.com';

export function AuthPage({ onAuthSuccess }: AuthPageProps) {
  const { register, handleSubmit, formState: { errors } } = useForm<AuthFormInputs>({
    defaultValues: {
      email: '',
      password: '',
    },
  });
  const [isSignUp, setIsSignUp] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleDevLogin = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const testToken = 'dev-test-token-' + DEV_USER_ID;
      localStorage.setItem('sb-dev-token', testToken);
      
      onAuthSuccess({
        id: DEV_USER_ID,
        email: DEV_USER_EMAIL,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Dev login failed');
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (data: AuthFormInputs) => {
    setError(null);
    setLoading(true);

    try {
      const result = isSignUp
        ? await supabase.auth.signUp({ email: data.email, password: data.password })
        : await supabase.auth.signInWithPassword({ email: data.email, password: data.password });

      if (result.error) {
        setError(result.error.message);
      } else if (result.data.user) {
        if (isSignUp && !result.data.session) {
          setError('Email verification required. Please check your email inbox to confirm your account.');
          setIsSignUp(false);
        } else {
          onAuthSuccess({
            id: result.data.user.id,
            email: result.data.user.email || '',
          });
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-background px-4">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-foreground">
            {isSignUp ? 'Create Account' : 'Sign In'}
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Manage your projects with ease
          </p>
        </div>

        {DEV_MODE && (
          <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4">
            <p className="text-sm text-yellow-800">
              <strong>🚀 Development Mode:</strong> Use the button below to test without Supabase auth
            </p>
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 card">
          <div>
            <label htmlFor="email" className="label">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              placeholder="you@example.com"
              className="input"
              disabled={loading}
              {...register('email', {
                required: 'Email is required',
                pattern: {
                  value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                  message: 'Please enter a valid email',
                },
              })}
            />
            {errors.email && <span className="error">{errors.email.message}</span>}
          </div>

          <div>
            <label htmlFor="password" className="label">
              Password
            </label>
            <input
              id="password"
              type="password"
              placeholder="••••••••"
              className="input"
              disabled={loading}
              {...register('password', {
                required: 'Password is required',
                minLength: {
                  value: 6,
                  message: 'Password must be at least 6 characters',
                },
              })}
            />
            {errors.password && <span className="error">{errors.password.message}</span>}
          </div>

          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full"
          >
            {loading ? 'Loading...' : isSignUp ? 'Create Account' : 'Sign In'}
          </button>
        </form>

        {DEV_MODE && (
          <button
            type="button"
            onClick={handleDevLogin}
            disabled={loading}
            className="w-full px-4 py-2 bg-violet-600 text-white rounded-md hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium"
          >
            {loading ? 'Loading...' : '🚀 Dev Login (Skip Auth)'}
          </button>
        )}

        <div className="text-center">
          <p className="text-sm text-muted-foreground">
            {isSignUp ? 'Already have an account?' : "Don't have an account?"}
            {' '}
            <button
              type="button"
              onClick={() => {
                setIsSignUp(!isSignUp);
                setError(null);
              }}
              disabled={loading}
              className="font-semibold text-primary hover:underline disabled:opacity-50"
            >
              {isSignUp ? 'Sign In' : 'Sign Up'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
