--[[
letter.lua: pandoc Lua filter for markdown-to-odt-letters.

Turns YAML frontmatter into the parts of a formal letter and wraps the
Markdown body with them. All visual styling comes from reference.odt; this
filter only chooses which named style each part uses and where the address
frames sit on page 1.

A4 paper and EU letter conventions only. Polish (pl-PL) is the default.

Layout "letter" (default when `recipient` is set), Polish defaults:
  [sender, top left]                  [place, date "… r.", top right]
                                      [return line + recipient: right window]
  reference, subject, salutation, BODY,
                                      [closing, ~3 lines space, signature: right half]
  numbered enclosures
Other languages default to the DIN 5008 arrangement: window left, sender top
right, date right-aligned below the address, sign-off on the left. Every
choice is overridable: window_side, date_position, signature_side.
Layout "document" (no recipient: notices, contracts):
  title, subtitle, date, BODY, closing, signature, enclosures (whichever exist)

Tested with pandoc 3.1.3. Needs pandoc >= 2.17 (Lua `pandoc.utils.type`).
]]

local stringify = pandoc.utils.stringify
local ptype = pandoc.utils.type

-- ---------------------------------------------------------------- helpers
local function xml_escape(s)
  return (s:gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;"):gsub('"', "&quot;"))
end

local function is_set(v)
  if v == nil then return false end
  if type(v) == "boolean" then return v end
  return stringify(v) ~= ""
end

-- Split an Inlines value at (soft) line breaks.
local function split_inlines(inl, out)
  local cur = pandoc.List()
  for _, el in ipairs(inl) do
    if el.t == "SoftBreak" or el.t == "LineBreak" then
      out:insert(stringify(cur)); cur = pandoc.List()
    else
      cur:insert(el)
    end
  end
  if #cur > 0 then out:insert(stringify(cur)) end
end

-- A metadata value as a list of text lines. Accepts a YAML list, or a
-- string / literal block (`|`) with one line per address line.
local function lines(v)
  local out = pandoc.List()
  if v == nil then return out end
  local t = ptype(v)
  if t == "List" then
    for _, item in ipairs(v) do out:insert(stringify(item)) end
  elseif t == "Inlines" then
    split_inlines(v, out)
  elseif t == "Blocks" then
    for _, b in ipairs(v) do
      if b.content and ptype(b.content) == "Inlines" then split_inlines(b.content, out)
      else out:insert(stringify(b)) end
    end
  else
    for l in tostring(stringify(v)):gmatch("[^\n]+") do out:insert(l) end
  end
  return out:filter(function(l) return l:match("%S") ~= nil end)
end

-- Lengths: 25, "25mm", "2.5cm", "1in", "72pt" -> millimetres (number)
local function to_mm(v, default)
  if v == nil then return default end
  local s = stringify(v):gsub("%s", "")
  local n, unit = s:match("^([%d%.]+)(%a*)$")
  n = tonumber(n)
  if not n then return default end
  if unit == "" or unit == "mm" then return n
  elseif unit == "cm" then return n * 10
  elseif unit == "in" then return n * 25.4
  elseif unit == "pt" then return n * 25.4 / 72 end
  return default
end

local function mm(n) return string.format("%.2fmm", n) end

-- ------------------------------------------------------- language tables
local MONTHS = {
  en = {"January","February","March","April","May","June","July","August","September","October","November","December"},
  de = {"Januar","Februar","März","April","Mai","Juni","Juli","August","September","Oktober","November","Dezember"},
  fr = {"janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"},
  es = {"enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"},
  it = {"gennaio","febbraio","marzo","aprile","maggio","giugno","luglio","agosto","settembre","ottobre","novembre","dicembre"},
  nl = {"januari","februari","maart","april","mei","juni","juli","augustus","september","oktober","november","december"},
  pt = {"janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"},
  -- genitive month forms, as used in dates
  pl = {"stycznia","lutego","marca","kwietnia","maja","czerwca","lipca","sierpnia","września","października","listopada","grudnia"},
  cs = {"ledna","února","března","dubna","května","června","července","srpna","září","října","listopadu","prosince"},
  fi = {"tammikuuta","helmikuuta","maaliskuuta","huhtikuuta","toukokuuta","kesäkuuta","heinäkuuta","elokuuta","syyskuuta","lokakuuta","marraskuuta","joulukuuta"},
  sv = {"januari","februari","mars","april","maj","juni","juli","augusti","september","oktober","november","december"},
  da = {"januar","februar","marts","april","maj","juni","juli","august","september","oktober","november","december"},
}
local REF_LABEL = { en = "Reference:", de = "Aktenzeichen:", fr = "Réf. :", es = "Ref.:", it = "Rif.:", nl = "Kenmerk:",
                    pt = "Ref.ª:", pl = "Znak sprawy:", cs = "Č. j.:", fi = "Viite:", sv = "Referens:", da = "Reference:" }
local ENC_LABEL = { en = "Enclosures:", de = "Anlagen:", fr = "Pièces jointes :", es = "Anexos:", it = "Allegati:", nl = "Bijlagen:",
                    pt = "Anexos:", pl = "Załączniki:", cs = "Přílohy:", fi = "Liitteet:", sv = "Bilagor:", da = "Bilag:" }

-- ISO dates (YYYY-MM-DD) are written out in the letter's language;
-- anything else is used verbatim.
local function format_date(raw, lang)
  local y, m, d = raw:match("^(%d%d%d%d)-(%d%d)-(%d%d)$")
  local base = lang:match("^(%a+)") or "en"
  if not y or not MONTHS[base] then return raw end
  local month = MONTHS[base][tonumber(m)]
  d = tostring(tonumber(d))
  if base == "pl" then return d .. " " .. month .. " " .. y .. " r."   -- "28 września 2026 r."
  elseif base == "de" or base == "da" or base == "cs" or base == "fi" then
    return d .. ". " .. month .. " " .. y
  elseif base == "es" or base == "pt" then return d .. " de " .. month .. " de " .. y
  elseif base == "fr" and d == "1" then return "1er " .. month .. " " .. y
  else return d .. " " .. month .. " " .. y end
end

-- --------------------------------------------------- window geometry (mm)
-- A4 only. Address field of DIN 5008 form B / ISO 269 window envelopes
-- (DL, C5, C6: window 90 x 45 mm, 20 mm from the side edge, 15 mm from the
-- bottom). Text starts 5 mm inside the window. `window_side: right` mirrors
-- the field for envelopes with the window on the right ("okienko prawe",
-- the Polish default here; also common in France).
-- Envelopes vary: always test-fold one printout into the real envelope.
local PAGE_W, PAGE_H = 210, 297
local GEOMETRY = {
  left  = { window_left = 25,  window_top = 62.7, window_w = 80, window_h = 27.3, return_top = 57 },
  right = { window_left = 105, window_top = 62.7, window_w = 80, window_h = 27.3, return_top = 57 },
}

local function frame(name, x, y, w, h, paras)
  return pandoc.RawBlock("opendocument", string.format(
    '<draw:frame draw:style-name="Letter_20_Frame" draw:name="%s" text:anchor-type="page" ' ..
    'text:anchor-page-number="1" svg:x="%s" svg:y="%s" svg:width="%s" svg:height="%s" draw:z-index="0">' ..
    '<draw:text-box fo:min-height="%s">%s</draw:text-box></draw:frame>',
    name, mm(x), mm(y), mm(w), mm(h), mm(h), paras))
end

local function paras(style, ls)
  local out = {}
  for _, l in ipairs(ls) do
    out[#out + 1] = string.format('<text:p text:style-name="%s">%s</text:p>', style, xml_escape(l))
  end
  return table.concat(out)
end

-- Fold / punch marks: tiny empty frames with a top border (reliably black;
-- LibreOffice ignores common graphic styles on draw:line shapes).
local function mark(x1, y, x2)
  return pandoc.RawBlock("opendocument", string.format(
    '<draw:frame draw:style-name="Letter_20_Mark" draw:name="Mark%d" text:anchor-type="page" ' ..
    'text:anchor-page-number="1" svg:x="%s" svg:y="%s" svg:width="%s" svg:height="0.30mm" draw:z-index="1">' ..
    '<draw:text-box><text:p text:style-name="Letter_20_Spacer"/></draw:text-box></draw:frame>',
    math.floor(y * 10), mm(x1), mm(y), mm(x2 - x1)))
end

-- A custom-styled paragraph. Inline Markdown in the value (e.g. *italic*) survives.
local function styled(style, value)
  local inl = (ptype(value) == "Inlines") and value or pandoc.Inlines(stringify(value))
  return pandoc.Div({ pandoc.Para(inl) }, pandoc.Attr("", {}, { ["custom-style"] = style }))
end

-- Tables: pandoc writes no column widths for short Markdown tables, and
-- LibreOffice then squeezes the columns so cell texts collide. Give every
-- column a width proportional to its longest cell (full text width), and
-- add a small gap after the table (ODT tables have no paragraph spacing).
function Table(tbl)
  local ncols = #tbl.colspecs
  local maxlen = {}
  for i = 1, ncols do maxlen[i] = 3 end
  local function scan(rows)
    for _, row in ipairs(rows) do
      for i, cell in ipairs(row.cells) do
        if i <= ncols then
          maxlen[i] = math.max(maxlen[i], utf8.len(stringify(cell.contents)) or 3)
        end
      end
    end
  end
  scan(tbl.head.rows)
  for _, b in ipairs(tbl.bodies) do scan(b.body) end
  local defaults = true
  for _, cs in ipairs(tbl.colspecs) do
    if cs[2] ~= nil and cs[2] ~= pandoc.ColWidthDefault and type(cs[2]) == "number" and cs[2] > 0 then
      defaults = false
    end
  end
  if defaults then
    local total = 0
    for i = 1, ncols do total = total + maxlen[i] end
    for i = 1, ncols do tbl.colspecs[i] = { tbl.colspecs[i][1], maxlen[i] / total } end
  end
  return { tbl, pandoc.RawBlock("opendocument", '<text:p text:style-name="Letter_20_Spacer"/>') }
end

-- ------------------------------------------------------------------ main
function Pandoc(doc)
  local meta = doc.meta
  local lang = is_set(meta.language) and stringify(meta.language)
            or (is_set(meta.lang) and stringify(meta.lang)) or "pl-PL"
  meta.lang = pandoc.MetaString(lang)
  local base = lang:match("^(%a+)") or "en"
  local polish = (base == "pl")

  -- Layout choices: Polish convention by default for Polish letters,
  -- DIN 5008 otherwise. md2odt.py resolves (and reports) the same defaults.
  local function choice(key, default, allowed)
    local v = is_set(meta[key]) and stringify(meta[key]):lower() or default
    for _, a in ipairs(allowed) do if v == a then return v end end
    return default
  end
  local side = choice("window_side", polish and "right" or "left", { "left", "right" })
  -- date at the top only fits in the free column above a right-hand window
  local date_pos = choice("date_position", (polish and side == "right") and "top" or "below",
                          { "top", "below" })
  if side == "left" then date_pos = "below" end
  local sig_side = choice("signature_side", polish and "right" or "left", { "left", "right" })
  local sig_sfx = (sig_side == "right") and " Right" or ""
  local g = GEOMETRY[side]
  local margin = to_mm(meta.margins, 25)
  local margin_right = to_mm(meta.margin_right, margin)

  local recipient = lines(meta.recipient)
  local sender = lines(meta.sender)
  local layout = is_set(meta.layout) and stringify(meta.layout)
               or (#recipient > 0 and "letter" or "document")

  local head, tail = pandoc.List(), pandoc.List()

  -- date: ISO or free text; defaults to today (md2odt.py reports this)
  local date_raw = is_set(meta.date) and stringify(meta.date) or os.date("%Y-%m-%d")
  local date_text = format_date(date_raw, lang)
  if is_set(meta.place) then date_text = stringify(meta.place) .. ", " .. date_text end

  if layout == "letter" then
    local wl = to_mm(meta.window_left, g.window_left)
    local wt = to_mm(meta.window_top, g.window_top)
    local ww = to_mm(meta.window_width, g.window_w)
    local wh = to_mm(meta.window_height, g.window_h)

    -- Sender block: the column beside the window (right of it by default,
    -- left of it with window_side: right), from the top margin down to the
    -- bottom of the window. Because frames use wrap=none, body text cannot
    -- start until below this frame and the recipient frame, so the date
    -- always follows the address field, however short the sender block is.
    -- (Frames must not overlap: LibreOffice drops/moves overlapping frames.)
    local sx, sw, sstyle
    if side == "left" then
      sw = math.min(80, PAGE_W - margin_right - (wl + ww) - 2)
      sx, sstyle = PAGE_W - margin_right - sw, "Letter_20_Sender"
    else
      sw = math.min(80, wl - 2 - margin)
      sx, sstyle = margin, "Letter_20_Sender_20_Left"
    end
    head:insert(frame("Sender", sx, margin, sw, wt + wh - margin,
                      #sender > 0 and paras(sstyle, sender)
                      or '<text:p text:style-name="Standard"/>'))

    -- return line (small sender line shown in the window above the address)
    -- Postal lines only: phone / e-mail / web lines are left out, both because
    -- they don't belong there and because a long line wraps into the address.
    local postal = pandoc.List()
    for _, l in ipairs(sender) do
      local low = l:lower()
      if not (low:find("@", 1, true) or low:match("^%s*tel") or low:match("^%s*kom")
              or low:match("^%s*fax") or low:match("^%s*phone") or low:match("^%s*e%-?mail")
              or low:match("^%s*www") or low:match("^%s*https?:") or low:match("^%s*%+?[%d%s%-/()]+$")) then
        postal:insert(l)
      end
    end
    local rl = meta.return_line
    local rl_text
    if type(rl) == "boolean" then rl_text = (rl and #postal > 0) and table.concat(postal, " · ") or nil
    elseif is_set(rl) then rl_text = stringify(rl)
    elseif #postal > 0 then rl_text = table.concat(postal, " · ") end
    if rl_text then
      head:insert(frame("ReturnLine", wl, wt - (g.window_top - g.return_top), ww, 4,
                        paras("Letter_20_Return_20_Line", { rl_text })))
    end

    head:insert(frame("Recipient", wl, wt, ww, wh, paras("Letter_20_Recipient", recipient)))

    -- Polish style: "Place, date" at the top right, above the window
    if date_pos == "top" then
      head:insert(frame("Date", wl, margin, ww, 8, paras("Letter_20_Date_20_Top", { date_text })))
    end

    if meta.fold_marks == true then
      -- DIN 5008 form B: folds at 105 / 210 mm, punch (hole) mark at 148.5 mm
      head:insert(mark(5, 105, 10)); head:insert(mark(5, 210, 10)); head:insert(mark(4, PAGE_H / 2, 11))
    end
  end

  -- empty first paragraph: switches page 1 to "First Page" (no page number)
  head:insert(pandoc.RawBlock("opendocument", '<text:p text:style-name="Document_20_Start"/>'))

  if layout == "letter" then
    if date_pos == "top" then
      -- gap between the address field and the subject (date is up top)
      head:insert(pandoc.RawBlock("opendocument", '<text:p text:style-name="Letter_20_Address_20_Gap"/>'))
    else
      head:insert(styled("Letter Date", date_text))
    end
    if is_set(meta.reference) then
      local label = is_set(meta.reference_label) and stringify(meta.reference_label)
                    or REF_LABEL[base] or REF_LABEL.en
      head:insert(styled("Letter Reference", label .. " " .. stringify(meta.reference)))
    end
    if is_set(meta.subject) then head:insert(styled("Letter Subject", meta.subject)) end
  else
    if is_set(meta.title) then head:insert(styled("Title", meta.title)) end
    if is_set(meta.subtitle) then head:insert(styled("Subtitle", meta.subtitle)) end
    if is_set(meta.date) or is_set(meta.place) then head:insert(styled("Date", date_text)) end
  end
  if is_set(meta.salutation) then head:insert(styled("Letter Salutation", meta.salutation)) end

  if is_set(meta.closing) then tail:insert(styled("Letter Closing" .. sig_sfx, meta.closing)) end
  local sig = is_set(meta.signature_name) and stringify(meta.signature_name)
              or (layout == "letter" and sender[1]) or nil
  if sig then
    tail:insert(styled("Letter Signature" .. sig_sfx, sig))
    for _, t in ipairs(lines(meta.signature_title)) do
      tail:insert(styled("Letter Signature Title" .. sig_sfx, t))
    end
  end
  local enc = lines(meta.enclosures)
  if #enc > 0 then
    local label = is_set(meta.enclosures_label) and stringify(meta.enclosures_label)
                  or ENC_LABEL[base] or ENC_LABEL.en
    -- one paragraph with line breaks, so the list can never split across pages
    local body = { xml_escape(label) }
    for i, e in ipairs(enc) do body[#body + 1] = i .. ". " .. xml_escape(e) end   -- numbered
    body = { '<text:p text:style-name="Letter_20_Enclosures">' ..
             table.concat(body, '<text:line-break/>') .. '</text:p>' }
    tail:insert(pandoc.RawBlock("opendocument", table.concat(body)))
  end

  -- stop pandoc's own template from printing a title block
  for _, k in ipairs({ "title", "subtitle", "author", "date", "abstract", "toc" }) do meta[k] = nil end

  local blocks = pandoc.List()
  blocks:extend(head); blocks:extend(doc.blocks); blocks:extend(tail)
  return pandoc.Pandoc(blocks, meta)
end
