import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "../api/client";

export const FAVORITES_QUERY_KEY = ["favorites"] as const;

export function useFavorites() {
  const queryClient = useQueryClient();

  const favoritesQuery = useQuery({
    queryKey: FAVORITES_QUERY_KEY,
    queryFn: () => apiClient.getFavorites(),
  });

  const invalidateFavorites = async () => {
    await queryClient.invalidateQueries({ queryKey: FAVORITES_QUERY_KEY });
  };

  const addFavorite = useMutation({
    mutationFn: (trackId: string) => apiClient.addFavorite(trackId),
    onSettled: invalidateFavorites,
  });

  const removeFavorite = useMutation({
    mutationFn: (trackId: string) => apiClient.removeFavorite(trackId),
    onSettled: invalidateFavorites,
  });

  const favoritedTrackIds = new Set(
    favoritesQuery.data?.items?.map((item) => item.track_id) ?? [],
  );

  const toggleFavorite = (trackId: string) => {
    if (favoritedTrackIds.has(trackId)) {
      removeFavorite.mutate(trackId);
      return;
    }
    addFavorite.mutate(trackId);
  };

  const isToggling = (trackId: string) =>
    (addFavorite.isPending && addFavorite.variables === trackId) ||
    (removeFavorite.isPending && removeFavorite.variables === trackId);

  return {
    favorites: favoritesQuery.data?.items ?? [],
    favoritedTrackIds,
    isLoading: favoritesQuery.isLoading,
    isError: favoritesQuery.isError,
    toggleFavorite,
    isToggling,
  };
}
