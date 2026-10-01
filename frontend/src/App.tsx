import { useEffect, useState } from 'react';
import { supabase } from './lib/supabase';
import { AuthPage } from './pages/AuthPage';
import { DashboardPage } from './pages/DashboardPage';
import { HistoryPage } from './pages/HistoryPage';
import { ComparisonPage } from './pages/ComparisonPage';

interface User {
  id: string;
  email: string;
}

type Page = 'dashboard' | 'history' | 'comparison' | 'projects';

export function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState<Page>('dashboard');

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session?.user) {
        setUser({
          id: session.user.id,
          email: session.user.email || '',
        });
      }
      setLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session?.user) {
        setUser({
          id: session.user.id,
          email: session.user.email || '',
        });
      } else {
        setUser(null);
      }
    });

    return () => subscription?.unsubscribe();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <div className="text-lg text-gray-600">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return <AuthPage onAuthSuccess={(newUser) => setUser(newUser)} />;
  }

  const handleLogout = async () => {
    await supabase.auth.signOut();
    setUser(null);
  };

  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-800">GridLens</h1>
            
            <div className="flex items-center gap-6">
              <div className="flex gap-4">
                <button
                  onClick={() => setCurrentPage('dashboard')}
                  className={`px-4 py-2 rounded-lg font-semibold transition ${
                    currentPage === 'dashboard'
                      ? 'bg-blue-500 text-white'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  Dashboard
                </button>
                <button
                  onClick={() => setCurrentPage('history')}
                  className={`px-4 py-2 rounded-lg font-semibold transition ${
                    currentPage === 'history'
                      ? 'bg-blue-500 text-white'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  History
                </button>
                <button
                  onClick={() => setCurrentPage('comparison')}
                  className={`px-4 py-2 rounded-lg font-semibold transition ${
                    currentPage === 'comparison'
                      ? 'bg-blue-500 text-white'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  Comparison
                </button>
              </div>

              <div className="flex items-center gap-4 pl-4 border-l border-gray-300">
                <span className="text-sm text-gray-600">{user.email}</span>
                <button
                  onClick={handleLogout}
                  className="px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg font-semibold"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Page Content */}
      <main>
        {currentPage === 'dashboard' && <DashboardPage />}
        {currentPage === 'history' && <HistoryPage />}
        {currentPage === 'comparison' && <ComparisonPage />}
      </main>
    </div>
  );
}
