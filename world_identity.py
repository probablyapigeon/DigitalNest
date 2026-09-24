"""Saved, deterministic visual genomes chosen from a builder's real state."""
import hashlib
import random


def visual_genome(instance, player, room, creator, traits=None, heart=None, motifs=()):
    traits, heart = traits or {}, heart or {}
    seed = int(hashlib.sha256(f'{instance}:{player}:{room}:{creator}'.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    hue = (rng.randrange(360) + int(traits.get('curiosity', 50))) % 360
    silhouette = rng.choice(['canopy', 'arches', 'spires', 'orbits'])
    if set(motifs).intersection({'garden', 'moss', 'flower', 'leaf'}):
        silhouette = 'canopy'
    elif set(motifs).intersection({'music', 'song', 'tune'}):
        silhouette = 'orbits'
    return dict(version=1, seed=seed, creator=creator, hue=hue,
                accent=(hue + rng.randint(35, 160)) % 360,
                silhouette=silhouette,
                pattern=rng.choice(['rings', 'tiles', 'rays']),
                density=rng.randint(6, 13), warmth=round(heart.get('light', .5), 3),
                motifs=list(motifs)[:4])
