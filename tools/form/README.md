# Form kit

How Stage 4 gets from the concept art to a model that looks like it, before any engineering. CLAUDE.md's Stage 4 steps 1 to 3 (design read, blockout, compare) use this. **Add to it every episode:** what worked, what failed and how long it took, so the next model starts ahead.

## The method: silhouettes first

Industrial designers block out a form from three orthographic views before anything else, and it works in any CAD tool, including one driven by script:

1. **Trace the silhouettes** from the layout sheet (or the concept art) into `DESIGN.md`: the side profile, the top plan and a front section, as point lists in a 0–1 box. Use enough points for the curves: 12 to 30 per curve, closer together where the curve is tight.
2. **Scale** them to the size the parts need (keep the ratios).
3. **Extrude the side profile** across the full width and **the top plan** through the full height, and **intersect** the two bodies. That gives the form's true side and top outlines at once, including asymmetry and a crown that peaks off-centre. Intersect a third body from the front section to round the cross-section.
4. **Soften** the edges the concept shows soft, with fillets where they work, or by lofting through cross-sections taken from the three views.
5. **Parting lines and colour splits**: split the body along the line the concept draws (a plane tilted to follow it, or a swept/extruded cut that follows the curve), and give each piece its colour.
6. **Signature details** as their own bodies: domed grilles (a sphere or a revolve cut back to the face), shaped light diffusers (an extruded outline, slightly proud), moulded switches and buttons (their real outline from the art, not a default circle or rectangle).

## Smooth curves

Curves drawn from a few straight `sketch.line` segments come out faceted and boxy. Every model so far (episodes 001 to 003) did that. Solidcraft's sketcher has splines, ellipses and conics (its v0.28.0 release notes mention snapping to them), so the shapes are there. Before the blockout, run `solidcraft-cli commands` (it prints every scriptable command) and record here which curve and form commands the script can use: spline, arc, ellipse or conic in sketches, sweep along a path, intersect/common in `solid.combine`, loft options, and variable-radius fillets. Then use them: draw silhouettes as splines through the traced points. Where there's no spline, use many short segments (every 1–2 mm along a curve) so the facets disappear in the render.

## What Solidcraft did (record new findings here)

| Episode | Tried | Result |
|---|---|---|
| 003 | `solid.loft` through 12 cross-sections for an asymmetric mouse-like body | Worked, slow-ish. The best route to the concept's shape so far. |
| 003 | Hollowing a loft with `solid.shell` | Failed: it can't offset freeform faces. A second, inset loft as the cavity worked. |
| 003 | Extruded plan, then a fillet over the crown | The fillet ran 5 min, then failed. |
| 003 | A curved (cylindrical) split for the two-colour swoosh | "Section does not close". A plane tilted front to back and side to side worked. |
| 003 | A spherical thumb dimple cut into the loft | Failed where the sphere met the split face. |
| 003 | Cuts through the lofted nose | About 3 min each; grouping them into one cut body is faster. |

## Compare

`python3 tools/form/compare.py episodes/<slug>` writes `4-model/compare.png`: the favourite concept art, the layout sheet and the latest blockout or iso screenshot side by side, scaled to the same height. Pass a screenshot to use another: `--shot 4-model/blockout-03.png`. For a revision: `python3 tools/form/compare.py products/<product>/rev-b` uses the previous hero render as the reference when there's no concept art in the folder.

Read it the way a designer would: squint, then check the silhouette, the proportions, where the visual weight sits, the parting line and colour split, then each detail. Score every signature feature in `DESIGN.md` (✓ / partly / ✗) and fix the worst first.
