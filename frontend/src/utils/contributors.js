function normalizeUser(user) {
  const id = Number(user?.id);
  if (!Number.isInteger(id) || id <= 0) return null;
  return {
    id,
    username: String(user?.username || "-"),
    role: user?.role || "",
    school_name: user?.school_name || "",
    avatar_url: user?.avatar_url || "",
    bio: user?.bio || "",
    date_joined: user?.date_joined || "",
  };
}

function toTimeValue(value) {
  if (!value) return null;
  const timestamp = new Date(value).getTime();
  return Number.isNaN(timestamp) ? null : timestamp;
}

function compareTime(a, b) {
  const aValue = toTimeValue(a);
  const bValue = toTimeValue(b);
  if (aValue !== null && bValue !== null) return aValue - bValue;
  if (aValue !== null) return -1;
  if (bValue !== null) return 1;
  return 0;
}

export function aggregateCreatorContributors(
  items,
  { userKey = "created_by", getUser = null, getTime = null } = {},
) {
  const source = Array.isArray(items) ? items : [];
  const contributorMap = new Map();

  for (const item of source) {
    const rawUser =
      typeof getUser === "function" ? getUser(item) : item?.[userKey];
    const user = normalizeUser(rawUser);
    if (!user) continue;

    const contributedAt =
      typeof getTime === "function"
        ? getTime(item)
        : item?.created_at || item?.published_at || item?.updated_at || null;

    const existing = contributorMap.get(user.id);
    if (existing) {
      existing.created_entry_count += 1;
      if (compareTime(contributedAt, existing.first_contributed_at) < 0) {
        existing.first_contributed_at = contributedAt;
      }
      if (compareTime(contributedAt, existing.last_contributed_at) > 0) {
        existing.last_contributed_at = contributedAt;
      }
      continue;
    }

    contributorMap.set(user.id, {
      user,
      is_creator: true,
      approved_revision_count: 0,
      created_entry_count: 1,
      first_contributed_at: contributedAt,
      last_contributed_at: contributedAt,
    });
  }

  return [...contributorMap.values()].sort((a, b) => {
    const firstDiff = compareTime(a.first_contributed_at, b.first_contributed_at);
    if (firstDiff !== 0) return firstDiff;
    const lastDiff = compareTime(a.last_contributed_at, b.last_contributed_at);
    if (lastDiff !== 0) return lastDiff;
    return String(a.user?.username || "").localeCompare(
      String(b.user?.username || ""),
      "zh-CN",
    );
  });
}
