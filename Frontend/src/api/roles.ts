// src/api/roles.ts
import type { Role, RoleStatus } from '../types/role';

// --- THIS IS THE FIX ---
// 1. Define the API_URL from environment variables
const API_URL = import.meta.env.VITE_API_BASE_URL || '';
// --- END OF FIX ---

export interface JdSummary {
  jd_id: string;
  title: string;
  role?: string | null;
  location?: string | null;
  job_type?: string | null;
  experience_required?: string | null;
  jd_parsed_summary?: string | null;

  // --- NEW FIELD: Full text content from backend ---
  jd_text?: string | null;

  created_at: string;
  updated_at: string;
  // backend may return key_requirements as a comma string or as an array
  key_requirements?: string | string[] | null;
  status?: RoleStatus;
  // optional candidate stats (may or may not be present)
  candidate_stats?: {
    liked?: number;
    contacted?: number;
  } | null;
}

/**
 * Helper: try to parse backend's key_requirements into string[]
 */
const parseKeyRequirements = (value?: string | string[] | null): string[] => {
  if (!value) return [];
  if (Array.isArray(value)) {
    return value.map(String);
  }
  // If it's a string, split by common separators (comma or semicolon)
  return value
    .split(/[,;]+/)
    .map(s => s.trim())
    .filter(Boolean);
};

/**
 * Helper: Maps the raw backend JdSummary DTO to the cleaner frontend Role type.
 */
const mapJdSummaryToRole = (jd: JdSummary): Role => ({
  id: jd.jd_id,
  title: jd.role || jd.title || 'Untitled Role',
  location: jd.location || 'N/A',
  created_at: jd.created_at,
  updated_at: jd.updated_at,
  // --- MAPPING CHANGE: jd_parsed_summary -> summary ---
  summary: jd.jd_parsed_summary || 'No summary available.',
  // --- NEW MAPPING: jd_text -> full_content ---
  full_content: jd.jd_text || '',

  experience: jd.experience_required || 'N/A',
  // --- MAPPING CHANGE: key_requirements (plural) ---
  key_requirements: parseKeyRequirements(jd.key_requirements),

  candidateStats: {
    liked: jd.candidate_stats?.liked ?? 0,
    contacted: jd.candidate_stats?.contacted ?? 0,
  },
  status: jd.status ?? 'open',
});

/**
 * Fetches real job descriptions uploaded by the current user using cookie authentication.
 * Returns raw backend DTO (JdSummary[]).
 */
export const fetchJdsForUser = async (sort?: string, filter?: string): Promise<JdSummary[]> => {
  // --- START: CORRECTED CODE ---
  // 2. Prepend API_URL and remove '/api'
  let url = `${API_URL}/roles/`; 
  const params = new URLSearchParams();
  if (sort) params.append('sort', sort);
  if (filter) params.append('filter', filter);

  const queryString = params.toString();
  if (queryString) {
    url += `?${queryString}`;
  }
  // --- END: CORRECTED CODE ---

  const res = await fetch(url, { // Use the manually built url string
    credentials: 'include', // 3. Keep credentials: 'include'
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to fetch roles (${res.status})`);
  }

  const data = await res.json();
  // Expecting an array; defensive fallback
  if (!Array.isArray(data)) {
    throw new Error('Unexpected response format from roles endpoint');
  }
  return data as JdSummary[];
};

/**
 * Creates a new role by uploading a Job Description file using cookie authentication.
 * Returns a Role (transformed).
 */
export const createRole = async (file: File): Promise<Role> => {
  const fd = new FormData();
  fd.append('file', file);

  // 2. Prepend API_URL and remove '/api'
  const res = await fetch(`${API_URL}/roles/`, {
    method: 'POST',
    credentials: 'include', // 3. Keep credentials: 'include'
    body: fd,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to create role (${res.status})`);
  }

  const created: JdSummary = await res.json();

  return mapJdSummaryToRole(created);
};

/**
 * Wrapper: getRoles() - returns transformed Role[] for frontend consumption.
 */
export const getRoles = async (sort?: string, filter?: string): Promise<Role[]> => {
  const jds = await fetchJdsForUser(sort, filter);
  return jds.map(mapJdSummaryToRole);
};

/**
 * Updates the status of a specific role.
 * - Sends a PATCH request and returns the transformed Role.
 */
export const updateRoleStatus = async (roleId: string, status: RoleStatus): Promise<Role> => {
  // 2. Prepend API_URL and remove '/api'
  const res = await fetch(`${API_URL}/roles/${encodeURIComponent(roleId)}/status`, {
    method: 'PATCH',
    credentials: 'include', // 3. Keep credentials: 'include'
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ status }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to update role status (${res.status})`);
  }

  const updated: JdSummary = await res.json();

  return mapJdSummaryToRole(updated);
};

// --- NEW FUNCTION: To update the editable JD content ---
export const editRoleContent = async (roleId: string, newContent: string): Promise<Role> => {
    // 2. Prepend API_URL and remove '/api'
    const res = await fetch(`${API_URL}/roles/${encodeURIComponent(roleId)}`, {
        method: 'PATCH',
        credentials: 'include', // 3. Keep credentials: 'include'
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ jd_text: newContent }),
    });

    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Failed to update role content (${res.status})`);
    }

    const updated: JdSummary = await res.json();
    // The backend PATCH endpoint returns the updated JdSummary, so we map it to Role
    return mapJdSummaryToRole(updated);
};

// --- NEW FUNCTION: To delete a role ---
export const deleteRole = async (roleId: string): Promise<void> => {
    // 2. Prepend API_URL and remove '/api'
    const res = await fetch(`${API_URL}/roles/${encodeURIComponent(roleId)}`, {
        method: 'DELETE',
        credentials: 'include', // 3. Keep credentials: 'include'
    });

    if (!res.ok && res.status !== 204) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Failed to delete role (${res.status})`);
    }
};


// Export for other modules if needed
export default {
  fetchJdsForUser,
  createRole,
  getRoles,
  updateRoleStatus,
  editRoleContent, // --- EXPORTED NEW FUNCTION ---
  deleteRole, // --- EXPORTED NEW FUNCTION ---
};