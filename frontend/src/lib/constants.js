import { CarFront, CircleHelp, Construction, OctagonAlert, Waves } from 'lucide-react';

// Traffic levels from SRS section 4.3.2. `rank` drives the meter (1 to 4 bars).
export const LEVELS = {
  FREE_FLOW: { label: 'Free flow', rank: 1, text: 'Traffic is moving normally.' },
  MODERATE: { label: 'Moderate', rank: 2, text: 'Traffic is slower than normal.' },
  HEAVY: { label: 'Heavy', rank: 3, text: 'Significant congestion.' },
  BLOCKED: { label: 'Blocked', rank: 4, text: 'Traffic is effectively stopped.' },
};
export const LEVEL_ORDER = ['FREE_FLOW', 'MODERATE', 'HEAVY', 'BLOCKED'];

export const INCIDENT_TYPES = {
  CRASH: { label: 'Crash', icon: CarFront },
  FLOODING: { label: 'Flooding', icon: Waves },
  ROADWORKS: { label: 'Roadworks', icon: Construction },
  BLOCKAGE: { label: 'Blockage', icon: OctagonAlert },
  OTHER: { label: 'Other', icon: CircleHelp },
};

export const STATUSES = {
  SUBMITTED: 'Submitted',
  UNDER_REVIEW: 'Under review',
  VERIFIED: 'Verified',
  RESOLVED: 'Resolved',
  REJECTED: 'Rejected',
};

export const REFRESH_MS = 30000;
