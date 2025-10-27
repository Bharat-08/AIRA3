import { useState, useEffect } from 'react';
import type { User } from '../types/user';

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // --- THIS IS THE MISSING LINE ---
  // This reads the VITE_API_BASE_URL environment variable.
  // In production (OnRender), this will be 'https://aira3.onrender.com'
  // In local dev, it will be '/api' (from your .env.development file)
  const API_URL = import.meta.env.VITE_API_BASE_URL || '';
  // --- END OF FIX ---

  useEffect(() => {
    const fetchUser = async () => {
      try {
        //
        // This path is now correct for both environments:
        // Prod: 'https://aira3.onrender.com/me'
        // Dev:  '/api/me' (which your vite.config.ts proxy will handle)
        //
        const response = await fetch(`${API_URL}/me`, {
          credentials: 'include', 
        });

        if (!response.ok) {
          // This is normal if the user is not logged in
          if (response.status === 401) {
            console.log('User not authenticated');
            return; 
          }
          throw new Error('Failed to fetch user');
        }

        const userData: User = await response.json();
        setUser(userData);
      } catch (error) {
        console.error("Failed to fetch user:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchUser();
  }, []);

  return { user, isLoading };
};