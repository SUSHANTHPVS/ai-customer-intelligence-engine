import { create } from 'zustand';
import { apiClient } from '../api/client';

export const useDatasetStore = create((set, get) => ({
  datasets: [],
  activeDatasetId: 'default',
  loading: false,

  refresh: async () => {
    set({ loading: true });
    try {
      const { data } = await apiClient.datasets.list();
      set({
        datasets: data.datasets || [],
        activeDatasetId: data.active_dataset_id || 'default',
        loading: false,
      });
    } catch (error) {
      set({ loading: false });
    }
  },

  getActiveDatasetName: () => {
    const active = get().datasets.find((d) => d.id === get().activeDatasetId);
    return active?.name || 'Demo Dataset';
  },
}));

export default useDatasetStore;
