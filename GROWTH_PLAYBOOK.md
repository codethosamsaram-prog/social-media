# @code_tho_samsaram growth playbook

Research notes (November 2026) on how trending Reels are built and what makes viewers follow, plus how the factory applies them. Platform-confirmed facts are marked ✅. Everything else comes from creator and marketing blogs, so treat it as a directional pattern, not data.

## What Instagram ranks on

- ✅ **Watch time, likes per reach, sends per reach** are the three signals Adam Mosseri named as the most important for ranking (January 2025). "Sends" means DM shares to a friend.
- ✅ Instagram tells creators to hook in the **first 3 seconds** and to track **View Rate** (the share of viewers who keep watching past 3 s) in Insights.
- Socialinsider's 140K-Reel study puts first-3-second skips at **60–65 %**. Most viewers leave before the hook ends, so the opening frame matters most.
- Each surface (Reels tab, Explore, Feed) ranks separately. Reels over 3 minutes reportedly stop being recommended. Ours are 7–32 s.

## How trending Reels open (first 1.5 s)

| Pattern | Why it works | Factory hook style |
|---|---|---|
| Huge stacked text, one word highlighted | Readable with sound off; the eye lands on the highlighted word | `stack` |
| Terminal / IDE typing | Native to dev content; viewers pause to read, which adds watch time | `terminal` |
| Warning / "stop doing X" | Negativity bias: a threat to avoid beats a gain to chase | `alert` |
| Text-post sticker | Looks like native content, not an ad, so it gets skipped less | `sticker` |
| Kinetic type, one word per beat | Movement on every beat resets attention | `kinetic` |

Hook copy formulas (exactly 3 words), rotated so the feed never repeats an opener:
- **Curiosity gap:** "NOBODY TALKS ABOUT", "GITHUB HIDDEN GEM"
- **Loss aversion:** "STOP WASTING HOURS", "STOP PAYING FOR"
- **Identity:** "SENIORS USE THIS", "JUNIORS DON'T KNOW". Viewers follow accounts that match who they want to be.
- **Specific result:** "XOR KILLS DUPLICATES", "ONE PASS SORT". Specific claims beat vague ones.
- **Save trigger:** "BOOKMARK THIS REPO", "SAVE THIS NOW"

Put the payoff first and cut the intro. Never open on a logo or setup.

## The middle

- Visual change every 1.2–2 s: a cut, zoom, new card or a code line typing in. The "cut every 2–3 s" rule is widely repeated but unproven, so motion that carries meaning beats random cuts.
- Captions are always on. Most viewers watch muted, so on-screen type carries the message. Kinetic typography is the most-cited 2026 motion trend.
- Open loops: tease the result ("watch what XOR does") before showing it.
- Code on screen makes viewers pause and rewatch, which counts as watch time. Dark full-screen IDE was the top comment-rate format in a 40-Reel AI-niche sample.

## How they end

The ending is where followers come from.

| Ending | Psychology | Factory CTA style |
|---|---|---|
| Comment keyword → auto-DM | A small action earns a reward. The comment ranks the Reel, and the DM opens a direct channel with the viewer. | `search`, `comment` |
| "Follow for part N+1" | Zeigarnik effect: an unfinished series is a reason to follow, not just like | `series` |
| "Send this to a dev who needs it" | Directly asks for **sends**, one of the top-3 ranking signals | `share` |
| Loop-back last frame | A seamless replay inflates watch time | (code card ends fully typed, so it reads on replay) |

Only promise what the auto-DM actually delivers. A keyword that doesn't send anything burns the trust of everyone who commented.

## Why every reel now looks different

All 5 seed reels used one template: nebula background, stacked hook, yellow pop captions, search-bar CTA. A feed of identical-looking posts reads as spam, and returning viewers stop seeing anything new.

`storyboard.pick_style` now gives every reel its own:
- **look:** `neon` / `terminal` / `blueprint` / `sunset` / `mono`
- **hook:** `stack` / `terminal` / `alert` / `sticker` / `kinetic`
- **captions:** `pop` / `box` (highlight block) / `clean` (subtitle pill) / `type` (terminal)
- **ending:** `search` / `comment` / `series` / `share`
- **font:** `anton` / `bebas` / `archivo`

Each axis rotates by queue position with a stride coprime to its size, so two consecutive reels never share any of them. Pin any axis on a queue item with `"style": {"look": "terminal", "cta": "share"}`.

## Follower-growth checklist

1. **Series, not one-offs.** Run "O(1) TRICKS · PART N", "GITHUB GEMS · PART N" and similar. A series is the clearest reason to hit follow.
2. **Consistent identity, varied packaging.** Keep the same handle, voice and niche in every reel; vary the look and edit style.
3. **Ask for sends,** not just comments, on every 3rd–4th reel (the `share` ending).
4. **Post twice a day** (09:00 and 19:00 IST in the Actions cron). Every 2 weeks, check which hook style has the best 3-second View Rate and pin it more often.
5. **A/B test hooks:** same body, different first 3 s and on-screen text.
6. **Reply to comments within the first hour.** The auto public reply already does this.
7. **Pin the 3 best reels** to the profile, and write the bio as a promise: "Daily O(1) tricks + AI tools for devs. Comment keywords for code."

## Sources

- [Instagram algorithm 2026: what gets reach, per Adam Mosseri](https://www.zoomsphere.com/blog/instagram-algorithm-2026-what-actually-gets-reach)
- [Instagram ranking signals Meta confirmed](https://www.reeldrop.io/learn/instagram-algorithm)
- [How the Instagram algorithm works, in Instagram's own words](https://keywordseverywhere.com/news/instagram-algorithm-updates/how-the-instagram-algorithm-works/)
- [Reel hooks that retain viewers (2026)](https://fobetmedia.com/instagram-reel-hooks/)
- [Instagram Reels best practices 2026](https://quso.ai/blog/instagram-reels-best-practices)
- [First 3 seconds hook and retention guide](http://npprteam.shop/en/articles/instagram/reels-on-instagram-basic-mechanics-first-3-seconds-and-hold/)
- [I studied 40 viral AI reels (formats, CTA ratios)](https://dev.to/whoffagents/i-studied-40-viral-ai-reels-to-find-what-actually-works-with-real-numbers-m6e)
- [11 editing aesthetics dominating short-form in 2026](https://www.opus.pro/blog/editing-aesthetics-dominating-short-form-2026)
- [Faceless reels in the tech niche](https://fluxnote.io/guides/faceless-instagram-reels-tech-niche)
