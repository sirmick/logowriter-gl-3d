# LogoWriter GL 3D

### [▶ Open the screensaver](https://sirmick.github.io/logowriter-gl-3d/)

**https://sirmick.github.io/logowriter-gl-3d/** · runs entirely in the page; needs a browser with WebGL 2

A 3D turtle-graphics screensaver built on the [LogoWriter GL](https://github.com/sirmick/logowriter-gl) compiler. Logo programs draw in 3D while the camera moves around the scene, and the playlist cycles through 16 programs with post-processing effects. It's one ES module (`logowriter3d.js`) plus a thin page (`index.html`), with no build step and no dependencies, and it can be embedded in other pages (see [Embedding](#embedding)).

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

## Running locally

The page loads `logowriter3d.js` as an ES module, and browsers won't load modules from `file://`, so opening `index.html` straight from disk no longer works. Serve the folder instead:

```sh
python3 -m http.server   # then open http://localhost:8000/
```

## Keys

`Space`/`→` next · `←` previous · `L` look · `C` camera · `P` hold · `E` code · `F` fullscreen (also requests a screen wake lock) · `H` hide HUD · drag to orbit · wheel to zoom. The HUD fades after 3.5 s without input.

## Embedding

`logowriter3d.js` runs the screensaver inside any element. Importing it has no side effects; each `mount` call creates its own canvas, runtime, renderer and WebGL context, so several can run at once and a mount can be disposed and recreated.

```js
import {mount, PROGRAMS, LOOKS, CAMS} from './logowriter3d.js';

const saver = mount(document.querySelector('#screensaver'), {look: 'random', speed: 1.5});
// later
saver.dispose();
```

**Catalogues** (each an array of `{id, name}`):

- `PROGRAMS`: the 16 programs, with stable kebab-case ids (`gyro-bloom`, `hilbert-cube`, `torus-knots`, `lorenz-attractor`, `spring-tree`, `fireworks`, `nautilus`, `pursuit`, `galaxy`, `lissajous-cage`, `armillary`, `sierpinski-tetrahedron`, `menger-sponge`, `h-tree`, `koch-in-3d`, `fern-bush`).
- `LOOKS`: `neon`, `hologram`, `tubes`, `dream`.
- `CAMS`: `auto` (each program's own default camera), `orbit`, `chase`, `drift`.

**`mount(container, opts) → handle`.** All options are optional.

| Option | Default | Meaning |
|---|---|---|
| `programs` | `'all'` | `'all'` or an array of program ids to cycle through. |
| `order` | `'shuffle'` | `'shuffle'` (reshuffled each pass) or `'sequence'` (the order given). |
| `look` | `'neon'` | A look id, or `'random'` to pick per program (the standalone page's "Auto"). |
| `cam` | `'auto'` | A camera id, or `'auto'` for each program's default. |
| `speed` | `1` | Drawing speed multiplier. |
| `hud` | `false` | Show the title, stats and buttons overlay. |
| `keys` | `false` | Keyboard shortcuts (see [Keys](#keys)). Keys are handled only while focus is inside the mount or on the page body, so it never takes keys from other inputs. |
| `editor` | `false` | Enable the flip-side source editor (`Code` button, `E`). |
| `maxSegments` | `400000` | Cap on line segments per program (36 bytes each on the CPU and GPU). The standalone page uses 2,000,000. |
| `fps` | `0` | Frame-rate cap; `0` means uncapped (display refresh). Drawing pace is kept the same when capped. |
| `onChange` | none | Called with `{look, cam}` when the user changes the look or camera from the HUD or keys (the standalone page uses it to save them). |
| `onFullscreen` | none | If given, the HUD shows a Fullscreen button and `F` calls this. The module itself never requests fullscreen or a wake lock. |

The handle has these methods. All of them do nothing after `dispose()`.

- `dispose()`: stops the animation frame loop, removes every listener, deletes the GL buffers, programs, framebuffers and textures, calls `WEBGL_lose_context.loseContext()`, removes the canvas and any DOM it added, and drops the segment buffer. Calling it twice is safe.
- `pause()` / `resume()`: stop and restart the frame loop. The loop also pauses on its own while `document.hidden`.
- `next()`: skip to the next program.
- `set(partialOpts)`: change any of the options above on a running mount. Changing `programs` or `order` restarts the playlist.

**Layout and styling.** The mount fills `container` (give the container a size), with a `<canvas>` at `width/height: 100%`. The canvas resolution follows a `ResizeObserver` on the container times `devicePixelRatio`, capped at 2. Everything the module adds sits under one `.lw3d` element whose scoped `<style>` uses only `.lw3d`/`.lw3d-*` selectors; it never styles `html` or `body`. The HUD names IBM Plex Mono and Silkscreen but doesn't load them: load the fonts in the host page if you want them, otherwise monospace fallbacks are used. The module doesn't use `localStorage`.

**Errors.** If WebGL 2 is unavailable, `mount` throws an `Error` with `err.code === 'no-webgl2'` and adds nothing to the DOM. Without `EXT_color_buffer_float` it falls back to 8-bit render targets (softer bloom) rather than failing, so `'no-float-color'` is never thrown. Any other GPU setup failure (for example a shader that won't compile) throws with `err.code === 'gl-init'`.

## Testing

`node tests/run-programs.mjs` compiles and runs every program headless, with rendering stubbed out. For each one it reports the segment count, peak turtle count, approximate run time at screensaver speed, and 3D bounds. It exits non-zero if any program fails. It imports the compiler and runtime from `logowriter3d.js` (via its `internals` export, which is not part of the embedding API).

`~/.venvs/web/bin/python tests/embed_check.py` (any Python with Playwright, numpy and Pillow) serves the repo and drives headless Chromium with SwiftShader WebGL 2. It checks that `index.html` renders and responds to keys, and uses `tests/embed.html` to check that the module: adds no globals or DOM on import; renders into a 640×360 div; disposes cleanly (canvas gone, context lost, and calling it twice is safe); mounts again; runs two mounts at once; and throws `no-webgl2` without leaving any DOM behind.

## License

MIT, see [LICENSE](LICENSE).
