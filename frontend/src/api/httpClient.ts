/**
 * HTTP client with timeout and error handling
 */

export interface HttpError {
  message: string;
  status?: number;
  isNetworkError: boolean;
}

export async function postJSON<T>(
  url: string,
  data: any,
  timeoutMs: number = 10000
): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const error: HttpError = {
        message: `HTTP ${response.status}: ${response.statusText}`,
        status: response.status,
        isNetworkError: response.status >= 500,
      };
      throw error;
    }

    return await response.json();
  } catch (err: any) {
    clearTimeout(timeoutId);

    // Handle abort (timeout)
    if (err.name === 'AbortError') {
      const error: HttpError = {
        message: 'Request timeout',
        isNetworkError: true,
      };
      throw error;
    }

    // Handle network errors
    if (err.message?.includes('fetch') || err.message?.includes('network')) {
      const error: HttpError = {
        message: 'Network error',
        isNetworkError: true,
      };
      throw error;
    }

    // Re-throw if already formatted
    if (err.isNetworkError !== undefined) {
      throw err;
    }

    // Generic error
    const error: HttpError = {
      message: err.message || 'Unknown error',
      isNetworkError: true,
    };
    throw error;
  }
}
