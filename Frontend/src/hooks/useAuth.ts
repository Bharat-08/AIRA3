import { useState, useEffect } from 'react';
import type { User } from '../types/user';

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        //
        // --- THIS IS THE FIX ---
        // You MUST add `credentials: 'include'` so the browser
        // sends the session cookie to the /api/me endpoint.
        //
        const response = await fetch('/api/me', {
          credentials: 'include', // <-- ADD THIS LINE
        });
        // --- END OF FIX ---

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