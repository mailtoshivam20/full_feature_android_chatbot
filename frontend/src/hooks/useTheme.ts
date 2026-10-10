import { useUIStore } from "@/store/uiStore";

export function useTheme() {
  const { theme, setTheme } = useUIStore();

  const toggle = () => {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
  };

  return { theme, setTheme, toggle };
}
