// src/api/upload.ts

// --- THIS IS THE FIX ---
// 1. Define the API_URL from environment variables
const API_URL = import.meta.env.VITE_API_BASE_URL || '';
// --- END OF FIX ---

/**
 * Uploads a single Job Description file to the backend.
 * @param file The JD file to upload.
 * @returns The parsed JD data from the backend.
 */
export const uploadJdFile = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);

  // 2. Prepend API_URL and remove '/api'
  const response = await fetch(`${API_URL}/upload/jd`, {
    method: 'POST',
    body: formData,
    credentials: 'include', // 3. Keep credentials: 'include'
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to upload JD');
  }

  return response.json();
};

/**
 * Uploads multiple resume files for a specific JD.
 *
 * This function sends the `jdId` in the form data, aligning it
 * with the backend's `/upload/resumes` endpoint.
 *
 * @param files The list of resume files to upload.
 * @param jdId The ID of the job description to associate the resumes with.
 * @returns The result of the upload process from the backend.
 */
export const uploadResumeFiles = async (files: FileList, jdId: string): Promise<{ success: boolean; message: string }> => {
  const formData = new FormData();
  
  formData.append('jd_id', jdId);

  // Append all selected files to the form data under the 'files' key
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }

  // 2. Prepend API_URL and remove '/api'
  const response = await fetch(`${API_URL}/upload/resumes`, {
    method: 'POST',
    body: formData,
    credentials: 'include', // 3. Keep credentials: 'include'
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to upload resumes.');
  }

  return response.json();
};