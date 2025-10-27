// src/api/search.ts
import type { Candidate } from '../types/candidate';

// --- THIS IS THE FIX ---
// 1. Define the API_URL from environment variables
const API_URL = import.meta.env.VITE_API_BASE_URL || '';
// --- END OF FIX ---

// --- TYPES for the new asynchronous API responses ---
interface TaskStartResponse {
  task_id: string;
  status: 'processing';
}

interface TaskStatusResponse {
  status: 'processing' | 'completed' | 'failed';
  data?: Candidate[];
  error?: string;
}

// --- MAIN SEARCH & RANK PIPELINE ---

/**
 * Starts the main search and rank pipeline on the backend.
 * @param jdId The ID of the job description.
 * @param prompt The user's search prompt.
 * @returns An object containing the task_id for the background job.
 */
export const startSearchAndRankTask = async (jdId: string, prompt: string): Promise<TaskStartResponse> => {
  // 2. Prepend API_URL and remove '/api'
  const response = await fetch(`${API_URL}/search/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ jd_id: jdId, prompt: prompt }),
    credentials: 'include', // 3. Keep credentials: 'include'
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to start search and rank task' }));
    throw new Error(errorData.detail || 'Failed to start search and rank task');
  }

  return response.json();
};

/**
 * Starts the Apollo-backed search (Fast or Web+Apollo) on the backend.
 * Calls the new endpoint: POST /search/apollo-search/{jd_id}
 *
 * @param jdId The ID of the job description.
 * @param prompt Optional prompt string (may be empty).
 * @param searchOption Numeric option:
 * 1 -> Fast search (Apollo-only)
 * 2 -> Web search + Apollo
 *
 * @returns TaskStartResponse with task_id
 */
export const startApolloSearchTask = async (jdId: string, prompt: string, searchOption: number): Promise<TaskStartResponse> => {
  // Validate option early to provide a clear client-side error
  if (![1, 2].includes(searchOption)) {
    throw new Error('searchOption must be 1 (Fast) or 2 (Web + Apollo)');
  }

  // 2. Prepend API_URL and remove '/api'
  const response = await fetch(`${API_URL}/search/apollo-search/${encodeURIComponent(jdId)}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include', // 3. Keep credentials: 'include'
    body: JSON.stringify({
      search_option: searchOption,
      prompt: prompt || ''
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to start Apollo search task' }));
    throw new Error(errorData.detail || 'Failed to start Apollo search task');
  }

  return response.json();
};

/**
 * Polls the backend for the result of the search and rank task.
 * @param taskId The ID of the background task.
 * @returns The current status of the task and the final data if completed.
 */
export const getSearchResults = async (taskId: string): Promise<TaskStatusResponse> => {
  // 2. Prepend API_URL and remove '/api'
  const response = await fetch(`${API_URL}/search/search/results/${taskId}`, {
    method: 'GET',
    credentials: 'include', // 3. Keep credentials: 'include'
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to get task results' }));
    throw new Error(errorData.detail || 'Failed to get task results');
  }

  return response.json();
};


// --- RESUME RANKING PIPELINE ---

/**
 * Starts the resume ranking process on the backend.
 * @param jdId The ID of the job description.
 * @param prompt A prompt (can be empty if not needed by this endpoint).
 * @returns An object containing the task_id for the background job.
 */
export const startRankResumesTask = async (jdId: string, prompt: string): Promise<TaskStartResponse> => {
  // 2. Prepend API_URL and remove '/api'
  const response = await fetch(`${API_URL}/search/rank-resumes`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ jd_id: jdId, prompt: prompt }),
    credentials: 'include', // 3. Keep credentials: 'include'
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to start resume ranking task' }));
    throw new Error(errorData.detail || 'Failed to start resume ranking task');
  }

  return response.json();
};

/**
 * Polls the backend for the result of the resume ranking task.
 * @param taskId The ID of the background task.
 * @returns The current status of the task and the final data if completed.
 */
export const getRankResumesResults = async (taskId: string): Promise<TaskStatusResponse> => {
  // 2. Prepend API_URL and remove '/api'
  const response = await fetch(`${API_URL}/search/rank-resumes/results/${taskId}`, {
    method: 'GET',
    credentials: 'include', // 3. Keep credentials: 'include'
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to get resume ranking results' }));
    throw new Error(errorData.detail || 'Failed to get resume ranking results');
  }

  return response.json();
};


// --- UTILITY FUNCTIONS (Cancellation and LinkedIn URL) ---

/**
 * Sends a request to the backend to stop a running Celery task.
 * @param taskId The ID of the task to cancel.
 */
export const stopTask = async (taskId: string): Promise<{ message: string }> => {
  // 2. Prepend API_URL and remove '/api'
  const response = await fetch(`${API_URL}/search/cancel/${taskId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include', // 3. Keep credentials: 'include'
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to stop the task' }));
    throw new Error(errorData.detail || 'Failed to stop the task');
  }

  return response.json();
};

/**
 * Calls the backend to generate a LinkedIn URL for a given candidate.
 * (This function's logic remains unchanged).
 * @param profileId The ID of the candidate's profile.
 * @returns An object containing the newly generated profile_url.
 */
export const generateLinkedInUrl = async (profileId: string): Promise<{ linkedin_url: string }> => {
  // 2. Prepend API_URL and remove '/api'
  const response = await fetch(`${API_URL}/search/generate-linkedin-url`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ profile_id: profileId }),
    credentials: 'include', // 3. Keep credentials: 'include'
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to generate LinkedIn URL' }));
    throw new Error(errorData.detail || 'Failed to generate LinkedIn URL');
  }

  return response.json();
};

// --- FIX: Removed the duplicate generateLinkedinUrl function ---
// The function above handles cookie-based auth, so the 
// one with the 'token' parameter was redundant and a syntax error.


/**
 * Toggle favorite status for a candidate.
 * @param candidateId The profile_id or resume_id of the candidate.
 * @param source Either "ranked_candidates" or "ranked_candidates_from_resume".
 * @param favorite The desired boolean favorite value.
 */
export const toggleFavorite = async (
  candidateId: string,
  source: 'ranked_candidates' | 'ranked_candidates_from_resume',
  favorite: boolean
): Promise<{ candidate_id: string; favorite: boolean }> => {
  // 2. Prepend API_URL and remove '/api'
  // Note: This endpoint is /favorites, not /search
  const response = await fetch(`${API_URL}/favorites/toggle`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include', // 3. Keep credentials: 'include'
    body: JSON.stringify({
      candidate_id: candidateId,
      source,
      favorite,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to toggle favorite' }));
    throw new Error(errorData.detail || 'Failed to toggle favorite');
  }

  return response.json();
};