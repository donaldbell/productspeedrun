# Form kit

How Stage 4 gets from the concept art to a model that looks like it, before any engineering. CLAUDE.md's Stage 4 steps 1 to 3 (design read, blockout, compare) use this. **Add to it every episode:** what worked, what failed and how long it took, so the next model starts ahead.

## The method: silhouettes first

Industrial designers block out a form from three orthographic views before anything else, and it works in any CAD tool, including one driven by script:

1. **Trace the silhouettes** from the control drawing (or the concept art) into `DESIGN.md`: the side profile, the top plan and a front section, as point lists in a 0–1 box. Use enough points for the curves: 12 to 30 per curve, closer together where the curve is tight.
2. **Scale** them to the size the parts need (keep the ratios).
3. **Extrude the side profile** across the full width and **the top plan** through the full height, and **intersect** the two bodies. That gives the form's true side and top outlines at once, including asymmetry and a crown that peaks off-centre. Intersect a third body from the front section to round the cross-section.
4. **Soften** the edges the concept shows soft, with fillets where they work, or by lofting through cross-sections taken from the three views.
5. **Parting lines and colour splits**: split the body along the line the concept draws (a plane tilted to follow it, or a swept/extruded cut that follows the curve), and give each piece its colour.
6. **Signature details** as their own bodies: domed grilles (a sphere or a revolve cut back to the face), shaped light diffusers (an extruded outline, slightly proud), moulded switches and buttons (their real outline from the art, not a default circle or rectangle).

## Smooth curves: Solidcraft's toolbox

**Never draw a curved outline with `sketch.line` segments.** Every model in episodes 001 to 003 did, and that's a big part of why they came out boxy. Solidcraft's script has proper curve and surface tools (from `solidcraft-cli commands`, November 2026; run it again for the exact parameters):

| Need | Command | Notes |
|---|---|---|
| A traced silhouette | `sketch.spline.fit_point` | `points: [[x,y], …]` (2–500), passes through every point; `periodic: true` closes a loop smoothly (3+ points). The main tool for DESIGN.md's traced outlines. |
| Hand-shaped curves | `sketch.spline.control_point`, `sketch.spline.control_point_5` | Control-point splines (degree 5 for very smooth curvature). |
| A smooth join between two curves | `sketch.conic` | `a, b`: the two curve ends (`"l1.end"`); `continuity: g1…g4` (g2 and up match curvature: the "designed" look where a flat meets a curve). |
| Ovals, round ends | `sketch.ellipse`, `sketch.arc.three_point`, `sketch.arc.tangent`, `sketch.arc.center_point` | `sketch.arc.tangent` continues smoothly off a line or arc. |
| Rounded sketch corners | `sketch.fillet` | Round a corner in the sketch rather than filleting the solid later. |
| 3D curves | `sketch.spline3d` | For a parting line that swoops in 3D. |
| A body through sections | `solid.loft` | 2–50 `sections`; `rails`: one or two guide curves (from the first section to the last) the loft follows. Rails from the side and top silhouettes make the body match both. |
| A body along a path | `solid.sweep` | Profile along a path; supports rails, twist and scale. |
| Surfaces | `surface.loft`, `surface.sweep`, a curve-network patch (u/v curves, Coons or Gordon surface), fill patches, `surface.fillet`, a fairing tool | `surface.loft` has `continuity` per end and `crown` (how full it bulges): good for domes, bellies and the bulge of a grille. Join surfaces into a solid with `operation: join`. |
| Fillets that don't fail | `solid.fillet` with `fit: "reduce"` or `"taper"` | `exact` (the default) refuses a radius too big for the geometry, which is how episode 003's crown fillet failed. `reduce` uses the largest radius that fits; `taper` narrows it where room runs out. Also `type: variable` (radius → radius2 along the edge) and `type: curvature` (G2). |
| Combining | `solid.combine` | Join, cut and (check the parameter) intersect bodies: the silhouette method's step 3. |

A blockout in this script style (as in the episodes' `build_model.py`, which writes a JSON command list for `solidcraft-cli run`):

```python
# side profile on the XZ plane (x along the length, z up), traced in DESIGN.md and scaled to mm
side = [[0, 4], [3, 14], [10, 22], [22, 26], [38, 24], [52, 17], [60, 9], [60, 0], [0, 0]]
c("sketch.create", plane="XZ", name="side")
c("sketch.spline.fit_point", points=side[:-2])            # the curved top edge, nose to back
c("sketch.line", start=side[-3], end=side[-2]); c("sketch.line", start=side[-2], end=side[-1])
c("sketch.line", start=side[-1], end=side[0])             # flat base closes the loop
c("sketch.finish")
c("solid.extrude", sketch="side", distance=60, symmetric=True, name="side_body")   # check extrude's params
# top plan on XY: a closed periodic spline through the traced outline (asymmetry and all)
c("sketch.create", plane="XY", name="plan")
c("sketch.spline.fit_point", points=plan_points, periodic=True)
c("sketch.finish")
c("solid.extrude", sketch="plan", distance=40, name="plan_body")
c("solid.combine", bodies=["side_body", "plan_body"], operation="intersect", name="blockout")  # check the operation name
c("solid.fillet", edges=[...], radius=6, fit="reduce")     # soften; reduce never fails on a tight spot
```

Check each command's exact parameter names with `solidcraft-cli commands` before relying on this sketch; then replace it with the real working version once an episode has one.

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

`python3 tools/form/compare.py episodes/<slug>` writes `4-model/compare.png`: the favourite concept art, the control drawing and the latest blockout or iso screenshot side by side, scaled to the same height. Pass a screenshot to use another: `--shot 4-model/blockout-03.png`. For a revision: `python3 tools/form/compare.py products/<product>/rev-b` uses the previous hero render as the reference when there's no concept art in the folder.

Read it the way a designer would: squint, then check the silhouette, the proportions, where the visual weight sits, the parting line and colour split, then each detail. Score every signature feature in `DESIGN.md` (✓ / partly / ✗) and fix the worst first.
