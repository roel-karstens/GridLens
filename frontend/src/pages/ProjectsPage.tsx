import { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { supabase } from '../lib/supabase';
import { api } from '../lib/api';
import { Project } from '../types';
import { ProjectForm } from '../components/ProjectForm';
import { ProjectList } from '../components/ProjectList';

interface ProjectsPageProps {
  user: { id: string; email: string };
  onLogout: () => void;
}

const DEV_MODE = import.meta.env.MODE === 'development';

export function ProjectsPage({ user, onLogout }: ProjectsPageProps) {
  const [token, setToken] = useState<string | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  useEffect(() => {
    const getInitialSession = async () => {
      try {
        if (DEV_MODE && localStorage.getItem('sb-dev-token')) {
          console.log('📝 Dev mode: requesting test token from backend...');
          
          // Add a timeout for the fetch
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 5000);
          
          try {
            const response = await fetch('http://localhost:8000/api/v1/dev/token', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ user_id: user.id }),
              signal: controller.signal,
            });
            
            clearTimeout(timeoutId);
            
            if (response.ok) {
              const data = await response.json();
              console.log('✅ Dev token retrieved:', data.token.substring(0, 20) + '...');
              setToken(data.token);
              setAuthError(null);
            } else {
              const errorText = await response.text();
              console.error('Failed to get dev token:', response.status, errorText);
              setAuthError(`Backend error: ${response.status}`);
              // Fallback: create a temporary token for testing
              const tempToken = 'dev-temp-' + Date.now();
              setToken(tempToken);
            }
          } catch (fetchErr) {
            clearTimeout(timeoutId);
            if (fetchErr instanceof Error && fetchErr.name === 'AbortError') {
              console.error('Dev token request timed out');
              setAuthError('Backend request timed out. Is the backend running on port 8000?');
            } else {
              console.error('Error fetching dev token:', fetchErr);
              setAuthError(`Failed to connect to backend: ${fetchErr instanceof Error ? fetchErr.message : 'Unknown error'}`);
            }
            // Fallback: create a temporary token for testing
            const tempToken = 'dev-temp-' + Date.now();
            setToken(tempToken);
          }
        } else {
          const { data: { session } } = await supabase.auth.getSession();
          if (session?.access_token) {
            console.log('✅ Token retrieved from Supabase (initial):', session.access_token.substring(0, 20) + '...');
            setToken(session.access_token);
            setAuthError(null);
          } else {
            console.log('📝 No initial session, listening for auth changes...');
            const { data: authListener } = supabase.auth.onAuthStateChange(
              async (_event, session) => {
                if (session?.access_token) {
                  console.log('✅ Token retrieved from Supabase:', session.access_token.substring(0, 20) + '...');
                  setToken(session.access_token);
                  setAuthError(null);
                }
              }
            );
            
            return () => {
              authListener?.subscription.unsubscribe();
            };
          }
        }
      } catch (err) {
        console.error('Error getting token:', err);
        setAuthError(err instanceof Error ? err.message : 'Authentication error');
      }
    };

    getInitialSession();
  }, [user.id]);

  const { data: projects = [], isLoading, error } = useQuery<Project[], Error>(
    ['projects', token],
    () => token ? api.get<Project[]>('/api/v1/projects', token) : Promise.resolve([]),
    {
      enabled: !!token,
      staleTime: 5 * 60 * 1000, // 5 minutes
    }
  );

  const createMutation = useMutation(
    (vars: { name: string; description: string }) =>
      token ? api.post<Project>('/api/v1/projects', vars, token) : Promise.reject(new Error('Not authenticated')),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['projects', token]);
      },
    }
  );

  const deleteMutation = useMutation(
    (id: string) =>
      token ? api.delete(`/api/v1/projects/${id}`, token) : Promise.reject(new Error('Not authenticated')),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['projects', token]);
      },
    }
  );

  const handleCreateProject = async (name: string, description: string) => {
    try {
      await createMutation.mutateAsync({ name, description });
    } catch (err) {
      console.error('Error creating project:', err);
    }
  };

  const handleDeleteProject = async (id: string) => {
    try {
      await deleteMutation.mutateAsync(id);
    } catch (err) {
      console.error('Error deleting project:', err);
    }
  };

  const handleLogout = async () => {
    if (DEV_MODE) {
      localStorage.removeItem('sb-dev-token');
    } else {
      await supabase.auth.signOut();
    }
    onLogout();
  };

  if (!token) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="text-center">
          <div className="text-lg text-slate-600 mb-4">Authenticating...</div>
          {authError && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 max-w-sm mx-auto">
              <p className="text-sm text-red-800 mb-2">{authError}</p>
              <p className="text-xs text-red-700">Make sure the backend is running: <code className="bg-red-100 px-1 py-0.5 rounded">python -m uvicorn app.main:app</code></p>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <header className="border-b border-slate-200 bg-white/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Projects</h1>
              <p className="text-sm text-slate-600 mt-1">{user.email}</p>
              <p className="text-xs text-slate-500 mt-0.5 font-mono">ID: {user.id.substring(0, 8)}...</p>
            </div>
            <div className="flex items-center gap-3">
              {DEV_MODE && (
                <span className="text-xs bg-violet-100 text-violet-800 px-2 py-1 rounded-full">
                  🚀 Dev Mode
                </span>
              )}
              <button
                onClick={handleLogout}
                className="btn-secondary"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <ProjectForm
            onCreate={handleCreateProject}
            isLoading={createMutation.isLoading}
            error={createMutation.error ? (createMutation.error as Error).message : undefined}
          />
        </div>

        {authError && (
          <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4 mb-6">
            <p className="text-sm text-yellow-800 font-medium mb-2">⚠️ Authentication Warning</p>
            <p className="text-sm text-yellow-700">{authError}</p>
            <p className="text-xs text-yellow-700 mt-2">Dev Mode: Using temporary token for testing</p>
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 mb-6">
            <p className="text-sm text-red-800">
              {error instanceof Error ? error.message : 'An error occurred'}
            </p>
          </div>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-lg text-muted-foreground">Loading projects...</div>
          </div>
        ) : projects.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-lg text-muted-foreground">No projects yet.</div>
            <p className="text-sm text-muted-foreground">Create one above to get started!</p>
          </div>
        ) : (
          <ProjectList
            projects={projects}
            onDelete={handleDeleteProject}
            isDeleting={deleteMutation.isLoading}
          />
        )}
      </main>
    </div>
  );
}
