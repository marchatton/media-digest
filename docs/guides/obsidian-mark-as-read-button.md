# Obsidian "Mark as Read" Button

Turn each summary note into a one-tap workflow: play the embedded audio, then tap a button that moves both the markdown file and its twin `.mp3` from the `summaries/unread/` folder to `summaries/read/`. This approach relies entirely on community plugins (no external scripts) so it works on desktop and mobile.

## Prerequisites
1. **Buttons** plugin (Community → install → enable).
2. **QuickAdd** plugin (Community → install → enable).
3. Obsidian vault synced across devices (Obsidian Sync / iCloud / Syncthing) so the `.mp3` moves with the note.
4. Consistent file layout, e.g.
   - `summaries/unread/<note>.md`
   - `summaries/unread/<note>.mp3`
   - `summaries/read/` (destination).

> If your folders differ, adjust the macro targets below.

## Step 1 – Create the QuickAdd Macro
1. Open **Settings → QuickAdd → Macros → + Add Macro**. Name it `Move summary to read`.
2. Click the new macro → **Add Command** twice so the macro will run two commands sequentially.
3. Configure the commands:
   - **Command 1:** `File: Move file` → set **Target folder** to `summaries/read/`.
   - **Command 2:** `File: Move attachment(s)` → choose `Link/attachment under cursor` and set the destination to `summaries/read/`.
4. Toggle **Capture active file** so the macro always acts on the note you’re viewing, and enable **Run on mobile** if prompted.
5. Press **Save Macro**. You can test it from the QuickAdd command palette entry `QuickAdd: Macro: Move summary to read`.

> If you prefer to rename the `.mp3` when moving, add a third step using QuickAdd’s **Templater** action or a small script, but the simple move works for most cases.

## Step 2 – Add the Button Snippet
Insert this block near the top (or bottom) of any summary template so every generated note inherits it:

````markdown
```button
name ✅ Mark as Read
type command
action QuickAdd: Macro: Move summary to read
```
````

- On desktop/mobile this renders a button. Tapping it executes the macro, moving the `.md` and its `.mp3` to your `read` folder.
- Buttons caches the command label, so if you later rename the macro just update the `action` line.

## Variant – Templater Script Instead of QuickAdd
If you already use Templater for automation, you can skip QuickAdd and wire the button directly to a Templater script. Create `scripts/move-summary.js` inside your vault’s Templater folder with:

```javascript
module.exports = async (tp) => {
  const file = tp.file.find_tfile(tp.file.path(true));
  const destination = 'summaries/read/';
  await app.fileManager.renameFile(file, destination + file.name);

  const audioEmbed = tp.file.content.match(/!\[\[(.*\.mp3)\]\]/);
  if (audioEmbed?.[1]) {
    const audioFile = app.metadataCache.getFirstLinkpathDest(audioEmbed[1], file.path);
    if (audioFile) {
      await app.fileManager.renameFile(audioFile, destination + audioFile.name);
    }
  }
};
```

Then change the button block to:

````markdown
```button
name ✅ Mark as Read
type templater
action move-summary
```
````

This gives you full control (rename, add metadata updates, etc.) at the cost of managing a short script.

## Optional – Hotkey or Command Palette
- Assign a hotkey to `QuickAdd: Macro: Move summary to read` (Settings → Hotkeys) for keyboard-first use.
- Add the macro to the ribbon (QuickAdd setting **Show in ribbon**) for a permanent clickable icon if you dislike inline buttons.

## Troubleshooting
| Symptom | Fix |
| --- | --- |
| Only the markdown moved, audio stayed in `unread` | Ensure the audio embed is selected (cursor on `![[file.mp3]]`) *before* running `File: Move attachment(s)`, or switch Command 2 to `All attachments in active file` if the plugin version supports it. |
| Button missing on mobile | Verify both Buttons and QuickAdd plugins are enabled on mobile. Sync the `.obsidian/plugins` folder or install manually. |
| Macro throws “folder not found” | Double-check the destination path in the macro matches your vault structure. |
| Need more automation | Replace QuickAdd with a custom plugin/Templater script to perform extra logic (rename files, update metadata, etc.). |

That’s it—once the Hetzner pipeline drops a new note and audio pair into `summaries/unread/`, Obsidian shows the embedded player plus the **Mark as Read** button so you can listen anywhere and file it away with a single tap.
