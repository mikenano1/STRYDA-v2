/**
 * App configuration
 * API_BASE is loaded from environment with fallback
 */

export const config = {
  API_BASE: process.env.API_BASE || 'https://api.stryda.local',
};
