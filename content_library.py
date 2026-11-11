"""Evergreen reel library: DSA patterns, interview concepts explained simply, and quick quizzes.

The daily schedule (slot_gate.SLOTS) asks for 2 DSA + 2 interview + 1 quiz + 1 hiring reel. Trending repos
only fill in when this library and the Gemini top-up are both empty.

Every DSA entry carries tests; `check_dsa` runs them, so a snippet that doesn't work never reaches a reel.
Gemini-written entries (content_gen.py) go through the same checks.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# DSA: hook -> problem -> naive -> approach steps -> code -> CTA
# steps are (icon, title, detail). Keep titles <= 24 chars and details <= 36 so they fit the cards.
# ---------------------------------------------------------------------------

DSA_LIBRARY: list[dict[str, Any]] = [
    {
        "key": "two_sum", "number": 1, "title": "Two Sum", "difficulty": "Easy", "hook": "ONE PASS ONLY",
        "statement": "Return the indexes of the two numbers that add up to the target.",
        "example": [2, 7, 11, 15], "naive": ("CHECK EVERY PAIR", "O(n²) TIME"), "pattern": "HASH MAP LOOKUP",
        "steps": [("🔁", "Walk the array once", "for each number n"), ("🧮", "Need = target - n", "what pairs with it?"),
                  ("🗂️", "Seen it before?", "check the hash map"), ("✅", "Return both indexes", "else store n -> index")],
        "func": "two_sum", "snippet": "def two_sum(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        if target - n in seen:\n            return [seen[target - n], i]\n        seen[n] = i",
        "focus": [3, 4], "stamps": ["O(n) TIME", "1 PASS"], "link": "https://leetcode.com/problems/two-sum/",
        "tests": [[[[2, 7, 11, 15], 9], [0, 1]], [[[3, 2, 4], 6], [1, 2]], [[[3, 3], 6], [0, 1]]],
        "narration": {
            "hook": "Ninety percent of people solve Two Sum the slow way.",
            "problem": "LeetCode 1. Find the two numbers that add up to the target, and return their indexes.",
            "naive": "Checking every pair works, but that's O of n squared.",
            "how": "Walk the array once. For each number, work out what it needs to reach the target. If you've already seen that number in your hash map, you're done. If not, store it and move on.",
            "code": "One pass, one hash map. O of n time.",
        },
    },
    {
        "key": "valid_parentheses", "number": 20, "title": "Valid Parentheses", "difficulty": "Easy", "hook": "USE A STACK",
        "statement": "Given a string of brackets, check that every bracket closes in the right order.",
        "example": ["(", "[", "]", ")", "{", "}"], "naive": ("REPLACE PAIRS LOOP", "O(n²) TIME"), "pattern": "STACK MATCHING",
        "steps": [("📥", "Opening bracket?", "push it on the stack"), ("📤", "Closing bracket?", "pop and compare"),
                  ("❌", "Mismatch or empty?", "return false"), ("✅", "Stack empty at end", "the string is valid")],
        "func": "is_valid", "snippet": "def is_valid(s):\n    pairs = {')': '(', ']': '[', '}': '{'}\n    stack = []\n    for ch in s:\n        if ch in pairs:\n            if not stack or stack.pop() != pairs[ch]:\n                return False\n        else:\n            stack.append(ch)\n    return not stack",
        "focus": [5, 6], "stamps": ["O(n) TIME", "STACK"], "link": "https://leetcode.com/problems/valid-parentheses/",
        "tests": [[["()[]{}"], True], [["(]"], False], [["([)]"], False], [["{[]}"], True], [["("], False]],
        "narration": {
            "hook": "This is the most asked stack question ever.",
            "problem": "LeetCode 20. Check that every bracket in the string closes in the right order.",
            "naive": "Repeatedly deleting matching pairs works, but it's O of n squared.",
            "how": "Opening bracket? Push it on the stack. Closing bracket? Pop the top and compare. A mismatch, or nothing to pop, means false. If the stack is empty at the end, it's valid.",
            "code": "One loop, one stack. O of n time.",
        },
    },
    {
        "key": "stock", "number": 121, "title": "Best Time to Buy Stock", "difficulty": "Easy", "hook": "TRACK THE MINIMUM",
        "statement": "Prices for each day. Buy once, sell once later. Find the maximum profit.",
        "example": [7, 1, 5, 3, 6, 4], "naive": ("EVERY BUY-SELL PAIR", "O(n²) TIME"), "pattern": "RUNNING MINIMUM",
        "steps": [("📉", "Track lowest price", "cheapest day so far"), ("💰", "Profit if sold today", "price - lowest"),
                  ("🏆", "Keep the best profit", "max of all days"), ("✅", "Answer here is 5", "buy at 1, sell at 6")],
        "func": "max_profit", "snippet": "def max_profit(prices):\n    low, best = float('inf'), 0\n    for p in prices:\n        low = min(low, p)\n        best = max(best, p - low)\n    return best",
        "focus": [3, 4], "stamps": ["O(n) TIME", "O(1) SPACE"], "link": "https://leetcode.com/problems/best-time-to-buy-and-sell-stock/",
        "tests": [[[[7, 1, 5, 3, 6, 4]], 5], [[[7, 6, 4, 3, 1]], 0], [[[2, 4, 1]], 2]],
        "narration": {
            "hook": "Amazon loves asking this one.",
            "problem": "LeetCode 121. You get stock prices for each day. Buy once, sell once later, and find the biggest profit.",
            "naive": "Trying every buy and sell pair is O of n squared.",
            "how": "Track the lowest price you've seen so far. Each day, the profit is today's price minus that lowest price. Keep the best profit. Here, buy at one, sell at six, profit five.",
            "code": "Two variables. O of n time, O of one space.",
        },
    },
    {
        "key": "longest_substring", "number": 3, "title": "Longest Substring", "difficulty": "Medium", "hook": "SLIDING WINDOW MAGIC",
        "statement": "Find the length of the longest substring without repeating characters.",
        "example": ["a", "b", "c", "a", "b", "c", "b", "b"], "naive": ("CHECK EVERY SUBSTRING", "O(n³) TIME"), "pattern": "SLIDING WINDOW",
        "steps": [("➡️", "Grow the right edge", "add one character"), ("🔁", "Repeat inside?", "jump left past it"),
                  ("📏", "Measure the window", "right - left + 1"), ("✅", "Keep the longest", "answer here is 3")],
        "func": "length_of_longest", "snippet": "def length_of_longest(s):\n    last, left, best = {}, 0, 0\n    for right, ch in enumerate(s):\n        if last.get(ch, -1) >= left:\n            left = last[ch] + 1\n        last[ch] = right\n        best = max(best, right - left + 1)\n    return best",
        "focus": [3, 4], "stamps": ["O(n) TIME", "1 PASS"], "link": "https://leetcode.com/problems/longest-substring-without-repeating-characters/",
        "tests": [[["abcabcbb"], 3], [["bbbbb"], 1], [["pwwkew"], 3], [[""], 0], [["abba"], 2]],
        "narration": {
            "hook": "Learn this once and you'll crack ten more problems.",
            "problem": "LeetCode 3. Find the longest substring with no repeating characters.",
            "naive": "Checking every substring is O of n cubed. Way too slow.",
            "how": "Use a sliding window. Grow the right edge one character at a time. If that character repeats inside the window, jump the left edge past its last position. Measure the window and keep the longest.",
            "code": "The sliding window pattern. O of n time.",
        },
    },
    {
        "key": "container_water", "number": 11, "title": "Container With Most Water", "difficulty": "Medium", "hook": "TWO POINTERS WIN",
        "statement": "Pick two lines that hold the most water between them.",
        "example": [1, 8, 6, 2, 5, 4, 8, 3, 7], "naive": ("EVERY PAIR OF LINES", "O(n²) TIME"), "pattern": "SQUEEZE INWARD",
        "steps": [("↔️", "Start at both ends", "widest container first"), ("💧", "Area = width × short", "the shorter line limits it"),
                  ("⏩", "Move the shorter line", "only it can improve"), ("✅", "Best area is 49", "pointers meet = done")],
        "func": "max_area", "snippet": "def max_area(h):\n    l, r, best = 0, len(h) - 1, 0\n    while l < r:\n        best = max(best, (r - l) * min(h[l], h[r]))\n        if h[l] < h[r]:\n            l += 1\n        else:\n            r -= 1\n    return best",
        "focus": [3, 4], "stamps": ["O(n) TIME", "O(1) SPACE"], "link": "https://leetcode.com/problems/container-with-most-water/",
        "tests": [[[[1, 8, 6, 2, 5, 4, 8, 3, 7]], 49], [[[1, 1]], 1], [[[4, 3, 2, 1, 4]], 16]],
        "narration": {
            "hook": "Two pointers turn this from slow to instant.",
            "problem": "LeetCode 11. Pick two lines that hold the most water between them.",
            "naive": "Checking every pair of lines is O of n squared.",
            "how": "Start with pointers at both ends, the widest container. The area is the width times the shorter line. Now move the shorter line inward, because only that can make it better. Stop when they meet.",
            "code": "Two pointers. O of n time, O of one space.",
        },
    },
    {
        "key": "binary_search", "number": 704, "title": "Binary Search", "difficulty": "Easy", "hook": "HALVE EVERY STEP",
        "statement": "Find the target in a sorted array and return its index, or minus one.",
        "example": [-1, 0, 3, 5, 9, 12], "naive": ("SCAN EVERY ELEMENT", "O(n) TIME"), "pattern": "CUT IN HALF",
        "steps": [("🎯", "Look at the middle", "mid = (lo + hi) // 2"), ("⬅️", "Target smaller?", "drop the right half"),
                  ("➡️", "Target bigger?", "drop the left half"), ("✅", "Found or lo > hi", "a billion items = 30 steps")],
        "func": "search", "snippet": "def search(nums, target):\n    lo, hi = 0, len(nums) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if nums[mid] == target:\n            return mid\n        if nums[mid] < target:\n            lo = mid + 1\n        else:\n            hi = mid - 1\n    return -1",
        "focus": [3, 6, 7], "stamps": ["O(log n) TIME", "O(1) SPACE"], "link": "https://leetcode.com/problems/binary-search/",
        "tests": [[[[-1, 0, 3, 5, 9, 12], 9], 4], [[[-1, 0, 3, 5, 9, 12], 2], -1], [[[5], 5], 0]],
        "narration": {
            "hook": "Find one item in a billion in thirty steps.",
            "problem": "LeetCode 704. Find the target in a sorted array and return its index.",
            "naive": "Scanning every element is O of n.",
            "how": "Look at the middle element. If the target is smaller, drop the right half. If it's bigger, drop the left half. Every step cuts the array in half, so a billion items takes about thirty steps.",
            "code": "Binary search. O of log n time.",
        },
    },
    {
        "key": "merge_intervals", "number": 56, "title": "Merge Intervals", "difficulty": "Medium", "hook": "SORT THEN MERGE",
        "statement": "Merge all overlapping intervals and return the result.",
        "example": ["1-3", "2-6", "8-10", "15-18"], "naive": ("COMPARE EVERY PAIR", "O(n²) TIME"), "pattern": "SORT BY START",
        "steps": [("🔢", "Sort by start time", "overlaps become neighbours"), ("🔍", "Overlaps the last one?", "start <= last end"),
                  ("🔗", "Yes: stretch the end", "end = max(both ends)"), ("➕", "No: start a new one", "append to the result")],
        "func": "merge", "snippet": "def merge(intervals):\n    out = []\n    for s, e in sorted(intervals):\n        if out and s <= out[-1][1]:\n            out[-1][1] = max(out[-1][1], e)\n        else:\n            out.append([s, e])\n    return out",
        "focus": [2, 3, 4], "stamps": ["O(n log n)", "SORT FIRST"], "link": "https://leetcode.com/problems/merge-intervals/",
        "tests": [[[[[1, 3], [2, 6], [8, 10], [15, 18]]], [[1, 6], [8, 10], [15, 18]]], [[[[1, 4], [4, 5]]], [[1, 5]]], [[[[1, 4], [0, 4]]], [[0, 4]]]],
        "narration": {
            "hook": "Google, Meta and Microsoft all ask this.",
            "problem": "LeetCode 56. Merge every pair of overlapping intervals.",
            "naive": "Comparing every interval with every other is O of n squared.",
            "how": "First, sort by start time, so overlapping intervals sit next to each other. Then walk through. If it overlaps the last merged one, stretch that end. If not, start a new interval.",
            "code": "Sort, then one pass. O of n log n.",
        },
    },
    {
        "key": "product_except_self", "number": 238, "title": "Product Except Self", "difficulty": "Medium", "hook": "NO DIVISION ALLOWED",
        "statement": "For each index, return the product of every other number. No division.",
        "example": [1, 2, 3, 4], "naive": ("MULTIPLY FOR EACH", "O(n²) TIME"), "pattern": "PREFIX × SUFFIX",
        "steps": [("➡️", "Left to right pass", "product of everything left"), ("⬅️", "Right to left pass", "times everything right"),
                  ("🧩", "Left × right", "= everything except self"), ("✅", "Answer: 24 12 8 6", "two passes, no division")],
        "func": "product_except_self", "snippet": "def product_except_self(nums):\n    out, left = [1] * len(nums), 1\n    for i in range(len(nums)):\n        out[i], left = left, left * nums[i]\n    right = 1\n    for i in reversed(range(len(nums))):\n        out[i] *= right\n        right *= nums[i]\n    return out",
        "focus": [3, 6, 7], "stamps": ["O(n) TIME", "NO DIVISION"], "link": "https://leetcode.com/problems/product-of-array-except-self/",
        "tests": [[[[1, 2, 3, 4]], [24, 12, 8, 6]], [[[-1, 1, 0, -3, 3]], [0, 0, 9, 0, 0]]],
        "narration": {
            "hook": "This question rejects most candidates.",
            "problem": "LeetCode 238. For every index, return the product of all the other numbers, without division.",
            "naive": "Multiplying everything again for each index is O of n squared.",
            "how": "Do a left to right pass, storing the product of everything to the left. Then a right to left pass, multiplying in everything to the right. Left times right is everything except itself.",
            "code": "Prefix and suffix products. O of n time.",
        },
    },
    {
        "key": "climbing_stairs", "number": 70, "title": "Climbing Stairs", "difficulty": "Easy", "hook": "DP MADE EASY",
        "statement": "Climb n stairs taking 1 or 2 steps at a time. How many distinct ways?",
        "example": [1, 2, 3, 5, 8], "naive": ("PLAIN RECURSION", "O(2ⁿ) TIME"), "pattern": "WAYS(N-1) + WAYS(N-2)",
        "steps": [("🪜", "Last move was 1 or 2", "only two ways to arrive"), ("➕", "ways(n) = n-1 + n-2", "it's Fibonacci"),
                  ("🧠", "Keep only two numbers", "no array needed"), ("✅", "5 stairs = 8 ways", "O(n) time, O(1) space")],
        "func": "climb_stairs", "snippet": "def climb_stairs(n):\n    a, b = 1, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a",
        "focus": [3], "stamps": ["O(n) TIME", "O(1) SPACE"], "link": "https://leetcode.com/problems/climbing-stairs/",
        "tests": [[[2], 2], [[3], 3], [[5], 8], [[1], 1]],
        "narration": {
            "hook": "The easiest way to finally understand dynamic programming.",
            "problem": "LeetCode 70. You climb one or two steps at a time. How many ways can you reach the top?",
            "naive": "Plain recursion recalculates the same stairs again and again. That's O of two to the n.",
            "how": "Think about your last move. You came from one step below or two steps below. So the ways to reach n equal ways to n minus one plus ways to n minus two. It's just Fibonacci.",
            "code": "Two variables. O of n time, O of one space.",
        },
    },
    {
        "key": "linked_list_cycle", "number": 141, "title": "Linked List Cycle", "difficulty": "Easy", "hook": "FAST AND SLOW",
        "statement": "Return true if the linked list has a cycle in it.",
        "example": [3, 2, 0, -4], "naive": ("HASH SET OF NODES", "O(n) SPACE"), "pattern": "TORTOISE & HARE",
        "steps": [("🐢", "Slow moves 1 step", "slow = slow.next"), ("🐇", "Fast moves 2 steps", "fast = fast.next.next"),
                  ("🔁", "Cycle? They meet", "fast laps the slow one"), ("✅", "Fast hits null?", "no cycle")],
        "func": "has_cycle_list", "snippet": "def has_cycle(head):\n    slow = fast = head\n    while fast and fast.next:\n        slow = slow.next\n        fast = fast.next.next\n        if slow is fast:\n            return True\n    return False",
        "focus": [3, 4, 5], "stamps": ["O(n) TIME", "O(1) SPACE"], "link": "https://leetcode.com/problems/linked-list-cycle/",
        "tests": [[[[3, 2, 0, -4], 1], True], [[[1, 2], 0], True], [[[1], -1], False]],
        "harness": "class Node:\n    def __init__(self, v):\n        self.val, self.next = v, None\ndef has_cycle_list(vals, pos):\n    nodes = [Node(v) for v in vals]\n    for a, b in zip(nodes, nodes[1:]):\n        a.next = b\n    if pos >= 0:\n        nodes[-1].next = nodes[pos]\n    return has_cycle(nodes[0] if nodes else None)",
        "narration": {
            "hook": "A runner on a circular track explains this perfectly.",
            "problem": "LeetCode 141. Does this linked list loop back on itself?",
            "naive": "Storing every visited node in a hash set costs O of n memory.",
            "how": "Send two pointers. Slow moves one step, fast moves two steps. If there's a cycle, the fast one laps the slow one and they meet. If fast hits null, there's no cycle.",
            "code": "Floyd's algorithm. O of one space.",
        },
    },
    {
        "key": "top_k_frequent", "number": 347, "title": "Top K Frequent", "difficulty": "Medium", "hook": "BUCKETS BEAT SORTING",
        "statement": "Return the k most frequent elements.",
        "example": [1, 1, 1, 2, 2, 3], "naive": ("COUNT THEN SORT", "O(n log n)"), "pattern": "BUCKET SORT",
        "steps": [("🧮", "Count every number", "hash map of counts"), ("🪣", "Bucket by frequency", "bucket[count] = numbers"),
                  ("⬇️", "Read buckets high→low", "most frequent first"), ("✅", "Stop after k items", "O(n) total")],
        "func": "top_k", "snippet": "def top_k(nums, k):\n    count = {}\n    for n in nums:\n        count[n] = count.get(n, 0) + 1\n    buckets = [[] for _ in range(len(nums) + 1)]\n    for n, c in count.items():\n        buckets[c].append(n)\n    out = [n for b in reversed(buckets) for n in b]\n    return out[:k]",
        "focus": [4, 6, 7], "stamps": ["O(n) TIME", "NO SORT"], "link": "https://leetcode.com/problems/top-k-frequent-elements/",
        "tests": [[[[1, 1, 1, 2, 2, 3], 2], [1, 2]], [[[1], 1], [1]]],
        "narration": {
            "hook": "Sorting here is the trap.",
            "problem": "LeetCode 347. Return the k most frequent numbers.",
            "naive": "Counting and then sorting by count is O of n log n.",
            "how": "Count every number with a hash map. Then put each number in a bucket, where the bucket index is its count. Read the buckets from highest to lowest and stop after k numbers.",
            "code": "Bucket sort. O of n time.",
        },
    },
    {
        "key": "group_anagrams", "number": 49, "title": "Group Anagrams", "difficulty": "Medium", "hook": "SORTED WORD KEY",
        "statement": "Group the words that are anagrams of each other.",
        "example": ["eat", "tea", "tan", "ate", "nat", "bat"], "naive": ("COMPARE EVERY PAIR", "O(n²·k)"), "pattern": "SAME KEY, SAME GROUP",
        "steps": [("🔤", "Sort each word", "eat, tea, ate -> aet"), ("🗝️", "Sorted word = key", "anagrams share a key"),
                  ("🗂️", "Group by that key", "hash map of lists"), ("✅", "Return the groups", "one pass over words")],
        "func": "group_anagrams_sorted", "snippet": "def group_anagrams(words):\n    groups = {}\n    for w in words:\n        key = ''.join(sorted(w))\n        groups.setdefault(key, []).append(w)\n    return list(groups.values())",
        "focus": [3, 4], "stamps": ["O(n·k log k)", "HASH MAP"], "link": "https://leetcode.com/problems/group-anagrams/",
        "tests": [[[["eat", "tea", "tan", "ate", "nat", "bat"]], [["ate", "eat", "tea"], ["bat"], ["nat", "tan"]]], [[[""]], [[""]]]],
        "harness": "def group_anagrams_sorted(words):\n    return sorted(sorted(g) for g in group_anagrams(words))",
        "narration": {
            "hook": "Anagrams have a secret fingerprint.",
            "problem": "LeetCode 49. Group together the words that are anagrams.",
            "naive": "Comparing every word with every other word is far too slow.",
            "how": "Sort the letters of each word. Eat, tea and ate all become the same key. Use that sorted word as a hash map key, and drop each word into its group.",
            "code": "One hash map, one pass over the words.",
        },
    },
    {
        "key": "move_zeroes", "number": 283, "title": "Move Zeroes", "difficulty": "Easy", "hook": "SNOWBALL THE ZEROES",
        "statement": "Move every zero to the end in place, keeping the order of the rest.",
        "example": [0, 1, 0, 3, 12], "naive": ("NEW ARRAY COPY", "O(n) SPACE"), "pattern": "WRITE POINTER",
        "steps": [("✍️", "Keep a write pointer", "where the next non-zero goes"), ("🔁", "Scan every number", "skip the zeroes"),
                  ("🔀", "Non-zero? Swap it", "into the write slot"), ("✅", "Zeroes end up last", "1 3 12 0 0")],
        "func": "move_zeroes_ret", "snippet": "def move_zeroes(nums):\n    w = 0\n    for i in range(len(nums)):\n        if nums[i] != 0:\n            nums[w], nums[i] = nums[i], nums[w]\n            w += 1",
        "focus": [3, 4, 5], "stamps": ["O(n) TIME", "IN PLACE"], "link": "https://leetcode.com/problems/move-zeroes/",
        "tests": [[[[0, 1, 0, 3, 12]], [1, 3, 12, 0, 0]], [[[0]], [0]], [[[1, 0, 1]], [1, 1, 0]]],
        "harness": "def move_zeroes_ret(nums):\n    move_zeroes(nums)\n    return nums",
        "narration": {
            "hook": "Facebook asked this in a phone screen.",
            "problem": "LeetCode 283. Move every zero to the end, in place, keeping the other numbers in order.",
            "naive": "Copying into a new array costs O of n extra memory.",
            "how": "Keep a write pointer at the front. Scan every number. Whenever you find a non-zero, swap it into the write slot and move the pointer forward. The zeroes snowball to the end.",
            "code": "One pass, in place. O of one space.",
        },
    },
    {
        "key": "daily_temperatures", "number": 739, "title": "Daily Temperatures", "difficulty": "Medium", "hook": "MONOTONIC STACK TRICK",
        "statement": "For each day, how many days until a warmer temperature?",
        "example": [73, 74, 75, 71, 69, 72, 76, 73], "naive": ("SCAN AHEAD EACH DAY", "O(n²) TIME"), "pattern": "MONOTONIC STACK",
        "steps": [("📚", "Stack of waiting days", "temps only go down in it"), ("🌡️", "Warmer day arrives?", "pop every colder day"),
                  ("📏", "Answer = gap in days", "today - popped day"), ("📥", "Push today", "it waits for warmer")],
        "func": "daily_temperatures", "snippet": "def daily_temperatures(t):\n    out, stack = [0] * len(t), []\n    for i, temp in enumerate(t):\n        while stack and t[stack[-1]] < temp:\n            j = stack.pop()\n            out[j] = i - j\n        stack.append(i)\n    return out",
        "focus": [3, 4, 5], "stamps": ["O(n) TIME", "STACK"], "link": "https://leetcode.com/problems/daily-temperatures/",
        "tests": [[[[73, 74, 75, 71, 69, 72, 76, 73]], [1, 1, 4, 2, 1, 1, 0, 0]], [[[30, 60, 90]], [1, 1, 0]]],
        "narration": {
            "hook": "One pattern solves a whole family of interview questions.",
            "problem": "LeetCode 739. For each day, how many days until it gets warmer?",
            "naive": "Scanning ahead from every day is O of n squared.",
            "how": "Keep a stack of days still waiting for a warmer day. When a warmer day arrives, pop every colder day, and its answer is the gap in days. Then push today onto the stack.",
            "code": "A monotonic stack. Every day is pushed and popped once, so O of n.",
        },
    },
    {
        "key": "invert_tree", "number": 226, "title": "Invert Binary Tree", "difficulty": "Easy", "hook": "SWAP EVERY CHILD",
        "statement": "Mirror a binary tree: every left child becomes the right child.",
        "example": [4, 2, 7, 1, 3, 6, 9], "naive": ("BUILD A NEW TREE", "O(n) EXTRA"), "pattern": "RECURSIVE SWAP",
        "steps": [("🌳", "Start at the root", "empty node? return"), ("🔀", "Swap left and right", "one line"),
                  ("🔁", "Recurse on both kids", "same job, smaller tree"), ("✅", "Tree is mirrored", "4 7 2 9 6 3 1")],
        "func": "invert_list", "snippet": "def invert(root):\n    if root:\n        root.left, root.right = invert(root.right), invert(root.left)\n    return root",
        "focus": [2], "stamps": ["O(n) TIME", "3 LINES"], "link": "https://leetcode.com/problems/invert-binary-tree/",
        "tests": [[[[4, 2, 7, 1, 3, 6, 9]], [4, 7, 2, 9, 6, 3, 1]], [[[2, 1, 3]], [2, 3, 1]]],
        "harness": "class T:\n    def __init__(self, v):\n        self.val, self.left, self.right = v, None, None\ndef invert_list(vals):\n    nodes = [T(v) for v in vals]\n    for i, n in enumerate(nodes):\n        if 2 * i + 1 < len(nodes): n.left = nodes[2 * i + 1]\n        if 2 * i + 2 < len(nodes): n.right = nodes[2 * i + 2]\n    root, out, q = invert(nodes[0]), [], []\n    q.append(root)\n    while q:\n        n = q.pop(0)\n        if n:\n            out.append(n.val); q += [n.left, n.right]\n    return out",
        "narration": {
            "hook": "The question the Homebrew creator famously failed at Google.",
            "problem": "LeetCode 226. Mirror a binary tree, so every left child becomes a right child.",
            "naive": "People overthink it and build a whole new tree.",
            "how": "Start at the root. Swap its left and right children. Then do exactly the same thing to both children, recursively. When you hit an empty node, just return.",
            "code": "Three lines of recursion. O of n time.",
        },
    },
    {
        "key": "rotated_search", "number": 33, "title": "Search Rotated Array", "difficulty": "Medium", "hook": "ONE HALF IS SORTED",
        "statement": "A sorted array was rotated. Find the target in O(log n).",
        "example": [4, 5, 6, 7, 0, 1, 2], "naive": ("LINEAR SCAN", "O(n) TIME"), "pattern": "MODIFIED BINARY SEARCH",
        "steps": [("🎯", "Check the middle", "found? return it"), ("📈", "Find the sorted half", "one half is always sorted"),
                  ("🔍", "Target inside it?", "search that half"), ("↩️", "Otherwise", "search the other half")],
        "func": "search_rotated", "snippet": "def search_rotated(a, target):\n    lo, hi = 0, len(a) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if a[mid] == target:\n            return mid\n        if a[lo] <= a[mid]:\n            if a[lo] <= target < a[mid]: hi = mid - 1\n            else: lo = mid + 1\n        else:\n            if a[mid] < target <= a[hi]: lo = mid + 1\n            else: hi = mid - 1\n    return -1",
        "focus": [6, 7, 10], "stamps": ["O(log n) TIME", "O(1) SPACE"], "link": "https://leetcode.com/problems/search-in-rotated-sorted-array/",
        "tests": [[[[4, 5, 6, 7, 0, 1, 2], 0], 4], [[[4, 5, 6, 7, 0, 1, 2], 3], -1], [[[1], 0], -1], [[[3, 1], 1], 1]],
        "narration": {
            "hook": "Binary search, but with a twist.",
            "problem": "LeetCode 33. A sorted array got rotated. Find the target in log n time.",
            "naive": "A linear scan works, but that's O of n.",
            "how": "Check the middle. Here's the key idea: one half is always sorted. If the target lies inside the sorted half, search there. Otherwise search the other half.",
            "code": "Modified binary search. O of log n.",
        },
    },
    {
        "key": "number_of_islands", "number": 200, "title": "Number of Islands", "difficulty": "Medium", "hook": "SINK EVERY ISLAND",
        "statement": "Count the islands of 1s in a grid. Land connects up, down, left and right.",
        "example": [], "naive": ("TRACK VISITED SET", "O(m·n) EXTRA"), "pattern": "FLOOD FILL DFS",
        "steps": [("🗺️", "Scan every cell", "row by row"), ("🏝️", "Found land?", "that's a new island"),
                  ("🌊", "Sink the whole island", "DFS turns 1s into 0s"), ("✅", "Count = islands", "each cell visited once")],
        "func": "num_islands_str", "snippet": "def num_islands(g):\n    def sink(r, c):\n        if 0 <= r < len(g) and 0 <= c < len(g[0]) and g[r][c] == '1':\n            g[r][c] = '0'\n            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):\n                sink(r + dr, c + dc)\n    count = 0\n    for r in range(len(g)):\n        for c in range(len(g[0])):\n            if g[r][c] == '1':\n                count += 1\n                sink(r, c)\n    return count",
        "focus": [3, 10, 11], "stamps": ["O(m·n) TIME", "DFS"], "link": "https://leetcode.com/problems/number-of-islands/",
        "tests": [[[["11000", "11000", "00100", "00011"]], 3], [[["111", "010", "111"]], 1], [[["000"]], 0]],
        "harness": "def num_islands_str(rows):\n    return num_islands([list(r) for r in rows])",
        "narration": {
            "hook": "This is the graph question every company asks.",
            "problem": "LeetCode 200. Count the islands in a grid, where land connects up, down, left and right.",
            "naive": "Keeping a separate visited set doubles your memory.",
            "how": "Scan every cell. When you find land, that's a new island, so count it. Then sink the whole island with DFS, turning its ones into zeros, so you never count it twice.",
            "code": "Flood fill. Every cell is visited once.",
        },
    },
]

# ---------------------------------------------------------------------------
# Interview concepts: hook -> simple analogy (3 steps) -> what to say in the interview (3 cards) -> CTA
# ---------------------------------------------------------------------------

INTERVIEW_LIBRARY: list[dict[str, Any]] = [
    {
        "key": "process_vs_thread", "topic": "Process vs Thread explained simply", "hook": "PROCESS VS THREAD", "keyword": "THREAD",
        "link": "https://en.wikipedia.org/wiki/Thread_(computing)",
        "hook_line": "Process versus thread. Most freshers mix these up.",
        "simple_title": "THINK OF A RESTAURANT",
        "simple": [("🏢", "Process = a restaurant", "own kitchen, own memory"), ("👨‍🍳", "Thread = a chef", "many chefs share one kitchen"),
                   ("💥", "Chefs share everything", "fast, but they can collide")],
        "simple_say": "Think of a restaurant. A process is the whole restaurant, with its own kitchen and memory. A thread is a chef. Many chefs share one kitchen, so they work fast, but they can bump into each other.",
        "answer": [("🧠", "Process: own memory", "isolated, heavier to create"), ("⚡", "Thread: shared memory", "lightweight, fast to switch"),
                   ("🔒", "Shared memory = races", "so we need locks")],
        "answer_say": "In the interview, say this. A process has its own memory and is isolated. Threads share their process's memory, so they are lighter and faster. But shared memory means race conditions, so you need locks.",
    },
    {
        "key": "url_typed", "topic": "What happens when you type a URL", "hook": "TYPE A URL", "keyword": "URL",
        "link": "https://en.wikipedia.org/wiki/Domain_Name_System",
        "hook_line": "What happens when you type google dot com and press enter?",
        "simple_title": "LIKE SENDING A LETTER",
        "simple": [("📒", "DNS = phonebook", "name -> IP address"), ("🤝", "TCP + TLS handshake", "secure line opens"),
                   ("📨", "HTTP request & reply", "server sends HTML back"), ("🎨", "Browser renders", "HTML, CSS, JavaScript")],
        "simple_say": "First, DNS works like a phonebook and turns the name into an IP address. Then a TCP and TLS handshake opens a secure line. Your browser sends an HTTP request, the server replies with HTML, and the browser renders the page.",
        "answer": [("🔎", "Cache first", "browser, OS, then DNS server"), ("🔐", "HTTPS = TLS", "encrypts everything"),
                   ("⚡", "Then CDN & caching", "why sites load fast")],
        "answer_say": "Bonus points: mention that DNS answers are cached at every level, that HTTPS uses TLS to encrypt the traffic, and that CDNs serve files from a server near you.",
    },
    {
        "key": "sql_vs_nosql", "topic": "SQL vs NoSQL explained simply", "hook": "SQL OR NOSQL", "keyword": "SQL",
        "link": "https://en.wikipedia.org/wiki/NoSQL",
        "hook_line": "SQL or NoSQL? Here's how to answer it in thirty seconds.",
        "simple_title": "EXCEL VS A FOLDER",
        "simple": [("📊", "SQL = Excel sheets", "fixed columns, strict rules"), ("🗂️", "NoSQL = folder of docs", "each doc can differ"),
                   ("🔗", "SQL loves joins", "relations between tables")],
        "simple_say": "SQL is like Excel sheets, with fixed columns and strict rules, and it's great at joining tables. NoSQL is like a folder of documents, where every document can look different.",
        "answer": [("🏦", "SQL for transactions", "banking, orders, ACID"), ("📈", "NoSQL to scale out", "huge, changing data"),
                   ("⚖️", "It's a trade-off", "consistency vs flexibility")],
        "answer_say": "In the interview: pick SQL when you need transactions and consistency, like payments. Pick NoSQL when data is huge, changes shape, and must scale across many servers. It's a trade-off.",
    },
    {
        "key": "db_index", "topic": "Database indexing explained simply", "hook": "INDEXES EXPLAINED SIMPLY", "keyword": "INDEX",
        "link": "https://en.wikipedia.org/wiki/Database_index",
        "hook_line": "One line of SQL made a query a thousand times faster.",
        "simple_title": "THE BOOK INDEX",
        "simple": [("📖", "No index = read every page", "full table scan"), ("🔖", "Index = back of the book", "jump straight to the page"),
                   ("🌳", "Stored as a B-tree", "O(log n) lookups")],
        "simple_say": "Without an index, the database reads every row, like reading every page of a book. An index is the index at the back of the book. It's stored as a B tree, so lookups are log n.",
        "answer": [("⚡", "Faster reads", "WHERE, JOIN, ORDER BY"), ("🐢", "Slower writes", "index updates on insert"),
                   ("🎯", "Index what you filter", "not every column")],
        "answer_say": "Say this: indexes make reads much faster, but every insert and update must also update the index, so writes get slower. Index the columns you filter and join on, not everything.",
    },
    {
        "key": "acid", "topic": "ACID properties explained simply", "hook": "ACID IN SECONDS", "keyword": "ACID",
        "link": "https://en.wikipedia.org/wiki/ACID",
        "hook_line": "Your bank money is safe because of four letters.",
        "simple_title": "A UPI TRANSFER",
        "simple": [("⚛️", "Atomic", "all or nothing"), ("✅", "Consistent", "rules never break"),
                   ("🚧", "Isolated", "transfers don't mix"), ("💾", "Durable", "saved even if power dies")],
        "simple_say": "Think of a UPI transfer. Atomic means all or nothing. Consistent means the rules never break. Isolated means two transfers don't mix up. Durable means it's saved, even if the power dies.",
        "answer": [("🏦", "Money leaves A", "and must reach B"), ("↩️", "Crash halfway?", "rollback, nothing lost"),
                   ("📝", "Done with a log", "write-ahead logging")],
        "answer_say": "Give this example: money leaves account A and must reach account B. If the server crashes halfway, the transaction rolls back. Databases do this with a write ahead log.",
    },
    {
        "key": "cap", "topic": "CAP theorem explained simply", "hook": "CAP THEOREM SIMPLIFIED", "keyword": "CAP",
        "link": "https://en.wikipedia.org/wiki/CAP_theorem",
        "hook_line": "You can't have all three. That's the CAP theorem.",
        "simple_title": "TWO SHOP BRANCHES",
        "simple": [("🔁", "Consistency", "both branches show same stock"), ("🟢", "Availability", "always answer customers"),
                   ("✂️", "Partition", "the phone line between them dies")],
        "simple_say": "Imagine two shop branches. Consistency means both show the same stock. Availability means they always answer customers. A partition is when the phone line between them dies.",
        "answer": [("📵", "Line dies? Choose", "consistency or availability"), ("🏦", "Banks pick C", "refuse rather than be wrong"),
                   ("📱", "Social apps pick A", "slightly stale is fine")],
        "answer_say": "When the line dies, you must choose. Banks pick consistency, and refuse requests rather than show wrong data. Social apps pick availability, and show slightly old data.",
    },
    {
        "key": "load_balancer", "topic": "Load balancer explained simply", "hook": "LOAD BALANCER BASICS", "keyword": "SCALE",
        "link": "https://en.wikipedia.org/wiki/Load_balancing_(computing)",
        "hook_line": "How does Hotstar handle millions watching a cricket match?",
        "simple_title": "TOLL BOOTH MANAGER",
        "simple": [("🚗", "Millions of requests", "one server would melt"), ("🚦", "Load balancer", "sends each car to a free booth"),
                   ("🖥️", "Many servers behind it", "add more when busy")],
        "simple_say": "Millions of requests would melt one server. A load balancer is like a toll booth manager, sending each car to a free booth. Behind it sit many servers, and you add more when it gets busy.",
        "answer": [("🔄", "Round robin", "or least connections"), ("❤️", "Health checks", "skip dead servers"),
                   ("📈", "Horizontal scaling", "more machines, not bigger")],
        "answer_say": "Mention the algorithms, like round robin and least connections. Mention health checks that skip dead servers. And call it horizontal scaling: more machines, not a bigger one.",
    },
    {
        "key": "caching", "topic": "Caching explained simply", "hook": "WHY CACHING WINS", "keyword": "CACHE",
        "link": "https://en.wikipedia.org/wiki/Cache_(computing)",
        "hook_line": "This one idea makes every big app fast.",
        "simple_title": "YOUR FRIDGE VS MARKET",
        "simple": [("🛒", "Database = the market", "far away and slow"), ("🧊", "Cache = your fridge", "close and instant"),
                   ("🔁", "Miss? Fetch and store", "next time it's in the fridge")],
        "simple_say": "The database is the market. It has everything, but it's far away. A cache, like Redis, is your fridge. Check the fridge first. If it's not there, go to the market and keep some in the fridge.",
        "answer": [("📦", "Cache-aside pattern", "check cache, then DB"), ("⏳", "TTL & eviction", "LRU throws out the oldest"),
                   ("⚠️", "Stale data risk", "invalidate on writes")],
        "answer_say": "Name it the cache aside pattern. Talk about expiry with a TTL and LRU eviction. And mention the hard part: invalidating the cache when the data changes.",
    },
    {
        "key": "deadlock", "topic": "Deadlock explained simply", "hook": "DEADLOCK IN SECONDS", "keyword": "DEADLOCK",
        "link": "https://en.wikipedia.org/wiki/Deadlock",
        "hook_line": "Two programs wait for each other forever. That's a deadlock.",
        "simple_title": "TWO CARS, ONE BRIDGE",
        "simple": [("🚗", "Car A holds the left lane", "wants the right"), ("🚙", "Car B holds the right", "wants the left"),
                   ("⛔", "Nobody gives up", "both wait forever")],
        "simple_say": "Two cars on a narrow bridge. Car A holds one lane and wants the other. Car B holds the other and wants the first. Nobody gives up, so both wait forever.",
        "answer": [("🔒", "4 conditions", "mutual exclusion, hold & wait"), ("🔁", "+ no preemption, circular", "break any one"),
                   ("📏", "Fix: lock ordering", "always lock A before B")],
        "answer_say": "Say there are four conditions: mutual exclusion, hold and wait, no preemption, and circular wait. Break any one and deadlock can't happen. The common fix is always taking locks in the same order.",
    },
    {
        "key": "oops", "topic": "4 pillars of OOP explained simply", "hook": "OOP IN 30s", "keyword": "OOPS",
        "link": "https://en.wikipedia.org/wiki/Object-oriented_programming",
        "hook_line": "The four pillars of OOP, using just a car.",
        "simple_title": "ALL WITH ONE CAR",
        "simple": [("💊", "Encapsulation", "engine hidden under the hood"), ("🎛️", "Abstraction", "you just press the pedal"),
                   ("🧬", "Inheritance", "an EV is still a car"), ("🎭", "Polymorphism", "start() works differently")],
        "simple_say": "Encapsulation: the engine is hidden under the hood. Abstraction: you just press the pedal. Inheritance: an electric car is still a car. Polymorphism: start works differently for petrol and electric.",
        "answer": [("🔐", "Encapsulation", "private data, public methods"), ("🧬", "Inheritance", "reuse code from a parent"),
                   ("🎭", "Polymorphism", "overloading and overriding")],
        "answer_say": "In code: encapsulation is private data with public methods. Inheritance reuses a parent class. Polymorphism is method overloading and overriding. Always give one real example.",
    },
    {
        "key": "big_o", "topic": "Big O notation explained simply", "hook": "BIG O SIMPLIFIED", "keyword": "BIGO",
        "link": "https://en.wikipedia.org/wiki/Big_O_notation",
        "hook_line": "Big O finally explained without the maths.",
        "simple_title": "FINDING A FRIEND",
        "simple": [("⚡", "O(1): know the seat", "go straight there"), ("🔍", "O(log n): sorted list", "halve it each time"),
                   ("🚶", "O(n): check every seat", "one by one"), ("🐌", "O(n²): ask everyone", "about everyone")],
        "simple_say": "You're looking for a friend in a stadium. O of one: you know the seat. O of log n: the list is sorted, so you halve it. O of n: you check every seat. O of n squared: everyone asks about everyone.",
        "answer": [("📈", "How it grows", "not the exact time"), ("🧹", "Drop constants", "O(2n) is O(n)"),
                   ("🧠", "Space counts too", "say both time and space")],
        "answer_say": "Say this: Big O describes how the time grows as the input grows, not the exact seconds. Drop the constants. And always state both the time and the space complexity.",
    },
    {
        "key": "tcp_udp", "topic": "TCP vs UDP explained simply", "hook": "TCP VS UDP", "keyword": "TCP",
        "link": "https://en.wikipedia.org/wiki/User_Datagram_Protocol",
        "hook_line": "Why does a video call use a different protocol than WhatsApp texts?",
        "simple_title": "COURIER VS SHOUTING",
        "simple": [("📦", "TCP = registered courier", "delivery confirmed, in order"), ("📢", "UDP = shouting", "fast, no guarantee"),
                   ("🎮", "Lost packet in UDP?", "just move on")],
        "simple_say": "TCP is a registered courier. Every packet is confirmed and arrives in order. UDP is like shouting across a room. It's fast, but there's no guarantee, and lost packets are just skipped.",
        "answer": [("💬", "TCP for correctness", "chat, web, payments"), ("📹", "UDP for speed", "video calls, games, DNS"),
                   ("🤝", "TCP has a handshake", "SYN, SYN-ACK, ACK")],
        "answer_say": "Use TCP when every byte matters, like chats and web pages. Use UDP when speed matters more, like video calls, games and DNS. Bonus: name the three way handshake.",
    },
    {
        "key": "jwt", "topic": "JWT authentication explained simply", "hook": "JWT EXPLAINED SIMPLY", "keyword": "JWT",
        "link": "https://en.wikipedia.org/wiki/JSON_Web_Token",
        "hook_line": "How does an app remember you're logged in?",
        "simple_title": "A CONCERT WRISTBAND",
        "simple": [("🔑", "Log in once", "server checks your password"), ("🎟️", "Get a signed token", "like a wristband"),
                   ("🚪", "Show it every request", "no password again")],
        "simple_say": "You log in once and the server checks your password. It gives you a signed token, like a concert wristband. You show it with every request, so you never send your password again.",
        "answer": [("🧩", "Header.Payload.Signature", "three parts, base64"), ("✍️", "Signature stops tampering", "change it and it breaks"),
                   ("⏰", "Short expiry", "plus refresh tokens")],
        "answer_say": "A JWT has three parts: header, payload and signature. The signature means nobody can edit it. The payload isn't encrypted, so no secrets in it. Keep expiry short and use refresh tokens.",
    },
    {
        "key": "monolith_micro", "topic": "Monolith vs microservices explained simply", "hook": "MONOLITH VS MICROSERVICES", "keyword": "MICRO",
        "link": "https://en.wikipedia.org/wiki/Microservices",
        "hook_line": "Why did Netflix break its app into hundreds of pieces?",
        "simple_title": "ONE SHOP VS A MALL",
        "simple": [("🏪", "Monolith = one big shop", "everything in one place"), ("🏬", "Microservices = a mall", "each shop runs alone"),
                   ("🔥", "One shop catches fire?", "the mall stays open")],
        "simple_say": "A monolith is one big shop where everything lives together. Microservices are a mall, where each shop runs on its own. If one shop catches fire, the rest of the mall stays open.",
        "answer": [("🚀", "Start with a monolith", "simple and fast to build"), ("📦", "Split when teams grow", "deploy services alone"),
                   ("🕸️", "Cost: network complexity", "monitoring, retries")],
        "answer_say": "The mature answer: start with a monolith because it's simple. Split into microservices when teams and traffic grow. The cost is network calls, monitoring and failures between services.",
    },
    {
        "key": "rate_limiting", "topic": "Rate limiting explained simply", "hook": "RATE LIMITING EXPLAINED", "keyword": "LIMIT",
        "link": "https://en.wikipedia.org/wiki/Token_bucket",
        "hook_line": "Why does an OTP page say try again after thirty seconds?",
        "simple_title": "THE TOKEN BUCKET",
        "simple": [("🪣", "Bucket of tokens", "say 10 tokens"), ("🎟️", "Each request costs one", "empty bucket = blocked"),
                   ("💧", "Refills slowly", "1 token per second")],
        "simple_say": "Picture a bucket of tokens. Every request costs one token. When the bucket is empty, you're blocked. It refills slowly, say one token every second.",
        "answer": [("🛡️", "Stops abuse", "brute force, bots, DDoS"), ("🔢", "Return HTTP 429", "too many requests"),
                   ("🗄️", "Store counts in Redis", "shared by all servers")],
        "answer_say": "Say rate limiting stops brute force and bot traffic. The server returns HTTP four twenty nine. In a real system, the counters live in Redis, so every server shares them.",
    },
    {
        "key": "merge_rebase", "topic": "Git merge vs rebase explained simply", "hook": "MERGE OR REBASE", "keyword": "GIT",
        "link": "https://git-scm.com/book/en/v2/Git-Branching-Rebasing",
        "hook_line": "Merge or rebase? Seniors argue about this all day.",
        "simple_title": "TWO WAYS TO JOIN",
        "simple": [("🔀", "Merge", "keeps both histories + a knot"), ("📏", "Rebase", "replays your commits on top"),
                   ("🧹", "Rebase = clean line", "but rewrites history")],
        "simple_say": "Merge joins two branches and keeps both histories, with a merge commit as the knot. Rebase replays your commits on top of main, giving one clean line, but it rewrites history.",
        "answer": [("🙅", "Never rebase shared", "branches others use"), ("🧽", "Rebase your local work", "before opening a PR"),
                   ("🤝", "Merge into main", "safe and traceable")],
        "answer_say": "The golden rule: never rebase a branch other people are using. Rebase your own local work to tidy it up, then merge into main.",
    },
]

# ---------------------------------------------------------------------------
# Quizzes: hook -> question with 4 options, countdown, reveal + why -> CTA
# `say` is the spoken question (keep the words "three" and "answer" out of it); `code` is shown on screen.
# ---------------------------------------------------------------------------

QUIZ_LIBRARY: list[dict[str, Any]] = [
    {"key": "float_sum", "hook": "PYTHON OUTPUT QUIZ", "hook_line": "Most developers get this wrong.",
     "question": "What does this print?", "code": "print(0.1 + 0.2 == 0.3)",
     "say": "What does this Python code print?", "options": ["True", "False", "Error", "None"], "correct": 1,
     "why": "False. Computers store decimals in binary, so zero point one plus zero point two is really zero point three zero zero zero four."},
    {"key": "mutable_default", "hook": "PYTHON TRAP QUIZ", "hook_line": "This Python trap catches seniors too.",
     "question": "What does the second call print?", "code": "def add(x, items=[]):\n    items.append(x)\n    return items\n\nadd(1)\nprint(add(2))",
     "say": "We call add twice. What does the second call print?", "options": ["[2]", "[1, 2]", "[2, 1]", "Error"], "correct": 1,
     "why": "One comma two. The default list is created only once, so every call shares the same list."},
    {"key": "typeof_null", "hook": "JAVASCRIPT WEIRDNESS QUIZ", "hook_line": "JavaScript is weird. Prove you know it.",
     "question": "What does this return?", "code": "typeof null",
     "say": "In JavaScript, what does type of null return?", "options": ["\"null\"", "\"undefined\"", "\"object\"", "Error"], "correct": 2,
     "why": "Object. It's a bug from the first version of JavaScript, and fixing it now would break the web."},
    {"key": "round_half", "hook": "ROUNDING TRAP QUIZ", "hook_line": "Ninety percent of people guess wrong here.",
     "question": "What does this print?", "code": "print(round(2.5))",
     "say": "What does round of two point five print in Python?", "options": ["2", "3", "2.5", "Error"], "correct": 0,
     "why": "Two. Python uses banker's rounding, so halves round to the nearest even number."},
    {"key": "list_alias", "hook": "REFERENCE TRAP QUIZ", "hook_line": "This bug has crashed real production code.",
     "question": "What does this print?", "code": "a = [1, 2]\nb = a\nb.append(3)\nprint(a)",
     "say": "We append to b. What does printing a show?", "options": ["[1, 2]", "[1, 2, 3]", "[3]", "Error"], "correct": 1,
     "why": "One two three. b equals a doesn't copy the list. Both names point to the same list."},
    {"key": "bfs_ds", "hook": "DSA BASICS QUIZ", "hook_line": "If you can't answer this, revise DSA today.",
     "question": "Which data structure does BFS use?", "code": "",
     "say": "Breadth first search uses which data structure?", "options": ["Stack", "Queue", "Heap", "Hash map"], "correct": 1,
     "why": "A queue. BFS visits nodes level by level, first in, first out. DFS is the one that uses a stack."},
    {"key": "quicksort_worst", "hook": "SORTING INTERVIEW QUIZ", "hook_line": "An interviewer asked me this last week.",
     "question": "Quicksort's worst-case time?", "code": "",
     "say": "What is the worst case time complexity of quicksort?", "options": ["O(n)", "O(n log n)", "O(n²)", "O(log n)"], "correct": 2,
     "why": "O of n squared. It happens when the pivot is always the smallest or largest, like an already sorted array."},
    {"key": "js_minus", "hook": "JAVASCRIPT MATH QUIZ", "hook_line": "JavaScript maths will break your brain.",
     "question": "What does this return?", "code": "\"5\" - 2",
     "say": "In JavaScript, what is the string five minus two?", "options": ["\"52\"", "3", "NaN", "Error"], "correct": 1,
     "why": "Three. Minus only works on numbers, so JavaScript turns the string into a number. But plus would give fifty two."},
    {"key": "floor_div", "hook": "PYTHON DIVISION QUIZ", "hook_line": "Even good programmers miss this one.",
     "question": "What does this print?", "code": "print(-7 // 2)",
     "say": "What does minus seven floor divided by two print in Python?", "options": ["-3", "-4", "-3.5", "3"], "correct": 1,
     "why": "Minus four. Floor division always rounds down, towards negative infinity, not towards zero."},
    {"key": "having", "hook": "SQL INTERVIEW QUIZ", "hook_line": "Every SQL interview has this question.",
     "question": "Which clause filters after GROUP BY?", "code": "SELECT dept, COUNT(*)\nFROM emp\nGROUP BY dept\n???? COUNT(*) > 5",
     "say": "Which clause filters the groups after group by?", "options": ["WHERE", "HAVING", "ORDER BY", "LIMIT"], "correct": 1,
     "why": "Having. Where filters rows before grouping. Having filters the groups after."},
    {"key": "bool_string", "hook": "PYTHON TRUTHY QUIZ", "hook_line": "This looks obvious. It isn't.",
     "question": "What does this print?", "code": "print(bool(\"False\"))",
     "say": "What does bool of the string False print?", "options": ["True", "False", "Error", "None"], "correct": 0,
     "why": "True. Any non empty string is truthy, even the word False."},
    {"key": "stable_sort", "hook": "SORTING TRICK QUIZ", "hook_line": "Only real DSA people know this one.",
     "question": "Which sort is NOT stable?", "code": "",
     "say": "Which of these sorting algorithms is not stable?", "options": ["Merge sort", "Insertion sort", "Quick sort", "Bubble sort"], "correct": 2,
     "why": "Quick sort. Its swaps can jump equal elements past each other, so their original order isn't kept."},
    {"key": "hashmap_avg", "hook": "HASHMAP BASICS QUIZ", "hook_line": "Every coding interview depends on this fact.",
     "question": "Average lookup time in a hash map?", "code": "",
     "say": "What is the average lookup time in a hash map?", "options": ["O(1)", "O(log n)", "O(n)", "O(n²)"], "correct": 0,
     "why": "O of one on average. The hash tells you exactly where to look. With many collisions, the worst case is O of n."},
    {"key": "is_vs_eq", "hook": "PYTHON IDENTITY QUIZ", "hook_line": "Most Python learners confuse these two.",
     "question": "What does this print?", "code": "a = [1, 2]\nb = [1, 2]\nprint(a == b, a is b)",
     "say": "Two lists with the same values. What does this print?", "options": ["True True", "True False", "False True", "False False"], "correct": 1,
     "why": "True, False. Double equals compares the values. Is checks whether they are the very same object."},
]

LETTERS = "ABCD"


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

import json as _json
import os as _os
import subprocess as _subprocess
import sys as _sys

_RUNNER = """
import json, sys
spec = json.loads(sys.stdin.read())
ns = {}
exec(spec["code"], ns)
fn = ns[spec["func"]]
for args, expected in spec["tests"]:
    got = fn(*args)
    if got != expected:
        print(json.dumps({"args": args, "expected": expected, "got": repr(got)}))
        sys.exit(1)
