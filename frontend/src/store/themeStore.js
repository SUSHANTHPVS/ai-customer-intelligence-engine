import { create } from 'zustand';

const applyTheme = (dark) => {
  const root = document.documentElement;
  if (dark) {
    root.classList.add('dark');
  } else {
    root.classList.remove('dark');
  }
};

const storedPreference = localStorage.getItem('dark_mode') === 'true';
applyTheme(storedPreference);

export const useThemeStore = create((set, get) => ({
  darkMode: storedPreference,

  toggleDarkMode: () => {
    const next = !get().darkMode;
    localStorage.setItem('dark_mode', String(next));
    applyTheme(next);
    set({ darkMode: next });
  },
}));

export default useThemeStore;
