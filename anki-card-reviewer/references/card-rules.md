# Card-writing rules

Tags in brackets point to the sources at the bottom. Cite rule names in `issues`.

## Core properties [M]
- **Focused**: one detail per card. Split multi-part answers.
- **Precise**: the question says exactly what kind of answer is wanted.
- **Consistent**: the same correct answer on every review. Open-ended "give an
  example" cards produce varying answers. Keep them only if they are deliberately
  creative prompts.
- **Tractable**: the user should be right about 90% of the time. Cards that keep
  failing (leeches) need splitting, more context or a mnemonic, not more reviews.
- **Effortful**: the answer must come from memory, not from the wording of the question.

## Checks
| Rule | Problem | Fix |
|---|---|---|
| one-answer [B2] | several answers are valid | narrow the question or add a disambiguating cue |
| yes-no [M, B5] | "Is X…?" | ask for the reason, consequence, or distinguishing item |
| no-example-request [B3] | "Give an example of X" | "X is an example of ___", or one card per example |
| no-enumeration [W9-10, B4] | "List all…" in one card | overlapping clozes, or one card per item |
| short-wording [M, W12] | long or oddly worded prompt, memorized by its shape | cut to the minimum words |
| context-free [B6, W16] | only makes sense next to other cards | add a short domain prefix ("Pharm:", "Lin. alg.:") |
| cue-not-giveaway [M] | hint reveals the answer ("herb starting with T") | a cue narrows the options ("herb in a bouquet garni besides parsley and bay") |
| interference [W11] | two similar cards keep getting confused | add a contrast card: "How does X differ from Y?" |
| explain-why [M, W13] | a bare fact with no hook | add a "Why…?" or "What makes… different…?" card |
| orphan [N] | a topic has only one card | suggest 1–2 more angles (reverse, application, cause) |
| understand-first [W1-2] | the card needs understanding the user may lack | flag it; don't just polish it |
| volatile [W18-19] | prices, versions, statistics, laws | add a source and date to the back |
| completionism [M] | trivia the user won't care about | mark `DELETE?` |
| cloze-guessable [M] | clozing a symbol or word that the sentence structure gives away | cloze a meaningful unit |

Examples:
- Yes/no: "Is DNA double-stranded?" → "DNA: what shape do the two strands form together?" → "double helix".
- Example request: "Give an example of a noble gas" → "Noble gases: which one has atomic number 10?" → "Neon".
- Enumeration: "List the 4 DNA bases" → `DNA bases: {{c1::adenine}}, {{c2::thymine}}, {{c3::guanine}}, {{c4::cytosine}}`.

## Math (MathJax) [A-math]
- Inline `\( … \)`, display `\[ … \]`. `$…$` is not rendered.
- Chemistry: `\ce{H2O}` (mhchem is built in).
- Anki's LaTeX-image mode (`[$]…[/$]`, `[$$]…[/$$]`, `[latex]…[/latex]`) needs a
  local TeX install and images generated on the desktop. Use it only if the deck
  already does.
- Cloze + math: `}}` inside the math closes the cloze early.
  `{{c1::\( \frac{1}{x^{2}} \)}}` breaks. Write `\frac{1}{x^{2} }` (space between
  the braces) or `}<!-- -->}`. Clozes inside math also work: `\( {{c1::x^2}} + 1 \)`.
- Cloze the whole expression or a meaningful part, not one symbol that's guessable from its position.
- In the field HTML, `<`, `>` and `&` inside math appear as `&lt;`, `&gt;` and `&amp;`. Leave them as they are.
- Remove editor residue inside math (`<b>`, `<span>`, `<div>`, `&nbsp;`).
- Keep notation consistent within a deck (e.g. `\mathbf{v}` vs `\vec{v}`, `\ln` vs `\log`).
- Fix unbalanced braces, `\left` without `\right`, and words in math without `\text{}`.
- Don't wrap plain words or numbers in math.

## Visuals (only when asked) [W6, W8, Mayer]
- Use the lightest form that carries the idea: a labelled diagram or schematic, or Image Occlusion for labelling tasks.
- Coherence: no decorative clutter.
- Spatial contiguity: put labels on the figure next to what they name.
- Signaling: highlight the one element being tested.
- Redundancy: don't repeat the written answer inside the image.
- On the front, the image must not give the answer away. On the back, it explains.
- Draw an original. Never reproduce copyrighted figures.

## Sources
- [M] Andy Matuschak, *How to write good prompts*, https://andymatuschak.org/prompts/
- [W] Piotr Woźniak, *Twenty rules of formulating knowledge*, https://www.supermemo.com/en/blog/twenty-rules-of-formulating-knowledge
- [B] Soren Bjornstad, *Rules for Designing Precise Anki Cards*, https://controlaltbackspace.org/precise/
- [N] Michael Nielsen, *Augmenting Long-term Memory*, http://augmentingcognition.com/ltm.html
- [A-math] Anki manual, Math & Symbols, https://docs.ankiweb.net/math.html
- [Mayer] R. Mayer, principles for reducing extraneous processing, *Cambridge Handbook of Multimedia Learning*, ch. 12
