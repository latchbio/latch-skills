<goal>
Overlay a user's tissue image (e.g. H&E or another pathology image) onto their spatial H5AD data by registering it to bead/spot coordinates with the viewer's built-in alignment tool, then persist the resulting alignment back to the H5AD file.
</goal>

<method>
### Step 0 — Always offer this step
Whenever spatial H5AD data is loaded into the viewer at the start of secondary analysis (`steps/data_loading.md`), ask the user whether they have an H&E or equivalent pathology image of the tissue they'd like to overlay — don't wait for them to bring it up. If they don't have one or decline, skip this step and continue the normal flow.

### Step 1 — Get the image file
Ask the user for the location of their tissue image file. This is almost always a **separate file** from the H5AD (e.g. a `.tiff`/`.png`/`.jpg`/`.svs` scan) — do not assume an image is already embedded in the H5AD. If the user hasn't provided it yet, render a `w_ldata_picker` (`file_type="file"`) for it and tell them they may instead use the attach button in the Agent interface or the image button in the viewer alignment tool — all 3 routes are fine. If none works, ask for its Latch Data path.

### Step 2 — Load the image and align
Using the **same `w_h5` viewer session opened in `steps/data_loading.md`** (which must already be opened with `sync_to` set to the source H5AD's `LPath` — see that doc), load the image file into the viewer and open the built-in alignment tool to register the image to the bead/spot coordinates. The tool performs the rotation/scale/translation fit interactively — the agent's job is to launch it with the right inputs and confirm the result looks correct (beads land on tissue, not background) before calling the overlay complete. If alignment looks off, tell the user and let them re-run the tool rather than declaring success.

Tell the user which tab to switch to *before* asking them to align — see `<new_tab_notice>` below for
the wording.

### Step 3 — Persist the alignment
Because the viewer was opened with `sync_to=h5ad_path`, the alignment performed in the viewer is written back to the source H5AD automatically — there is no separate save step to run. Confirm with the user that the alignment is complete before moving on, since edits sync as they happen in the viewer.
</method>

<workflows>
</workflows>

<library>
</library>

<self_eval_criteria>
- The user was proactively asked about an H&E/pathology image at data-loading time, not only when they brought it up themselves.
- The image file is confirmed as the user's intended tissue image before alignment is attempted.
- The viewer used for alignment was opened with `sync_to` pointed at the source H5AD's `LPath`, so the alignment is actually persisted back to the file rather than lost at session end.
- After alignment, beads visually fall on tissue regions rather than background; if they don't, flag it to the user and offer to re-run the alignment tool instead of treating the step as done.
- The user was told, in chat, which tab to switch to in order to run the alignment tool.
</self_eval_criteria>

<new_tab_notice>
The alignment tool is hands-on and lives in the viewer's tab, so the user cannot do this step from
wherever they are currently looking. Tell them which tab to switch to before asking them to align —
see "Telling the user where results appeared" in `SKILL.md`:

> Your H&E image is loaded and the alignment tool is open in the **viewer tab** — click that tab in
> the notebook and drag the image until the beads land on tissue. Tell me when it looks right.

This is the same tab `steps/data_loading.md` opened, not a new one — say "the viewer tab" rather than
"a new tab" so the user does not go hunting for a second one.
</new_tab_notice>
