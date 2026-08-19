# Assets

This MVP renders everything procedurally with Ursina primitives (cubes,
scaled/colored to represent props) so it runs immediately with zero
external asset dependencies.

To add real art/audio later:

- Drop `.glb`/`.obj` models here and reference them by filename in
  `config/settings.py` (`OBJECT_PERSONALITIES[...]["model"]`) instead of
  `"cube"`.
- Drop `.ogg`/`.wav` files here and hook them up at the call sites noted
  in the README's "Known limitations" section (transform, scanner,
  footsteps, attack, objective completion, elimination, round
  start/end).