"""


def check_dsa(entry: dict[str, Any]) -> str | None:
    """Runs the entry's tests in a separate, isolated Python with no secrets in its environment.
    Returns None when they pass, else the reason. Gemini output goes through here too, so it is untrusted."""
    tests = entry.get("tests") or []
    if len(tests) < 2:
        return "needs at least 2 tests"
    spec = {"code": entry["snippet"] + "\n\n" + entry.get("harness", ""), "func": entry["func"], "tests": tests}
    env = {k: _os.environ[k] for k in ("PATH", "SYSTEMROOT") if k in _os.environ}
    try:
        res = _subprocess.run([_sys.executable, "-I", "-c", _RUNNER], input=_json.dumps(spec), capture_output=True,
                              text=True, timeout=10, env=env)
    except _subprocess.TimeoutExpired:
        return "tests timed out"
    if res.returncode:
        return (res.stdout or res.stderr).strip()[-300:] or "tests failed"
    return None


def check_quiz(entry: dict[str, Any]) -> str | None:
    say = entry.get("say", "").lower()
    if any(w in say for w in ("three", "answer")):
        return "spoken question must not contain 'three' or 'answer' (they time the countdown and the reveal)"
    if len(entry.get("options") or []) != 4 or entry.get("correct") not in range(4):
        return "needs 4 options and a correct index 0-3"
    return None


# ---------------------------------------------------------------------------
# Queue items (explicit storyboards, rendered by storyboard.from_spec)
# ---------------------------------------------------------------------------

def _steps(rows: list) -> list[dict[str, str]]:
    return [{"icon": r[0], "title": r[1], "detail": r[2]} for r in rows]


def dsa_item(e: dict[str, Any], source: str = "dsa_library") -> dict[str, Any]:
    n = e["narration"]
    example = list(e.get("example") or [])
    return {
        "id": f"dsa-{e['key']}".replace("_", "")[:40],
        "topic": f"LeetCode {e['number']} {e['title']} - {e['pattern'].title()}",
        "keyword": "LEETCODE", "keyword_spoken": "leetcode", "category": "dsa",
        "hook": e["hook"], "script": n["how"], "link": e["link"],
        "code": {"language": "python", "filename": e["func"].split("_")[0] + ".py", "snippet": e["snippet"]},
        "caption": f"LeetCode {e['number']}: {e['title']} 🧠 Save this for your next interview",
        "source": source, "status": "queued", "dsa": {"library": e["key"]},
        "storyboard": [
            {"type": "hook", "narration": n["hook"], "kicker": "LEETCODE TRICK"},
            {"type": "problem", "narration": n["problem"], "data": {
                "source": "LeetCode", "number": e["number"], "title": e["title"], "difficulty": e["difficulty"],
                "statement": e["statement"], "example": example[:8]}},
            {"type": "naive", "narration": n["naive"], "kicker": "THE OBVIOUS WAY", "optional": True,
             "data": {"label": e["naive"][0], "items": example[:6] or [8, 4, 2, 1], "cost": e["naive"][1]}},
            {"type": "how", "narration": n["how"], "kicker": "THE SMART WAY", "stretchable": True,
             "data": {"title": e["pattern"], "steps": _steps(e["steps"])}},
            {"type": "code", "narration": n["code"], "kicker": f"LEETCODE {e['number']}",
             "data": {"title": "THE CODE", "focus": e.get("focus", []), "stamps": e.get("stamps")}},
        ],
    }


def interview_item(e: dict[str, Any], source: str = "interview_library") -> dict[str, Any]:
    return {
        "id": f"intv-{e['key']}".replace("_", "")[:40],
        "topic": e["topic"], "keyword": e["keyword"], "category": "interview",
        "hook": e["hook"], "script": e["simple_say"], "link": e["link"],
        "caption": f"{e['topic']} 🎯 Save it before your interview",
        "source": source, "status": "queued",
        "storyboard": [
            {"type": "hook", "narration": e["hook_line"], "kicker": "INTERVIEW QUESTION"},
            {"type": "how", "narration": e["simple_say"], "kicker": "IN SIMPLE WORDS", "stretchable": True,
             "data": {"title": e["simple_title"], "steps": _steps(e["simple"])}},
            {"type": "use_cases", "narration": e["answer_say"], "kicker": "IN THE INTERVIEW", "stretchable": True,
             "data": {"title": "SAY THIS", "cards": _steps(e["answer"])}},
        ],
    }


def quiz_item(e: dict[str, Any], source: str = "quiz_library") -> dict[str, Any]:
    letter = LETTERS[e["correct"]]
    spoken = f"{e['say']} Comment your answer. Three, two, one. The answer is {letter}. {e['why']}"
    return {
        "id": f"quiz-{e['key']}".replace("_", "")[:40],
        "topic": f"{e['hook'].title()} - {e['question']} {e.get('code', '').splitlines()[0] if e.get('code') else ''}".strip(),
        "keyword": "QUIZ", "category": "quiz", "hook": e["hook"], "script": spoken,
        "link": f"https://www.instagram.com/code_tho_samsaram/?quiz={e['key']}",
        "code": {"language": "python", "filename": "quiz.py", "snippet": e.get("code") or e["question"]},
        "caption": f"Quiz time 🧩 {e['question']} Comment A, B, C or D before the reveal 👇",
        "source": source, "status": "queued",
        "storyboard": [
            {"type": "hook", "narration": e["hook_line"], "kicker": "QUICK QUIZ"},
            {"type": "quiz", "narration": spoken, "stretchable": True,
             "data": {"question": e["question"], "code": e.get("code", ""), "options": e["options"], "correct": e["correct"]}},
        ],
    }


BUILDERS = {"dsa": (DSA_LIBRARY, dsa_item, check_dsa), "interview": (INTERVIEW_LIBRARY, interview_item, None),
            "quiz": (QUIZ_LIBRARY, quiz_item, check_quiz)}
