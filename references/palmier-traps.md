# Palmier Pro: things that fail quietly

Each of these reports success while doing something other than what you meant. Check for them every time.

1. **Adding the first clip resets the canvas** to that clip's resolution. Call `set_project_settings` with `width: 1080, height: 1920` after `add_clips`, not before.
2. **`fontSize` is in canvas points, not pixels.** Points are measured against a 1080-tall canvas, so on a 1080x1920 reel one point renders as 1.78 pixels. For text that should render 44px tall: `fontSize = 44 * 1080 / 1920 = 24.75`. Shadow blur, outline width and line spacing use the same unit.
3. **A text box wraps at about 80 percent of the canvas width** (roughly 860px on a 1080 canvas). A long line can quietly wrap into two. Check the rendered frame, and break lines yourself with `\n` where the user wants them.
4. **Bold fonts need `bold: true`.** Naming a bold font such as `HelveticaNeue-Bold` is not always enough; set the bold trait as well and check the render.
5. **Two clips on one track at the same time collapse into one.** Adding three text blocks in one `add_texts` call puts them on one track, and only the last survives. Add each text block and each image in its own call so each gets its own track (the builder does this).
6. **Colour temperature is in kelvin.** 6500 is neutral; 6300 is slightly cooler and 6700 slightly warmer. Small numbers such as 0.04 turn the whole image blue.
7. **Transforms are fractions of the canvas, not pixels.** A clip's `width: 1.1` means 110 percent of the canvas. Position keyframes set the clip's top-left corner, not its centre.
8. **`capture_frame` occasionally stalls.** Use a timeout and retry once (the bundled client does).
9. **Closing is the save.** `manage_project` with `action: close` writes the final state to disk. Read `project.json` back if you need to confirm a change.
10. **Moving a project:** close it, move the `.palmier` folder, then open it from the new path once so Palmier records the new location.
11. **Media is referenced in place, not copied.** Keep the cut sources and images inside the output folder so the projects never lose them.
12. **Measuring a camera move:** static text dominates any whole-frame comparison, so compare a region with only footage in it (for example the bottom third) when checking that a pan rendered.
13. **Exports carry the source audio untouched.** The cut sources have no audio, so exports are silent by design.
