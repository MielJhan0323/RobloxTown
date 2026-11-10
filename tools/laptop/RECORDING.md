# Recording guide (for Claude on the laptop, with Roblox Studio MCP)

When the user says **"record <slug>"**:

1. Run `bash ~/RobloxTown/tools/laptop/sync.sh` to get the latest scripts.
2. Read `scripts/<slug>.md`: the shot list table (location, characters, pose/expression, camera,
   props, mood, FX, seconds) and any notes above it (e.g. how a recurring prop must look).
3. Work through the shots **grouped by location** (build each set once, reuse it), in Roblox Studio:
   - real Roblox avatars + Toolbox models; warm sunset lighting for `warm`, darker/bluer for `sad`/`night`;
   - pose characters to match the pose/expression column; keep recurring props identical across shots;
   - vertical 9:16 camera; **faces in the upper 40% of the frame** (captions sit on the chest);
   - shots with movement: start the animation first.
4. Record each shot with macOS screen capture over **only the 3D view**, mouse moved out of view:
   `screencapture -x -v -V <sec+1> -R x,y,w,h ~/RobloxTown/raw/<slug>/shot_XX.mov`
   (`XX` = the shot number with two digits; record ~1 s longer than the Sec column).
5. Check each file exists and isn't empty before moving on. Don't take screenshots to check your work
   unless a recording failed (saves usage). Do 10 shots, then stop and tell the user, so they can `/clear`.
6. When all shots are done, tell the user: "Upload `~/RobloxTown/raw/<slug>/` to the shared Drive
   folder and send the link to the cloud Claude."

Tips: same lighting/sky across a story; avoid UI, grid, selection outlines in frame; if a shot
can't be built exactly, get as close as possible and note it for the user.
