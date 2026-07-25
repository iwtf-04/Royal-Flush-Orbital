export async function parseApiResponse<T = unknown>(response: Response): Promise<T> {
  const text = await response.text();

  if (!text) {
    return {} as T;
  }

  try {
    return JSON.parse(text) as T;
  } catch {
    throw new Error(text.length > 200 ? `${text.slice(0, 200)}...` : text);
  }
}
