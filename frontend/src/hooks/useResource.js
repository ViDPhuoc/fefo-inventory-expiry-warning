import { useEffect, useState } from "react";
// Bỏ phản hồi đã cũ khi bộ lọc đổi nhanh; không để kết quả cũ ghi đè kết quả mới.
export default function useResource(load, dependencies) {
  const [state, setState] = useState({ data: null, loading: true, error: "" });
  useEffect(() => {
    let active = true;
    setState((s) => ({ ...s, loading: true, error: "" }));
    Promise.resolve()
      .then(load)
      .then((data) => {
        if (active) setState({ data, loading: false, error: "" });
      })
      .catch((error) => {
        if (active)
          setState((s) => ({ ...s, loading: false, error: error.message }));
      });
    return () => {
      active = false;
    };
  }, dependencies);
  return state;
}
