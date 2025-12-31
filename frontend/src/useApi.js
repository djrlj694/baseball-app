import { useState } from "react";

export function useApi(fetcher) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const call = async (...args) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetcher(...args);
      setLoading(false);
      return result;
    } catch (err) {
      setError(err.message || "Unknown error");
      setLoading(false);
      throw err;
    }
  };

  return { call, loading, error };
}
