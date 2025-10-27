// src/api/pipeline.ts
import type { PipelineCandidate } from '../types/candidate';

const mockCandidates: PipelineCandidate[] = [
  {
    id: '1',
    name: 'Sophia Rodriguez',
    role: 'Software Engineer',
    company: 'TechCorp',
    status: 'Favourited',
    stage: 'In Consideration',
  },
  {
    id: '2',
    name: 'Liam Thompson',
    role: 'Product Manager',
    company: 'Innovate Solutions',
    status: 'Contacted',
    stage: 'Offer Extended',
  },
  {
    id: '3',
    name: 'Ava Carter',
    role: 'Data Scientist',
    company: 'DataMinds Inc.',
    status: 'Favourited',
    stage: 'Rejected',
  },
  {
    id: '4',
    name: 'Noah Bennett',
    role: 'UX Designer',
    company: 'Creative Studio',
    status: 'Contacted',
    stage: 'Interviewing',
  },
  {
    id: '5',
    name: 'Emma Garcia',
    role: 'Frontend Developer',
    company: 'WebWeavers',
    status: 'Favourited',
    stage: 'In Consideration',
  },
  {
    id: '6',
    name: 'Oliver Martinez',
    role: 'Backend Engineer',
    company: 'ServerWorks',
    status: 'Contacted',
    stage: 'Interviewing',
  },
  {
    id: '7',
    name: 'Isabella Robinson',
    role: 'DevOps Engineer',
    company: 'Cloud Nine',
    status: 'Contacted',
    stage: 'Rejected',
  },
  {
    id: '8',
    name: 'James Clark',
    role: 'Project Manager',
    company: 'Innovate Solutions',
    status: 'Favourited',
    stage: 'Offer Extended',
  },
  {
    id: '9',
    name: 'Charlotte Lewis',
    role: 'QA Engineer',
    company: 'TechCorp',
    status: 'Contacted',
    stage: 'In Consideration',
  },
  {
    id: '10',
    name: 'Benjamin Walker',
    role: 'Full Stack Developer',
    company: 'CodeCrafters',
    status: 'Favourited',
    stage: 'Interviewing',
  },
  {
    id: '11',
    name: 'Mia Hall',
    role: 'UI Designer',
    company: 'Creative Studio',
    status: 'Contacted',
    stage: 'In Consideration',
  },
  {
    id: '12',
    name: 'Lucas Allen',
    role: 'Data Analyst',
    company: 'DataMinds Inc.',
    status: 'Favourited',
    stage: 'Hired',
  },
];

// If you were to fetch this from the API, the function would look like this:
/*
const API_URL = import.meta.env.VITE_API_BASE_URL || '';

// Note: This function is also named correctly, but is commented out
// because your file currently only uses mock data.
export const getPipelineCandidates = async (roleId: string): Promise<PipelineCandidate[]> => {
  // This is an example endpoint, please change it to your actual API endpoint
  const response = await fetch(`${API_URL}/roles/${roleId}/pipeline`, {
    method: 'GET',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch pipeline candidates');
  }
  return response.json();
};
*/

// --- THIS IS THE FIX ---
// I have renamed 'getMockPipelineCandidates' to 'getPipelineCandidates'
// to match what your PipelinePage.tsx is trying to import.
export const getPipelineCandidates = (): PipelineCandidate[] => {
  return mockCandidates;
};
// --- END OF FIX ---