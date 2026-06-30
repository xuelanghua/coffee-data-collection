const DRAFT_INDEX_KEY = "coffee_draft_index";
const DRAFT_PREFIX = "coffee_draft:";

export class InMemoryDraftStorage {
  constructor() {
    this.items = new Map();
  }

  getItem(key) {
    return this.items.get(key) || null;
  }

  setItem(key, value) {
    this.items.set(key, String(value));
  }

  removeItem(key) {
    this.items.delete(key);
  }
}

export class LocalDraftStore {
  constructor({ storage, now = () => new Date().toISOString() }) {
    if (!storage) {
      throw new Error("storage is required");
    }
    this.storage = storage;
    this.now = now;
  }

  async saveDraft(draft) {
    if (!draft?.eventId) {
      throw new Error("draft.eventId is required");
    }
    const stored = {
      ...draft,
      updatedAt: this.now(),
    };
    this.storage.setItem(draftKey(draft.eventId), JSON.stringify(stored));
    this.storage.setItem(DRAFT_INDEX_KEY, JSON.stringify(addUnique(this.readIndex(), draft.eventId)));
    return stored;
  }

  async getDraft(eventId) {
    const raw = this.storage.getItem(draftKey(eventId));
    return raw ? JSON.parse(raw) : null;
  }

  async listDrafts() {
    const drafts = [];
    for (const eventId of this.readIndex()) {
      const draft = await this.getDraft(eventId);
      if (draft) {
        drafts.push(draft);
      }
    }
    return drafts.sort((left, right) => String(right.updatedAt).localeCompare(String(left.updatedAt)));
  }

  async removeDraft(eventId) {
    this.storage.removeItem(draftKey(eventId));
    this.storage.setItem(DRAFT_INDEX_KEY, JSON.stringify(this.readIndex().filter((item) => item !== eventId)));
  }

  readIndex() {
    const raw = this.storage.getItem(DRAFT_INDEX_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  }
}

function draftKey(eventId) {
  return `${DRAFT_PREFIX}${eventId}`;
}

function addUnique(items, item) {
  return items.includes(item) ? items : [...items, item];
}
