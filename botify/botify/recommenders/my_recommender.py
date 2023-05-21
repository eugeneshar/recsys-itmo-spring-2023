from collections import defaultdict

from .random import Random
from .recommender import Recommender
import random

from .toppop import TopPop


class MyRecommender(Recommender):
    """
    Recommend tracks closest to the previous one.
    Fall back to the random recommender if no
    recommendations found for the track.
    """

    def __init__(self, tracks_redis, catalog):
        self.tracks_redis = tracks_redis
        self.toppop = TopPop(tracks_redis, catalog.top_tracks[:100])
        self.fallback = Random(tracks_redis)
        self.catalog = catalog
        self.user_favourite = defaultdict(set)

    def recommend_next(self, user: int, prev_track: int, prev_track_time: float) -> int:
        if prev_track_time > 0.8:  # Liked the track, keep the same path
            self.user_favourite[user].add(prev_track)
        if prev_track_time < 0.2:  # Didn't like the track, return to better path
            if user in self.user_favourite:
                return self.recommend_next(user, random.choice(list(self.user_favourite[user])), 0.8)
            return self.toppop.recommend_next(user, prev_track, prev_track_time)
        previous_track = self.tracks_redis.get(prev_track)
        if previous_track is None:
            return self.fallback.recommend_next(user, prev_track, prev_track_time)
        previous_track = self.catalog.from_bytes(previous_track)  # Get recommendations by Context Recommender
        recommendations = previous_track.recommendations
        if not recommendations:
            return self.fallback.recommend_next(user, prev_track, prev_track_time)

        shuffled = list(recommendations)
        random.shuffle(shuffled)

        return shuffled[0]

