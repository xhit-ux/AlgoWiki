export const FIXED_TRICK_TERM_ORDER = [
  "数学",
  "动态规划",
  "字符串",
  "计算几何",
  "数据结构",
  "图论",
  "其他",
];

export const TRICK_TERM_TONE_CLASS_MAP = Object.freeze({
  数学: "trick-term-tone--math",
  动态规划: "trick-term-tone--dp",
  字符串: "trick-term-tone--string",
  计算几何: "trick-term-tone--geometry",
  数据结构: "trick-term-tone--ds",
  图论: "trick-term-tone--graph",
  其他: "trick-term-tone--other",
});

const trickTermOrderMap = new Map(
  FIXED_TRICK_TERM_ORDER.map((name, index) => [name, index]),
);

const collator = new Intl.Collator("zh-u-co-pinyin", {
  sensitivity: "base",
  numeric: true,
  ignorePunctuation: true,
});

export function sortFixedTrickTerms(items) {
  const source = Array.isArray(items) ? [...items] : [];
  source.sort((left, right) => {
    const leftName = String(left?.name || "");
    const rightName = String(right?.name || "");
    const leftOrder = trickTermOrderMap.get(leftName);
    const rightOrder = trickTermOrderMap.get(rightName);

    if (leftOrder != null || rightOrder != null) {
      return (leftOrder ?? 999) - (rightOrder ?? 999);
    }

    return collator.compare(leftName, rightName);
  });
  return source;
}

export function getTrickTermToneClass(termName) {
  return (
    TRICK_TERM_TONE_CLASS_MAP[String(termName || "").trim()] ||
    "trick-term-tone--default"
  );
}
