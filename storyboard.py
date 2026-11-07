"""Storyboards: turn a queue item into narrated, timed scenes for the Remotion reel.

Formats
  dsa      hook -> problem -> naive way (stamped O(n)) -> animated trace -> code + stamps -> CTA   (20-32 s)
  repo     hook -> repo card -> how it works -> setup demo -> use cases -> CTA                    (20-32 s)
  others   hook -> browser / compare / code scene(s) -> CTA                                          (7-12 s)

A queue item may also carry an explicit "storyboard" list to hand-author any reel.

The DSA visualisations are not drawn by hand: each trick has a tracer that runs the real
algorithm on the example input and records every pointer move, swap and variable change.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable

# Reel length window (seconds) per category.
LENGTHS: dict[str, tuple[float, float]] = {"dsa": (20.0, 34.0), "repo": (20.0, 34.0), "hiring": (14.0, 26.0)}
DEFAULT_LENGTH = (8.0, 15.0)

ACCENTS = {"hiring": "#ff9933", "dsa": "#ff9e64", "repo": "#36f9f6", "ai_tool": "#ff7edb", "dev_tip": "#7aa2f7", "website": "#9ece6a"}

# Caption centre line per scene type (None hides captions: the scene's own text carries it).
CAPTION_Y: dict[str, int | None] = {
    "hook": None, "problem": 1430, "naive": 1430, "visualize": 1520, "code": 1520, "compare": 1450,
    "repo_intro": 1430, "how": 1470, "demo": 1560, "use_cases": 1450, "browser": 1530, "hiring": 1530, "cta": None,
}
MIN_DUR = {
    "hook": 1.5, "problem": 3.0, "naive": 3.0, "visualize": 5.5, "code": 3.2, "compare": 3.4,
    "repo_intro": 3.0, "how": 4.5, "demo": 4.0, "use_cases": 4.0, "browser": 4.0, "hiring": 6.0, "cta": 2.6,
}
TRANSITIONS = ["whip", "zoom", "slide-up", "glitch", "spin", "shutter", "blur", "flash", "iris", "drop"]

C = {"red": "#f7768e", "green": "#9ece6a", "yellow": "#ffe600", "purple": "#bb9af7", "cyan": "#36f9f6", "orange": "#ff9e64"}

Word = tuple[float, float, str]


@dataclass
class Scene:
    type: str
    narration: str
    data: dict[str, Any] = field(default_factory=dict)
    kicker: str | None = None
    transition: str | None = None
    optional: bool = False
    stretchable: bool = False
    # filled in by the pipeline
    start: float = 0.0
    duration: float = 0.0
    voice_len: float = 0.0
    words: list[Word] = field(default_factory=list)

    @property
    def min_dur(self) -> float:
        return MIN_DUR.get(self.type, 2.0)


# ---------------------------------------------------------------------------
# Code tokenising (Pygments -> Tokyo Night hex tokens)
# ---------------------------------------------------------------------------

TOKYO = {
    "fg": "#c0caf5", "comment": "#565f89", "keyword": "#bb9af7", "string": "#9ece6a", "number": "#ff9e64",
    "function": "#7aa2f7", "class": "#2ac3de", "operator": "#89ddff", "punct": "#9aa5ce", "decorator": "#e0af68",
    "tag": "#f7768e", "attr": "#73daca",
}


def _color(ttype: Any) -> str:
    from pygments.token import Comment, Keyword, Name, Number, Operator, Punctuation, String

    for kind, key in ((Comment, "comment"), (Keyword.Constant, "number"), (Keyword, "keyword"),
                      (Name.Decorator, "decorator"), (Name.Function, "function"), (Name.Class, "class"),
                      (Name.Builtin, "class"), (Name.Tag, "tag"), (Name.Attribute, "attr"), (String, "string"),
                      (Number, "number"), (Operator, "operator"), (Punctuation, "punct")):
        if ttype in kind:
            return TOKYO[key]
    return TOKYO["fg"]


def tokenize(snippet: str, language: str, max_lines: int = 12) -> list[list[list[str]]]:
    from pygments import lex
    from pygments.lexers import TextLexer, get_lexer_by_name
    from pygments.util import ClassNotFound

    lexer = None
    for name in (language, {"tsx": "typescript", "jsx": "javascript"}.get(language, "")):
        if name and lexer is None:
            try:
                lexer = get_lexer_by_name(name, stripnl=False, ensurenl=False)
            except ClassNotFound:
                pass
    lines: list[list[list[str]]] = [[]]
    for ttype, value in lex(snippet.expandtabs(4).rstrip(), lexer or TextLexer(stripnl=False, ensurenl=False)):
        for i, part in enumerate(value.split("\n")):
            if i:
                lines.append([])
            if part:
                lines[-1].append([part, _color(ttype)])
    return lines[:max_lines]


def code_chars(lines: list[list[list[str]]]) -> int:
    return sum(len(t) for line in lines for t, _ in line) + len(lines)


# ---------------------------------------------------------------------------
# DSA tracers: run the real algorithm, record each visual step
# ---------------------------------------------------------------------------


def _bits(n: int, width: int) -> str:
    return format(n & ((1 << width) - 1), f"0{width}b")


def trace_xor_single(nums: list[int]) -> tuple[list[dict], str]:
    width = max(3, max(nums).bit_length())
    x, seen, dim = 0, {}, []
    steps = [{"array": nums, "bits": [{"label": "x", "bits": _bits(0, width)}], "note": "x = 0"}]
    for i, n in enumerate(nums):
        x ^= n
        if n in seen:
            dim += [seen.pop(n), i]
        else:
            seen[n] = i
        steps.append({
            "pointers": {"n": i}, "highlight": [i], "dim": list(dim),
            "bits": [{"label": f"n = {n}", "bits": _bits(n, width), "color": C["purple"]},
                     {"label": f"x = {x}", "bits": _bits(x, width)}],
            "note": f"x ^= {n}" + ("   pair cancels!" if i in dim else ""),
        })
    keep = [i for i in range(len(nums)) if i not in dim]
    steps.append({"highlight": keep, "dim": dim, "bits": [{"label": f"x = {x}", "bits": _bits(x, width), "color": C["green"]}],
                  "note": "every pair cancelled to 0", "done": True})
    return steps, f"ANSWER: {x}"


def trace_floyd(nums: list[int]) -> tuple[list[dict], str]:
    slow = fast = nums[0]
    steps = [{"array": nums, "pointers": {"slow": slow, "fast": fast}, "note": "value = index of next node"}]
    while True:
        slow, fast = nums[slow], nums[nums[fast]]
        steps.append({"pointers": {"slow": slow, "fast": fast}, "highlight": [slow, fast],
                      "note": "slow +1 step, fast +2 steps"})
        if slow == fast:
            steps[-1]["note"] = f"they meet at index {slow}"
            break
    slow = nums[0]
    steps.append({"pointers": {"slow": slow, "fast": fast}, "note": "reset slow, both move 1 step"})
    while slow != fast:
        slow, fast = nums[slow], nums[fast]
        steps.append({"pointers": {"slow": slow, "fast": fast}, "highlight": [slow]})
    dup = [i for i, v in enumerate(nums) if v == slow]
    steps.append({"pointers": {"slow": slow, "fast": fast}, "highlight": dup, "note": "cycle entrance = duplicate", "done": True})
    return steps, f"DUPLICATE: {slow}"


def trace_boyer_moore(nums: list[int]) -> tuple[list[dict], str]:
    cand, count = None, 0
    steps = [{"array": nums, "vars": {"candidate": "-", "count": 0}}]
    for i, n in enumerate(nums):
        note = ""
        if count == 0:
            cand, note = n, f"count is 0 -> new candidate {n}"
        count += 1 if n == cand else -1
        steps.append({"pointers": {"i": i}, "highlight": [i], "vars": {"candidate": cand, "count": count},
                      "note": note or ("same -> +1" if n == cand else "different -> -1")})
    steps.append({"highlight": [i for i, v in enumerate(nums) if v == cand], "vars": {"candidate": cand, "count": count},
                  "note": "the majority always survives", "done": True})
    return steps, f"MAJORITY: {cand}"


def trace_xor_missing(nums: list[int]) -> tuple[list[dict], str]:
    x = len(nums)
    steps = [{"array": nums, "vars": {"x": x}, "note": f"start with n = {x}"}]
    for i, n in enumerate(nums):
        x ^= i ^ n
        steps.append({"pointers": {"i": i}, "highlight": [i], "vars": {"x": x}, "note": f"x ^= {i} ^ {n}"})
    steps.append({"vars": {"x": x}, "note": "everything else cancelled", "done": True})
    return steps, f"MISSING: {x}"


def trace_negate(nums: list[int]) -> tuple[list[dict], str]:
    a, out = list(nums), []
    steps = [{"array": list(a), "vars": {"out": "[]"}, "note": "value v -> slot v - 1"}]
    for k in range(len(a)):
        n = a[k]
        i = abs(n) - 1
        if a[i] < 0:
            out.append(abs(n))
            note = f"slot {i} already negative -> {abs(n)} is a dup!"
        else:
            note = f"flip slot {i} negative"
        a[i] = -a[i]
        steps.append({"array": list(a), "pointers": {"k": k, "slot": i}, "highlight": [i],
                      "vars": {"out": str(out)}, "note": note})
    steps.append({"array": list(a), "vars": {"out": str(out)}, "note": "no extra memory used", "done": True})
    return steps, f"DUPLICATES: {', '.join(map(str, out))}"


def trace_dutch(nums: list[int]) -> tuple[list[dict], str]:
    a = list(nums)
    lo = mid = 0
    hi = len(a) - 1
    steps = [{"array": list(a), "pointers": {"lo": lo, "mid": mid, "hi": hi}}]
    while mid <= hi:
        swap, note = None, ""
        if a[mid] == 0:
            a[lo], a[mid] = a[mid], a[lo]
            swap, note = (lo, mid), "0 -> swap to lo"
            lo += 1
            mid += 1
        elif a[mid] == 1:
            note = "1 -> just move on"
            mid += 1
        else:
            a[mid], a[hi] = a[hi], a[mid]
            swap, note = (mid, hi), "2 -> swap to hi"
            hi -= 1
        steps.append({"array": list(a), "pointers": {"lo": lo, "mid": mid, "hi": hi},
                      "swap": list(swap) if swap else None, "highlight": list(swap) if swap else [], "note": note})
    steps.append({"array": list(a), "note": "one pass, in place", "done": True})
    return steps, "SORTED IN 1 PASS"


def trace_kadane(nums: list[int]) -> tuple[list[dict], str]:
    best = cur = nums[0]
    cur_start, best_range = 0, (0, 0)
    steps = [{"array": nums, "pointers": {"i": 0}, "highlight": [0], "vars": {"cur": cur, "best": best}}]
    for i in range(1, len(nums)):
        n = nums[i]
        if n > cur + n:
            cur, cur_start, note = n, i, f"{n} alone beats the run -> start fresh"
        else:
            cur, note = cur + n, f"extend the run -> {cur + n}"
        if cur > best:
            best, best_range = cur, (cur_start, i)
            note += "   new best!"
        steps.append({"pointers": {"i": i}, "highlight": list(range(cur_start, i + 1)),
                      "vars": {"cur": cur, "best": best}, "note": note})
    steps.append({"highlight": list(range(best_range[0], best_range[1] + 1)), "vars": {"cur": cur, "best": best},
                  "note": "best run found in one pass", "done": True})
    return steps, f"MAX SUM: {best}"


def trace_pow2(_: list[int]) -> tuple[list[dict], str]:
    steps: list[dict] = []
    for n in (8, 6):
        rows = [{"label": f"n = {n}", "bits": _bits(n, 4), "color": C["cyan"]}]
        steps.append({"bits": list(rows), "note": f"{n} in binary"})
        rows.append({"label": f"n-1 = {n - 1}", "bits": _bits(n - 1, 4), "color": C["purple"]})
        steps.append({"bits": list(rows), "note": "subtract 1: lower bits flip"})
        res = n & (n - 1)
        rows.append({"label": "n & (n-1)", "bits": _bits(res, 4), "color": C["green"] if res == 0 else C["red"]})
        steps.append({"bits": list(rows), "note": "= 0 -> power of two" if res == 0 else "!= 0 -> not a power of two"})
    steps[-1]["done"] = True
    return steps, "O(1) CHECK"


def trace_reverse(nums: list[int]) -> tuple[list[dict], str]:
    n = len(nums)
    links = ["→"] * (n - 1)
    prev, curr = -1, 0
    steps = [{"array": nums, "links": list(links), "pointers": {"prev": prev, "curr": curr}, "note": "prev = null"}]
    while curr < n:
        nxt = curr + 1
        if curr > 0:
            links[curr - 1] = "←"
        steps.append({"links": list(links), "pointers": {"prev": prev, "curr": curr, "nxt": nxt}, "highlight": [curr],
                      "note": f"{nums[curr]}.next = " + ("null" if prev < 0 else str(nums[prev]))})
        prev, curr = curr, nxt
    steps.append({"links": list(links), "pointers": {"prev": prev, "curr": curr}, "highlight": [prev],
                  "note": "curr is null -> prev is the new head", "done": True})
    return steps, f"NEW HEAD: {nums[-1]}"


TRACERS: dict[str, Callable[[list[int]], tuple[list[dict], str]]] = {
    "xor_single": trace_xor_single, "floyd": trace_floyd, "boyer_moore": trace_boyer_moore,
    "xor_missing": trace_xor_missing, "negate": trace_negate, "dutch": trace_dutch,
    "kadane": trace_kadane, "pow2": trace_pow2, "reverse": trace_reverse,
}

DSA_TRICKS: dict[str, dict[str, Any]] = {
    "xor_single": {
        "topic": "Solve array duplicates in O(1) space with Bitwise XOR", "hook": "XOR KILLS DUPLICATES",
        "number": 136, "title": "Single Number", "difficulty": "Easy",
        "statement": "Every number appears twice except one. Find it with O(1) extra space.",
        "input": [4, 1, 2, 1, 2], "mode": "array", "naive": ("HASH SET", "O(n) SPACE"), "viz_title": "XOR EVERYTHING",
        "link": "https://leetcode.com/problems/single-number/", "filename": "single_number.py", "focus": [3],
        "snippet": "def single_number(nums):\n    x = 0\n    for n in nums:\n        x ^= n   # a ^ a = 0\n    return x",
        "narration": {
            "hook": "Stop using a hash set for this.",
            "problem": "LeetCode 136. Every number appears twice, except one. Find the loner using constant space.",
            "naive": "The obvious fix is a hash set. That costs O of n memory.",
            "visualize": "Instead, XOR every number together. A number XOR itself is zero, so every pair cancels out, and only four survives.",
            "code": "Five lines. One variable. O of n time, O of one space.",
        },
    },
    "floyd": {
        "topic": "Find the duplicate number in O(1) space (Floyd's cycle detection)", "hook": "NO HASHSET NEEDED",
        "number": 287, "title": "Find the Duplicate", "difficulty": "Medium",
        "statement": "n + 1 numbers in the range 1 to n. Find the duplicate without modifying the array.",
        "input": [1, 3, 4, 2, 2], "mode": "array", "naive": ("HASH SET", "O(n) SPACE"), "viz_title": "TORTOISE & HARE",
        "link": "https://leetcode.com/problems/find-the-duplicate-number/", "filename": "find_duplicate.py", "focus": [3, 4],
        "snippet": "def find_duplicate(nums):\n    slow = fast = nums[0]\n    while True:\n        slow = nums[slow]\n        fast = nums[nums[fast]]\n        if slow == fast:\n            break\n    slow = nums[0]\n    while slow != fast:\n        slow, fast = nums[slow], nums[fast]\n    return slow",
        "narration": {
            "hook": "You don't need a hash set here.",
            "problem": "LeetCode 287. Find the duplicate number without modifying the array, in constant space.",
            "naive": "A hash set solves it, but that's O of n extra memory.",
            "visualize": "Treat every value as a pointer to the next index. The duplicate creates a cycle. Move slow one step and fast two steps until they meet, then reset slow and walk both to the cycle entrance.",
            "code": "Floyd's cycle detection. O of n time, O of one space.",
        },
    },
    "boyer_moore": {
        "topic": "Majority element in O(1) space (Boyer-Moore voting)", "hook": "ONE VARIABLE WINS",
        "number": 169, "title": "Majority Element", "difficulty": "Easy",
        "statement": "Find the element that appears more than n / 2 times.",
        "input": [2, 2, 1, 1, 1, 2, 2], "mode": "array", "naive": ("HASH MAP COUNTS", "O(n) SPACE"), "viz_title": "BOYER-MOORE VOTE",
        "link": "https://leetcode.com/problems/majority-element/", "filename": "majority.py", "focus": [3, 4, 5],
        "snippet": "def majority(nums):\n    cand, count = None, 0\n    for n in nums:\n        if count == 0:\n            cand = n\n        count += 1 if n == cand else -1\n    return cand",
        "narration": {
            "hook": "One variable beats a hash map.",
            "problem": "LeetCode 169. Find the element that appears more than half the time.",
            "naive": "Counting with a hash map works, but costs O of n memory.",
            "visualize": "Keep one candidate and a counter. Same number, plus one. Different, minus one. When the count hits zero, pick a new candidate. The majority always survives.",
            "code": "Boyer Moore voting. O of n time, O of one space.",
        },
    },
    "xor_missing": {
        "topic": "Missing number in O(1) space with XOR", "hook": "XOR FINDS MISSING",
        "number": 268, "title": "Missing Number", "difficulty": "Easy",
        "statement": "The array holds every number from 0 to n except one. Find the missing number.",
        "input": [3, 0, 1], "mode": "array", "naive": ("SORT OR SET", "O(n) SPACE"), "viz_title": "XOR INDEX & VALUE",
        "link": "https://leetcode.com/problems/missing-number/", "filename": "missing_number.py", "focus": [3],
        "snippet": "def missing_number(nums):\n    x = len(nums)\n    for i, n in enumerate(nums):\n        x ^= i ^ n\n    return x",
        "narration": {
            "hook": "Find the missing number with XOR.",
            "problem": "LeetCode 268. The array holds every number from zero to n, except one. Find the missing one.",
            "naive": "Most people sort it or use a set. That's extra time or extra memory.",
            "visualize": "Start with n. XOR in every index and every value. Each number that appears twice cancels out, and the missing one is all that's left.",
            "code": "Four lines. O of n time, O of one space.",
        },
    },
    "negate": {
        "topic": "Find all duplicates in O(1) space (index negation trick)", "hook": "NEGATE THE INDEX",
        "number": 442, "title": "Find All Duplicates", "difficulty": "Medium",
        "statement": "Values are in the range 1 to n. Return every number that appears twice, using no extra space.",
        "input": [4, 3, 2, 7, 8, 2, 3, 1], "mode": "array", "naive": ("HASH SET", "O(n) SPACE"), "viz_title": "FLIP THE SIGN",
        "link": "https://leetcode.com/problems/find-all-duplicates-in-an-array/", "filename": "find_duplicates.py", "focus": [4, 5, 6],
        "snippet": "def find_duplicates(nums):\n    out = []\n    for n in nums:\n        i = abs(n) - 1\n        if nums[i] < 0:\n            out.append(abs(n))\n        nums[i] = -nums[i]\n    return out",
        "narration": {
            "hook": "Use the array as its own hash set.",
            "problem": "LeetCode 442. Values are between one and n. Find every number that appears twice, with no extra space.",
            "naive": "A hash set would do it, but that's O of n extra memory.",
            "visualize": "Use each value as an index and flip that slot negative. If the slot is already negative, you've seen that number before. That's a duplicate.",
            "code": "The array is its own hash set. O of one extra space.",
        },
    },
    "dutch": {
        "topic": "Sort colors in one pass, O(1) space (Dutch national flag)", "hook": "ONE PASS SORT",
        "number": 75, "title": "Sort Colors", "difficulty": "Medium",
        "statement": "Sort an array of 0s, 1s and 2s in place, in a single pass.",
        "input": [2, 0, 2, 1, 1, 0], "mode": "array", "naive": ("SORT() OR COUNT", "2 PASSES"), "viz_title": "THREE POINTERS",
        "link": "https://leetcode.com/problems/sort-colors/", "filename": "sort_colors.py", "focus": [4, 7, 9],
        "snippet": "def sort_colors(a):\n    lo = mid = 0\n    hi = len(a) - 1\n    while mid <= hi:\n        if a[mid] == 0:\n            a[lo], a[mid] = a[mid], a[lo]\n            lo += 1; mid += 1\n        elif a[mid] == 1:\n            mid += 1\n        else:\n            a[mid], a[hi] = a[hi], a[mid]\n            hi -= 1",
        "narration": {
            "hook": "Sort this array in one pass.",
            "problem": "LeetCode 75. Sort an array of zeros, ones and twos, in place, in a single pass.",
            "naive": "Counting sort needs two passes, and calling sort is n log n.",
            "visualize": "Use three pointers: low, mid and high. Zero? Swap it to low. One? Just move on. Two? Swap it to high. Done in one pass.",
            "code": "The Dutch national flag algorithm. O of n time, O of one space.",
        },
    },
    "kadane": {
        "topic": "Maximum subarray in O(1) space (Kadane's algorithm)", "hook": "KADANE IN SECONDS",
        "number": 53, "title": "Maximum Subarray", "difficulty": "Medium",
        "statement": "Find the contiguous subarray with the largest sum.",
        "input": [-2, 1, -3, 4, -1, 2, 1, -5, 4], "mode": "array", "naive": ("EVERY SUBARRAY", "O(n²) TIME"), "viz_title": "EXTEND OR RESTART",
        "link": "https://leetcode.com/problems/maximum-subarray/", "filename": "kadane.py", "focus": [3, 4],
        "snippet": "def max_subarray(nums):\n    best = cur = nums[0]\n    for n in nums[1:]:\n        cur = max(n, cur + n)\n        best = max(best, cur)\n    return best",
        "narration": {
            "hook": "Max subarray in one loop.",
            "problem": "LeetCode 53. Find the contiguous subarray with the largest sum.",
            "naive": "Checking every subarray is O of n squared. Way too slow.",
            "visualize": "Walk the array once. At each number, either extend the current run or start fresh, whichever is bigger. Keep the best sum you've seen. The answer is six.",
            "code": "Kadane's algorithm. O of n time, O of one space.",
        },
    },
    "pow2": {
        "topic": "Power of two in O(1) with one bitwise AND", "hook": "ONE LINE CHECK",
        "number": 231, "title": "Power of Two", "difficulty": "Easy",
        "statement": "Return true if n is a power of two. Can you do it without loops?",
        "input": [], "mode": "bits", "naive": ("DIVIDE BY 2 LOOP", "O(log n)"), "viz_title": "n & (n - 1)",
        "link": "https://leetcode.com/problems/power-of-two/", "filename": "power_of_two.py", "focus": [1],
        "snippet": "def is_power_of_two(n: int) -> bool:\n    return n > 0 and n & (n - 1) == 0",
        "narration": {
            "hook": "Check a power of two in one line.",
            "problem": "LeetCode 231. Is this number a power of two? No loops allowed.",
            "naive": "Dividing by two in a loop works, but it's O of log n.",
            "visualize": "A power of two has exactly one set bit. Subtract one and every bit below it flips. AND them together and you get zero. Six fails the test.",
            "code": "One line. Constant time.",
        },
        "stamps": ["O(1) TIME", "1 LINE"],
    },
    "reverse": {
        "topic": "Reverse a linked list in place, O(1) space", "hook": "THREE POINTERS ONLY",
        "number": 206, "title": "Reverse Linked List", "difficulty": "Easy",
        "statement": "Reverse a singly linked list in place.",
        "input": [1, 2, 3, 4, 5], "mode": "list", "naive": ("COPY TO ARRAY", "O(n) SPACE"), "viz_title": "FLIP EVERY ARROW",
        "link": "https://leetcode.com/problems/reverse-linked-list/", "filename": "reverse_list.py", "focus": [4],
        "snippet": "def reverse(head):\n    prev, curr = None, head\n    while curr:\n        nxt = curr.next\n        curr.next = prev\n        prev, curr = curr, nxt\n    return prev",
        "narration": {
            "hook": "The interview classic, in three pointers.",
            "problem": "LeetCode 206. Reverse a linked list, in place.",
            "naive": "Copying values into an array works, but costs O of n memory.",
            "visualize": "Keep three pointers: previous, current and next. Flip one arrow per step, then move everything forward. When current hits null, previous is your new head.",
            "code": "O of n time, O of one space.",
        },
    },
}

# ---------------------------------------------------------------------------
# Storyboard builders
# ---------------------------------------------------------------------------


def cta_scene(item: dict[str, Any], handle: str) -> Scene:
    thing = "code" if item["category"] == "dsa" else "link"
    spoken = item.get("keyword_spoken") or item["keyword"].lower()
    style = item.get("_style") or {}
    series = style.get("series")
    ending = style.get("cta", "search")
    if ending == "series" and series:
        nxt = int(series.rsplit(" ", 1)[-1]) + 1
        line = f"Comment {spoken} for the {thing}, and follow for part {nxt}."
    elif ending == "share":
        line = f"Send this to a dev friend, and comment {spoken} for the {thing}."
    elif ending == "triple":
        what = "all three links" if item.get("links") else f"the {thing}"
        line = f"Follow, like, and comment {spoken}, and I'll DM you {what}."
    else:
        line = f"Comment {spoken} and I'll DM you the {thing}."
    return Scene("cta", line, {"keyword": item["keyword"], "thing": "links" if item.get("links") else thing,
                               "handle": handle, "series": series},
                 transition="zoom")


def hook_scene(item: dict[str, Any], narration: str, kicker: str | None) -> Scene:
    return Scene("hook", narration, {"words": item["hook"].split()}, kicker=kicker, transition="none")


def code_data(snippet: str, language: str, filename: str, focus: list[int], stamps: list[str] | None = None) -> dict[str, Any]:
    return {"filename": filename, "lines": tokenize(snippet, language), "focusLines": focus, "stampTexts": stamps or []}


def dsa_storyboard(item: dict[str, Any], handle: str) -> list[Scene]:
    key = (item.get("dsa") or {}).get("trick", "xor_single")
    trick = DSA_TRICKS[key]
    n = trick["narration"]
    steps, result = TRACERS[key](list(trick["input"]))
    code = item.get("code") or {}
    snippet = code.get("snippet") if (item.get("dsa") or {}).get("use_item_code") else trick["snippet"]
    return [
        hook_scene(item, n["hook"], "LEETCODE TRICK"),
        Scene("problem", n["problem"], {"source": "LeetCode", "number": trick["number"], "title": trick["title"],
                                         "difficulty": trick["difficulty"], "statement": trick["statement"], "example": trick["input"]},
              transition="whip"),
        Scene("naive", n["naive"], {"label": trick["naive"][0], "items": trick["input"][:6] or [8, 4, 2, 1], "cost": trick["naive"][1]},
              kicker="THE OBVIOUS WAY", transition="glitch", optional=True),
        Scene("visualize", n["visualize"], {"title": trick["viz_title"], "mode": trick["mode"], "steps": steps, "result": result},
              kicker="THE O(1) TRICK", transition="zoom", stretchable=True),
        Scene("code", n["code"], code_data(snippet or trick["snippet"], "python", trick["filename"], trick["focus"],
                                           trick.get("stamps") or ["O(n) TIME", "O(1) SPACE"]) | {"title": "THE CODE"},
              kicker=f"LEETCODE {trick['number']}", transition="slide-up"),
        cta_scene(item, handle),
    ]


def _stars_spoken(stars: int) -> str:
    if stars >= 1000:
        return f"{round(stars / 1000):,} thousand"
    return f"{stars:,}"


def repo_storyboard(item: dict[str, Any], handle: str) -> list[Scene]:
    repo = item.get("repo") or {}
    owner, _, name = (repo.get("full_name") or "owner/repo").partition("/")
    narr = repo.get("narration") or {}
    stars = int(repo.get("stars") or 0)
    desc = repo.get("description") or item["topic"]
    spoken_name = re.sub(r"[-_]+", " ", name)
    pitch = (repo.get("pitch") or desc).rstrip(".")
    intro = narr.get("intro") or (
        f"{spoken_name} has {_stars_spoken(stars)} stars on GitHub. {pitch}." if stars else f"Meet {spoken_name}. {pitch}."
    )
    how = repo.get("how") or []
    cases = repo.get("use_cases") or []
    scenes = [
        hook_scene(item, narr.get("hook") or "This GitHub repo is blowing up right now.", "GITHUB TRENDING"),
        Scene("repo_intro", intro, {"owner": owner, "name": name, "description": desc, "stars": stars,
                                    "language": repo.get("language"),
                                    "badge": f"+{repo['stars_today']:,} stars today" if repo.get("stars_today") else "Trending on GitHub"},
              transition="zoom"),
    ]
    if how:
        scenes.append(Scene("how", narr.get("how") or "Here's how it works. " + " Then ".join(s["say"] for s in how if s.get("say")),
                            {"title": "HOW IT WORKS", "steps": how}, transition="whip", stretchable=True))
    if repo.get("install"):
        demo_code = None
        if repo.get("demo_code"):
            dc = repo["demo_code"]
            demo_code = code_data(dc["snippet"], dc.get("language", "python"), dc.get("filename", "main.py"), dc.get("focus", []))
        scenes.append(Scene("demo", narr.get("demo") or "Setup is a single command.",
                            {"install": repo["install"], "output": repo.get("output") or [], "code": demo_code},
                            kicker="SETUP", transition="slide-up", stretchable=True))
    if len(cases) >= 2:
        titles = [c["title"].lower() for c in cases[:3]]
        default = "Use it to " + (", ".join(titles[:-1]) + ", or " + titles[-1] if len(titles) > 2 else " or ".join(titles)) + "."
        scenes.append(Scene("use_cases", narr.get("use_cases") or default, {"title": "USE CASES", "cards": cases[:3]},
                            transition="glitch", stretchable=True))
    scenes.append(cta_scene(item, handle))
    return scenes


def generic_storyboard(item: dict[str, Any], handle: str) -> list[Scene]:
    """ai_tool / dev_tip / website without a hand-written storyboard."""
    body = item["script"].strip()
    first, _, rest = body.partition(". ")
    browser = item.get("browser")
    if item["category"] == "ai_tool" and browser:
        mid = Scene("browser", rest or body, {"url": browser["url"], "prompt": browser.get("prompt"), "mock": browser.get("mock", "landing"),
                                              "headline": browser.get("headline", ""), "bullets": browser.get("bullets", []),
                                              "query": browser.get("query", "")}, transition="zoom", stretchable=True)
    else:
        code = item["code"]
        mid = Scene("code", rest or body, code_data(code["snippet"], code["language"], code["filename"], code.get("focus", []))
                    | {"title": item.get("code_title", "THE TRICK")}, transition="zoom", stretchable=True)
    return [hook_scene(item, first + ".", None), mid, cta_scene(item, handle)]


def hiring_storyboard(item: dict[str, Any], handle: str) -> list[Scene]:
    """hook (names the 3 companies) -> 3 company cards, one per sentence -> follow/like/comment CTA."""
    companies = item["hiring"]["companies"][:3]
    body = item["script"].strip()
    first, _, rest = body.partition(". ")
    cards = [{k: c.get(k) for k in ("name", "domain", "color", "roles", "fresh", "top_role", "cities", "logo")} for c in companies]
    mid = Scene("hiring", rest or body, {"title": "HIRING IN INDIA", "companies": cards}, kicker="REAL OPENINGS",
                transition="zoom", stretchable=True)
    return [hook_scene(item, first + ".", "HIRING ALERT"), mid, cta_scene(item, handle)]


def from_spec(item: dict[str, Any], handle: str) -> list[Scene]:
    scenes: list[Scene] = []
    for spec in item["storyboard"]:
        data = dict(spec.get("data") or {})
        kind = spec["type"]
        if kind == "hook":
            scenes.append(hook_scene(item, spec["narration"], spec.get("kicker")))
            continue
        if kind == "code":
            code = item["code"]
            data = code_data(data.get("snippet", code["snippet"]), data.get("language", code["language"]),
                             data.get("filename", code["filename"]), data.get("focus", []), data.get("stamps")) | {"title": data.get("title", "THE CODE")}
        scenes.append(Scene(kind, spec.get("narration", ""), data, kicker=spec.get("kicker"), transition=spec.get("transition"),
                            optional=spec.get("optional", False), stretchable=spec.get("stretchable", kind in {"browser", "compare", "how"})))
    if not scenes or scenes[-1].type != "cta":
        scenes.append(cta_scene(item, handle))
    return scenes


def spoken_opening(hook: Scene, day: int | None, is_dsa: bool) -> None:
    """User's rule for every reel: open on the interesting line, then say the day number.
    DSA adds the interview framing, and the problem scene follows straight on."""
    line = hook.narration.strip()
    if line and line[-1] not in ".!?":
        line += "."
    parts = [line, f"Day {day}." if day else ""]
    if is_dsa:
        parts.append("Imagine you get this question in your interview.")
        hook.kicker = "CAN YOU SOLVE IT?"
    hook.narration = " ".join(p for p in parts if p)


def build(item: dict[str, Any], handle: str) -> list[Scene]:
    if item.get("storyboard"):
        scenes = from_spec(item, handle)
    elif item["category"] == "dsa":
        scenes = dsa_storyboard(item, handle)
    elif item["category"] == "repo":
        scenes = repo_storyboard(item, handle)
    elif item["category"] == "hiring":
        scenes = hiring_storyboard(item, handle)
    else:
        scenes = generic_storyboard(item, handle)
    if scenes[0].type == "hook":
        spoken_opening(scenes[0], item.get("_day"), item["category"] == "dsa")
    order =(item.get("_style") or {}).get("transitions") or TRANSITIONS
    for i, s in enumerate(scenes):
        # The style's shuffled order wins over format defaults; a hand-authored storyboard keeps its own.
        if s.transition is None or (s.transition != "none" and item.get("_style") and not item.get("storyboard")):
            s.transition = order[i % len(order)]
    return scenes


def length_window(item: dict[str, Any]) -> tuple[float, float]:
    return LENGTHS.get(item["category"], DEFAULT_LENGTH)


# ---------------------------------------------------------------------------
# Layout: timed props for Remotion + SFX cues, once durations and words are known
# ---------------------------------------------------------------------------


def _clean(w: str) -> str:
    return re.sub(r"[^a-z0-9()]", "", w.lower())


def cue(scene: Scene, prefixes: list[str], default: float, after: float = 0.0) -> float:
    """Local time of the first narrated word starting with any prefix (after `after`)."""
    for start, _, text in scene.words:
        local = start - scene.start
        if local >= after and any(_clean(text).startswith(p) for p in prefixes if p):
            return max(0.0, local - 0.05)
    return default


def spread(n: int, start: float, end: float) -> list[float]:
    if n <= 1:
        return [start]
    step = (end - start) / (n - 1)
    return [start + i * step for i in range(n)]


def _cue_words(text: str) -> list[str]:
    stop = {"the", "a", "an", "your", "you", "it", "to", "and", "of", "in", "for", "with", "auto", "any"}
    words = [_clean(w) for w in text.split()]
    return [w[:5] for w in words if w and w not in stop][:1]


def layout(scene: Scene) -> tuple[dict[str, Any], list[tuple[float, str, float]], list[float]]:
    """Returns (props for this scene, [(abs time, sfx name, gain)], [abs impact times])."""
    d, s0 = scene.duration, scene.start
    data = dict(scene.data)
    sfx: list[tuple[float, str, float]] = []
    impacts: list[float] = []

    def at(local: float, name: str, gain: float) -> None:
        sfx.append((s0 + local, name, gain))

    def typing(span: tuple[float, float], gain: float = 0.1) -> None:
        t = span[0]
        k = 0
        while t < span[1]:
            at(t, "click", gain * (0.75 + 0.5 * ((k * 7919) % 10) / 10))
            t += 0.045 + ((k * 104729) % 5) * 0.008
            k += 1

    kind = scene.type
    if kind == "hook":
        data["wordTimes"] = [0.03, 0.27, 0.51][: len(data["words"])]
        cues = data.pop("cues", None)
        if cues:  # each on-screen word lands as it is spoken
            data["wordTimes"] = [round(cue(scene, c, dflt), 3) for c, dflt in zip(cues, data["wordTimes"])]
        # Voice only under the hook: no per-word hits, that was the "dum dum dum" opening.
        if data["wordTimes"]:
            impacts.append(s0 + data["wordTimes"][-1])
        data.setdefault("stock", None)

    elif kind == "problem":
        data["exampleAt"] = [1.0 + i * 0.1 for i in range(len(data["example"]))]
        for t in data["exampleAt"]:
            at(t, "tick", 0.18)

    elif kind == "naive":
        data["itemTimes"] = [0.55 + i * 0.2 for i in range(len(data["items"]))]
        for t in data["itemTimes"]:
            at(t + 0.2, "pop", 0.18)
        floor = data["itemTimes"][-1] + 0.4
        data["stampAt"] = max(floor, cue(scene, ["o(", "o", "two", "way"], d * 0.62, after=floor))
        data["stampAt"] = min(data["stampAt"], d - 0.6)
        at(data["stampAt"], "impact", 0.6)
        impacts.append(s0 + data["stampAt"])

    elif kind == "visualize":
        steps = [dict(st) for st in data["steps"]]
        times = spread(len(steps), 0.6, max(1.2, d - 1.1))
        for st, t in zip(steps, times):
            st["at"] = round(t, 3)
            at(t, "chime" if st.get("done") else "tick", 0.45 if st.get("done") else 0.22)
            if st.get("done"):
                impacts.append(s0 + t)
        data["steps"] = steps

    elif kind in ("code", "demo"):
        if kind == "demo":
            cmd = data["install"]
            data["installTyping"] = [0.35, 0.35 + min(1.6, len(cmd) * 0.045)]
            typing(tuple(data["installTyping"]))
            out_at = data["installTyping"][1] + 0.3
            data["output"] = [{"text": text, "at": round(out_at + i * 0.22, 3)} for i, text in enumerate(data.get("output", []))]
            for o in data["output"]:
                at(o["at"], "tick", 0.12)
            data["codeAt"] = round((data["output"][-1]["at"] if data["output"] else data["installTyping"][1]) + 0.45, 3)
            code = data.get("code")
            if code:
                at(data["codeAt"], "whoosh", 0.25)
                begin = data["codeAt"] + 0.35
                end = begin + min(max(1.0, d - begin - 1.2), code_chars(code["lines"]) / 55)
                code |= {"typing": [round(begin, 3), round(end, 3)], "focusAt": round(end + 0.25, 3) if code["focusLines"] else None, "stamps": []}
                code.pop("stampTexts", None)
                typing((begin, end), 0.08)
            data["code"] = code
        else:
            begin = 0.35
            end = begin + min(d * 0.5, code_chars(data["lines"]) / 50)
            focus_at = round(end + 0.25, 3) if data["focusLines"] else None
            stamps = data.pop("stampTexts", [])
            stamp_times = spread(len(stamps), max(end + 0.6, d - 1.4), d - 0.75) if stamps else []
            colors = [C["cyan"], C["green"], C["yellow"]]
            code = {k: data.pop(k) for k in ("filename", "lines", "focusLines")}
            code |= {"typing": [begin, round(end, 3)], "focusAt": focus_at,
                     "stamps": [{"text": t, "at": round(a, 3), "color": colors[i % 3]} for i, (t, a) in enumerate(zip(stamps, stamp_times))]}
            data["code"] = code
            typing((begin, end))
            if focus_at:
                at(focus_at, "pop", 0.3)
            for a in stamp_times:
                at(a, "impact", 0.55)
                impacts.append(s0 + a)

    elif kind == "compare":
        rows = data["rows"]
        for row, t in zip(rows, spread(len(rows), 0.5, max(0.6, d / 2))):
            row["at"] = round(t, 3)
            at(t, "riser", 0.25)
            at(t + 1.5, "pop", 0.3)

    elif kind == "repo_intro":
        at(0.05, "whoosh", 0.3)
        at(1.9, "chime", 0.35)

    elif kind in ("how", "use_cases"):
        key = "steps" if kind == "how" else "cards"
        items = [dict(x) for x in data[key]]
        defaults = spread(len(items), 0.45, max(0.6, d - 1.3))
        last = 0.0
        for item_, default in zip(items, defaults):
            t = cue(scene, [_clean(c)[:5] for c in item_.get("cue", "").split()] or _cue_words(item_["title"]), default, after=last + 0.3)
            t = min(max(t, last + 0.35 if last else 0.35), d - 0.8)
            item_["at"] = round(t, 3)
            item_.pop("cue", None)
            item_.pop("say", None)
            last = t
            at(t, "pop" if kind == "how" else "whoosh", 0.3)
        data[key] = items

    elif kind == "browser":
        url = data["url"]
        data["urlTyping"] = [0.3, 0.3 + min(1.0, len(url) * 0.05)]
        typing(tuple(data["urlTyping"]))
        p_text = data.get("prompt") or data.get("query") or ""
        p_start = data["urlTyping"][1] + 0.3
        data["promptTyping"] = [p_start, p_start + min(1.8, len(p_text) * 0.04)] if p_text else [p_start, p_start]
        if p_text:
            typing(tuple(data["promptTyping"]), 0.08)
        data["mockAt"] = round(data["promptTyping"][1] + 0.3, 3)
        at(data["mockAt"], "pop", 0.35)
        bullets = data.get("bullets") or []
        times = spread(len(bullets), data["mockAt"] + 0.35, max(data["mockAt"] + 0.4, d - 1.0))
        data["bullets"] = [{"text": b if isinstance(b, str) else b["text"], "at": round(t, 3)} for b, t in zip(bullets, times)]
        for t in times:
            at(t, "tick", 0.2)
        data["prompt"] = data.get("prompt")
        data["query"] = data.get("query") or ""
        data["headline"] = data.get("headline") or ""

    elif kind == "hiring":
        cards = data.get("companies") or []
        fallback = spread(len(cards), 0.35, max(0.4, d - 1.6))
        t_prev = 0.0
        for c, dflt in zip(cards, fallback):
            first = _clean(c["name"].split()[0])[:5]
            c["at"] = round(max(t_prev, cue(scene, [first], dflt, after=t_prev)), 3)
            t_prev = c["at"] + 0.3
            at(c["at"], "pop", 0.4)
            at(c["at"] + 0.45, "tick", 0.25)

    elif kind == "cta":
        data["bubbleAt"] = 0.25
        data["followAt"] = round(min(d - 0.8, 1.35), 3)
        at(-0.9, "riser", 0.3)
        at(data["bubbleAt"], "pop", 0.4)
        typing((0.45, 0.45 + len(data["keyword"]) * 0.06), 0.12)
        at(data["followAt"], "chime", 0.35)

    if scene.transition in TRANSITIONS and s0 > 0:
        at(-0.16, "whoosh", 0.45)
    if scene.transition in ("zoom", "glitch", "flash", "drop") and s0 > 0:
        at(0.0, "impact", 0.2)

    props = {
        "id": f"s{int(s0 * 1000)}-{kind}",
        "type": kind,
        "start": round(s0, 3),
        "duration": round(d, 3),
        "transition": scene.transition or "whip",
        "captionY": CAPTION_Y.get(kind, 1420),
        **({"kicker": scene.kicker} if scene.kicker else {}),
        **data,
    }
    return props, sfx, impacts


EMPHASIS_RE = re.compile(r"^(\d[\d,.]*|zero|one|two|three|five|never|stop|free|fast|faster|instant|secret|hidden|best|"
                         r"only|every|constant|magic|huge|thousand|million|viral|real|trick|wrong|hiring|interview|cancels?|survives?)$")
EMPHASIS_GAP, CAMERA_MAX_HOLD = 1.3, 2.8


def emphasis(scenes: list[Scene]) -> list[dict[str, Any]]:
    """Moments the edit reacts to. strong = a word worth a burst; every moment moves the camera, and the
    camera never holds longer than CAMERA_MAX_HOLD even in a sentence with nothing to stress."""
    out: list[dict[str, Any]] = []
    last = -10.0
    for scene in scenes:
        for start, _, text in scene.words:
            word = re.sub(r"[^a-z0-9,.]", "", text.lower()).strip(",.")
            strong = bool(EMPHASIS_RE.match(word))
            if start - last >= EMPHASIS_GAP and (strong or (start - last >= CAMERA_MAX_HOLD and len(word) >= 4)):
                out.append({"t": round(start, 3), "strong": strong})
                last = start
    return out


# ---------------------------------------------------------------------------
# Visual identity: every reel draws its own combination from each axis below
# ---------------------------------------------------------------------------

# look -> (accent override or None for the category accent, highlight colour)
LOOKS: dict[str, tuple[str | None, str]] = {
    "neon": (None, "#ffe600"),
    "terminal": ("#3fb950", "#7ee787"),
    "blueprint": ("#36f9f6", "#ffd166"),
    "sunset": ("#ffd166", "#fff275"),
    "mono": ("#ff3b5c", "#ffe600"),
    "aurora": ("#7ee787", "#a5f3fc"),
    "matrix": ("#00ff9c", "#d1ff4a"),
    "glass": ("#c4b5fd", "#fde68a"),
    "ember": ("#ff8a3d", "#ffd166"),
    "galaxy": ("#a78bfa", "#f0abfc"),
    "circuit": ("#22d3ee", "#a3e635"),
    "retrosun": ("#ff4d8d", "#ffe066"),
    "ocean": ("#38bdf8", "#fde047"),
    "chalk": ("#f8fafc", "#fde047"),
    "hexgrid": ("#34d399", "#fbbf24"),
    "bokeh": (None, "#fff275"),
}
AXES: dict[str, list[str]] = {
    "look": list(LOOKS),
    "hook": ["stack", "terminal", "alert", "sticker", "kinetic", "question", "glitch", "news", "spotlight", "chat", "split"],
    "captions": ["pop", "box", "clean", "type", "neon", "bounce", "gradient", "tape", "mega", "underline", "karaoke"],
    "cta": ["search", "comment", "series", "share", "triple"],
    "hookFont": ["anton", "bebas", "archivo", "oswald"],
    "presenter": ["aarav", "kabir", "rohan"],  # male only: the voice is male (user's rule)
    "camera": ["punch", "snap", "drift", "handheld", "breathe"],
    "grade": ["none", "teal_orange", "warm", "cool", "vivid", "faded", "contrast"],
    "overlay": ["none", "leaks", "dust", "vhs", "letterbox", "sparks"],
    "burst": ["ring", "rays", "sparks", "slash"],
    "music": ["lofi", "keys", "pad", "pluck", "bell", "arp"],
}
# Base odds before learning (1.0 unless listed).
BASE_WEIGHT: dict[tuple[str, str], float] = {}
SERIES_NAMES = {"dsa": "O(1) TRICKS", "repo": "GITHUB GEMS", "ai_tool": "AI DEV TOOLS", "dev_tip": "DEV TIPS",
                "website": "DEV WEBSITES", "hiring": "HIRING IN INDIA"}
FORCED: dict[str, dict[str, str]] = {"hiring": {"cta": "triple"}}


def engagement_score(insights: dict[str, Any]) -> float | None:
    """Per-view engagement: sends and saves count most (top ranking signals), then comments, then likes."""
    views = insights.get("views") or insights.get("reach") or 0
    if views < 50:  # too early to judge
        return None
    pts = (insights.get("likes", 0) + 3 * insights.get("comments", 0) + 4 * insights.get("shares", 0)
           + 3 * insights.get("saved", 0))
    return pts / views


def learned_weights(queue: list[dict[str, Any]]) -> dict[tuple[str, str], float]:
    """Bayesian-smoothed lift per style option from published reels' Insights. 1.0 = average.
    Clamped to [0.4, 3] so nothing is ever ruled out (keeps exploring)."""
    rows = [(i["style_used"], sc) for i in queue
            if i.get("style_used") and (sc := engagement_score(i.get("insights") or {})) is not None]
    if len(rows) < 3:
        return {}
    mean = sum(sc for _, sc in rows) / len(rows) or 1e-9
    prior_n = 3.0
    weights: dict[tuple[str, str], float] = {}
    for axis, options in AXES.items():
        for opt in options:
            hits = [sc for st, sc in rows if st.get(axis) == opt]
            smoothed = (sum(hits) + mean * prior_n) / (len(hits) + prior_n)
            weights[(axis, opt)] = max(0.4, min(3.0, smoothed / mean))
    return weights


def pick_style(item: dict[str, Any], queue: list[dict[str, Any]], rng: Any = None) -> dict[str, Any]:
    """Weighted-random pick per axis. Never repeats the previous reel's choice on any axis, leans
    towards options whose reels performed better, and lets a queue item pin axes via "style"."""
    import random as _random

    rng = rng or _random.Random()
    done = [q for q in queue if q.get("style_used") and q["id"] != item["id"]]
    done.sort(key=lambda q: q.get("rendered_at") or q.get("created_at") or "")
    prev = done[-1]["style_used"] if done else {}
    learned = learned_weights(queue)
    pinned = {**FORCED.get(item["category"], {}), **(item.get("style") or {})}
    style: dict[str, Any] = {}
    for axis, options in AXES.items():
        if axis in pinned:
            style[axis] = pinned[axis]
            continue
        pool = [o for o in options if o != prev.get(axis)] or options
        weights = [BASE_WEIGHT.get((axis, o), 1.0) * learned.get((axis, o), 1.0) for o in pool]
        style[axis] = rng.choices(pool, weights=weights, k=1)[0]
    accent, highlight = LOOKS.get(style["look"], LOOKS["neon"])
    style["highlight"] = pinned.get("highlight") or highlight
    style["accent"] = pinned.get("accent") or accent or ACCENTS.get(item["category"], "#ff7edb")
    trans = TRANSITIONS[:]
    rng.shuffle(trans)
    style["transitions"] = trans
    same = [q for q in queue if q.get("category") == item["category"]]
    idx = next((k for k, q in enumerate(same) if q["id"] == item["id"]), len(same))
    style["series"] = f"{SERIES_NAMES.get(item['category'], 'DEV TIPS')} · PART {idx + 1}"
    style["emoji"] = rng.random() < 0.8
    return style
