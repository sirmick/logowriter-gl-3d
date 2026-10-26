# LogoWriter GL 3D

### [▶ Open the screensaver](https://sirmick.github.io/logowriter-gl-3d/)

**https://sirmick.github.io/logowriter-gl-3d/** · runs entirely in the page; needs a browser with WebGL 2

A 3D turtle-graphics screensaver built on the [LogoWriter GL](https://github.com/sirmick/logowriter-gl) compiler. Logo programs draw in 3D while the camera moves around the scene, and the playlist cycles through 16 programs with post-processing effects. It's a single HTML file with no build step.

## Features

- **3D turtles.** Each turtle carries a full orientation frame (heading, left, up). 2D programs still work unchanged and draw in the XY plane.
- **Same compiler.** The tokenizer, parser and Logo→JS code generator come from LogoWriter GL unchanged: coroutine turtles, `LAUNCH`, pure-procedure detection, and `;` comments.
- **Renderer.** Each segment is an instanced, camera-facing capsule impostor, antialiased in the fragment shader. Rendering goes through an MSAA RGBA16F target, a dual-filter bloom chain, and a composite pass with ACES tonemapping. The background is a procedural starfield and nebula sampled along the view ray, so it parallaxes with the camera.
- **Looks** (`L`):
  - **Neon:** additive glow.
  - **Hologram:** monochrome cyan with scanlines, flicker and chromatic aberration.
  - **Tubes:** lit, depth-tested solid tubes using alpha-to-coverage.
  - **Dream:** per-segment depth of field, made by widening each line by its circle of confusion.
- **Cameras** (`C`):
  - **Orbit:** auto-fits the drawing's bounding box.
  - **Chase:** rides behind the drawing turtle.
  - **Drift:** wanders the focus point around the drawing.
- **Lifecycle.** Each program draws, then holds while a light pulse runs along the drawing order, then dissolves into the next program. New segments flash briefly as they're drawn.
- **Flip side** (`E`). Shows the current program's source. You can edit it and run it with `Ctrl`/`⌘`+`Enter`.

## Programs

Gyro bloom · Hilbert cube · Torus knots · Lorenz attractor · Spring tree · Fireworks · Nautilus · Pursuit · Galaxy · Lissajous cage · Armillary · Sierpinski tetrahedron · Menger sponge · H-tree · Koch in 3D · Fern bush

## 3D primitives

| Primitive | Meaning |
|---|---|
| `FD BK n` · `RT LT deg` | Move; yaw around the turtle's up axis. |
| `UP DOWN deg` | Pitch the nose up or down. |
| `RR RL deg` | Roll right or left around the heading. |
| `SETXYZ x y z` · `SETZ z` | Move to a point, drawing if the pen is down. `SETXY`, `SETX`, `SETY` keep Z. |
| `SETPOS [x y z]` · `POS` | `POS` outputs `[x y z]`; `SETPOS` accepts 2 or 3 items. |
| `FACE [x y z]` | Point the heading at a point. |
| `ZCOR` | Turtle Z. `DISTANCE` and `POSOF` are 3D. |
| `HUE deg` | Outputs an `[r g b]` color from a cosine palette. |
| `WAIT n` | Sleep n frames. |

The default pen color (black) is treated as "auto" and colored from the current look's palette along the drawing order.

## Keys

`Space`/`→` next · `←` previous · `L` look · `C` camera · `P` hold · `E` code · `F` fullscreen (also requests a screen wake lock) · `H` hide HUD · drag to orbit · wheel to zoom. The HUD fades after 3.5 s without input.

## Testing

`node tests/run-programs.mjs` compiles and runs every program headless, with rendering stubbed out. For each one it reports the segment count, peak turtle count, approximate run time at screensaver speed, and 3D bounds. It exits non-zero if any program fails.

## License

MIT, see [LICENSE](LICENSE).
