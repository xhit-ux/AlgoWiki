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

function mergeContributorRecord(
  contributorMap,
  {
    user,
    is_creator = false,
    approved_revision_count = 0,
    created_entry_count = 0,
    first_contributed_at = null,
    last_contributed_at = null,
  },
) {
  const normalizedUser = normalizeUser(user);
  if (!normalizedUser) return;

  const normalizedApprovedRevisionCount = Math.max(
    0,
    Number(approved_revision_count || 0),
  );
  const normalizedCreatedEntryCount = Math.max(0, Number(created_entry_count || 0));
  const firstContributedAt = first_contributed_at || last_contributed_at || null;
  const lastContributedAt = last_contributed_at || first_contributed_at || null;

  const existing = contributorMap.get(normalizedUser.id);
  if (existing) {
    existing.is_creator = existing.is_creator || !!is_creator;
    existing.created_entry_count += normalizedCreatedEntryCount;
    existing.approved_revision_count += normalizedApprovedRevisionCount;
    if (compareTime(firstContributedAt, existing.first_contributed_at) < 0) {
      existing.first_contributed_at = firstContributedAt;
    }
    if (compareTime(lastContributedAt, existing.last_contributed_at) > 0) {
      existing.last_contributed_at = lastContributedAt;
    }
    return;
  }

  contributorMap.set(normalizedUser.id, {
    user: normalizedUser,
    is_creator: !!is_creator,
    approved_revision_count: normalizedApprovedRevisionCount,
    created_entry_count: normalizedCreatedEntryCount,
    first_contributed_at: firstContributedAt,
    last_contributed_at: lastContributedAt,
  });
}

export function aggregateCreatorContributors(
  items,
  { userKey = "created_by", getUser = null, getTime = null } = {},
) {
  const source = Array.isArray(items) ? items : [];
  const contributorMap = new Map();

  for (const item of source) {
    const embeddedContributors = Array.isArray(item?.contributors)
      ? item.contributors
      : [];
    if (embeddedContributors.length) {
      for (const contributor of embeddedContributors) {
        mergeContributorRecord(contributorMap, {
          user: contributor?.user,
          is_creator: contributor?.is_creator,
          approved_revision_count: contributor?.approved_revision_count,
          created_entry_count: contributor?.is_creator ? 1 : 0,
          first_contributed_at:
            contributor?.first_contributed_at || contributor?.last_contributed_at,
          last_contributed_at:
            contributor?.last_contributed_at || contributor?.first_contributed_at,
        });
      }
      continue;
    }

    const rawUser =
      typeof getUser === "function" ? getUser(item) : item?.[userKey];
    const contributedAt =
      typeof getTime === "function"
        ? getTime(item)
        : item?.created_at || item?.published_at || item?.updated_at || null;

    mergeContributorRecord(contributorMap, {
      user: rawUser,
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
