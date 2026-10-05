# Anki plain-text export/import

## Export (Anki 2.1.55+ desktop)
In the Browser, select the notes (or a whole deck), then choose *Notes → Export Notes*
(or *File → Export*). Set the format to **Notes in Plain Text (.txt)** and tick:
- Include HTML and media references
- Include tags
- Include deck name
- Include notetype name
- Include unique identifier (the GUID; required for updating notes in place)

## File format
Header lines come first, then one row per note:
```
#separator:tab
#html:true
#guid column:1
#notetype column:2
#deck column:3
#tags column:N
```
- Rows use CSV quoting. A field that contains the separator, a newline or `"` is
  wrapped in quotes, and any `"` inside it is doubled.
- The columns that aren't special are the note's fields, in note-type order. When
  note types are mixed, rows can have different lengths.
- `anki_tsv.py` keeps the header exactly as it was and uses the same quoting.

## Import behaviour (Anki manual, "Text files")
- If there's a GUID, notes are matched on it. With **Existing notes: Update**, the
  other fields are overwritten and "the existing scheduling information on all
  their cards will be preserved".
- If there's no GUID, notes are matched on the first field. A changed first field
  means a new duplicate note.
- The duplicate option doesn't work for rows with a non-empty GUID.
- Note type and field count must match the existing note. Changing the note type
  isn't possible through import.
- Cloze numbers you remove leave empty cards. Clean them up with *Tools → Empty Cards*.
- Media: import only brings in the `<img src>` references. The files themselves
  must be in `collection.media` (*Tools → Check Media* lists missing ones).

## Sources
- https://docs.ankiweb.net/importing/text-files.html
- https://docs.ankiweb.net/exporting.html
- https://docs.ankiweb.net/editing.html
