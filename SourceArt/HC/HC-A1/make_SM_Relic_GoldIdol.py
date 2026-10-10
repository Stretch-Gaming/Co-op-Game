"""SM_Relic_GoldIdol: the sitting gold lion idol from concepts/gold-idol-25cm.png, about 25 cm tall,
with a round jade gem on its chest. Built from carved blocks (head, mane, body, paws) with wide
bevels, like the concept's carved look. Faces -Y.

    blender -b --factory-startup --python SourceArt/HC/HC-A1/make_SM_Relic_GoldIdol.py -- /tmp/HC-A1
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import relic_parts as rp  # noqa: E402
from relic_parts import ball, block, cylinder, kit, pair, ring, tube  # noqa: E402

NAME = "SM_Relic_GoldIdol"

kit.reset()
gold, jade = rp.relic_materials()
parts = []

# Body: one big chunky barrel that the legs and haunches grow out of, with a shield-shaped chest
# plate holding the gem.
parts.append(block("Torso", (0.15, 0.13, 0.14), (0, 0.01, 0.085), taper=(0.8, 0.8), bevel=0.36, seed=1, mat=gold))
parts.append(block("ChestPlate", (0.068, 0.032, 0.1), (0, -0.064, 0.1), rot=(-6, 0, 0), taper=(1.3, 1.0),
                   bevel=0.26, seed=2, mat=gold))
parts.append(ring("GemRim", 0.027, 0.0065, (0, -0.082, 0.115), rot=(96, 0, 0), mat=gold))
parts.append(ball("Gem", 0.024, (0, -0.082, 0.115), scale=(1, 0.72, 1), rot=(-6, 0, 0), segments=20, rings=12,
                  mat=jade))

# Shoulders, front legs and front paws with three chunky toes.
parts += pair(cylinder("Shoulder", 0.04, 0.03, (0.07, -0.015, 0.115), rot=(0, 90, 0), bevel=0.26, mat=gold))
parts += pair(block("FrontLeg", (0.045, 0.048, 0.09), (0.047, -0.054, 0.06), rot=(-8, 0, 3), bevel=0.24, seed=3,
                    mat=gold))
parts += pair(block("FrontPaw", (0.058, 0.048, 0.032), (0.048, -0.07, 0.017), bevel=0.26, seed=4, mat=gold))
for i, dx in enumerate((-0.018, 0.0, 0.018)):
    parts += pair(block(f"FrontToe{i}", (0.023, 0.034, 0.031), (0.048 + dx, -0.09, 0.0155), bevel=0.26, seed=10 + i,
                        mat=gold))

# Big round haunches and back paws.
parts += pair(block("Haunch", (0.06, 0.105, 0.095), (0.072, 0.028, 0.052), rot=(0, 0, -4), bevel=0.46, seed=5,
                    mat=gold))
parts += pair(block("BackPaw", (0.04, 0.055, 0.025), (0.09, -0.028, 0.013), rot=(0, 0, -8), bevel=0.26, seed=6,
                    mat=gold))
for i, dx in enumerate((-0.013, 0.0, 0.013)):
    parts += pair(block(f"BackToe{i}", (0.016, 0.026, 0.024), (0.094 + dx, -0.056 + 0.0015 * i, 0.013),
                        rot=(0, 0, -8), bevel=0.26, seed=20 + i, mat=gold))

# Head, sitting low on the body: an angry brow, puffy cheeks, a broad muzzle, a jaw with two
# fangs, and thick round ears.
parts.append(block("Head", (0.125, 0.095, 0.092), (0, -0.04, 0.192), taper=(0.92, 0.95), bevel=0.24, seed=7, mat=gold))
parts += pair(block("Brow", (0.062, 0.03, 0.028), (0.027, -0.086, 0.218), rot=(0, -14, -6), bevel=0.26, seed=8,
                    mat=gold))
parts += pair(ball("Eye", 0.012, (0.029, -0.088, 0.199), scale=(1.35, 0.6, 0.8), mat=gold))
parts += pair(block("Cheek", (0.038, 0.042, 0.04), (0.05, -0.093, 0.168), bevel=0.26, seed=17, mat=gold))
parts.append(block("Muzzle", (0.088, 0.048, 0.044), (0, -0.102, 0.173), taper=(0.92, 0.9), bevel=0.26, seed=9, mat=gold))
parts.append(block("Nose", (0.042, 0.022, 0.024), (0, -0.122, 0.19), taper=(1.15, 0.8), bevel=0.26, seed=11, mat=gold))
parts.append(block("Jaw", (0.08, 0.052, 0.03), (0, -0.097, 0.141), bevel=0.24, seed=12, mat=gold))
parts += pair(block("Fang", (0.014, 0.012, 0.018), (0.027, -0.12, 0.158), taper=(0.7, 0.8), bevel=0.24, seed=13,
                    mat=gold))
parts += pair(ring("Ear", 0.014, 0.009, (0.062, 0.0, 0.236), rot=(80, 0, -10), major_segments=16, mat=gold))

# Mane: a big rounded hood behind the head and over the neck, a crest over the top and a
# ridge down the back.
parts.append(block("ManeHood", (0.15, 0.105, 0.12), (0, 0.012, 0.19), rot=(8, 0, 0), taper=(0.82, 0.8), bevel=0.34,
                   seed=14, mat=gold))
parts.append(block("ManeCrest", (0.066, 0.135, 0.036), (0, -0.012, 0.237), rot=(-8, 0, 0), taper=(0.85, 0.9),
                   bevel=0.26, seed=15, mat=gold))

parts.append(block("ManeRidge", (0.042, 0.03, 0.1), (0, 0.06, 0.155), rot=(16, 0, 0), taper=(1.25, 1.0), bevel=0.4,
                   seed=18, mat=gold))

# A tail curled round the right haunch.
parts.append(tube("Tail", [(0.04, 0.07, 0.012), (0.085, 0.09, 0.014), (0.115, 0.065, 0.024), (0.118, 0.03, 0.036)],
                  0.011, mat=gold))
parts.append(ball("TailTip", 0.0145, (0.118, 0.029, 0.038), scale=(1, 1.2, 1), mat=gold))

idol = rp.finish(parts, NAME, height=0.25)
rp.deliver(idol, NAME, rp.out_dir())
