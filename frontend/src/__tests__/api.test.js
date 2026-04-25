import { searchNotes, getRecentNotes, getNote, uploadFile, getConnections } from "../api";

function mockFetch(body, ok = true, status = 200) {
  global.fetch = jest.fn().mockResolvedValue({
    ok,
    status,
    json: () => Promise.resolve(body),
    text: () => Promise.resolve(typeof body === "string" ? body : JSON.stringify(body)),
  });
}

afterEach(() => jest.restoreAllMocks());

describe("searchNotes", () => {
  it("calls the correct endpoint", async () => {
    mockFetch({ results: [] });
    await searchNotes("vector embeddings");
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/search?q=vector%20embeddings"),
      expect.anything()
    );
  });

  it("returns parsed results", async () => {
    const results = [{ id: "1", title: "Note", preview: "...", relevance: 0.9 }];
    mockFetch({ results });
    const data = await searchNotes("test");
    expect(data.results).toEqual(results);
  });

  it("throws when response is not ok", async () => {
    mockFetch("Internal Server Error", false, 500);
    await expect(searchNotes("test")).rejects.toThrow();
  });
});

describe("getNote", () => {
  it("calls the correct endpoint", async () => {
    mockFetch({ id: "42", title: "My note" });
    await getNote("42");
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/notes/42"),
      expect.anything()
    );
  });

  it("throws when note is not found", async () => {
    mockFetch("Not Found", false, 404);
    await expect(getNote("999")).rejects.toThrow();
  });
});

describe("uploadFile", () => {
  it("sends a POST request with FormData", async () => {
    mockFetch({ id: "new-id", title: "uploaded.txt" });
    const file = new File(["content"], "uploaded.txt", { type: "text/plain" });
    await uploadFile(file);

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/notes/upload"),
      expect.objectContaining({ method: "POST" })
    );
    const body = global.fetch.mock.calls[0][1].body;
    expect(body).toBeInstanceOf(FormData);
    expect(body.get("file")).toBe(file);
  });

  it("throws when upload fails", async () => {
    mockFetch("Upload failed", false, 422);
    const file = new File(["x"], "bad.exe");
    await expect(uploadFile(file)).rejects.toThrow();
  });
});

describe("getRecentNotes", () => {
  it("calls the correct endpoint", async () => {
    mockFetch({ notes: [] });
    await getRecentNotes();
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/notes"),
      expect.anything()
    );
  });
});

describe("getConnections", () => {
  it("calls the correct endpoint", async () => {
    mockFetch({ nodes: [], links: [] });
    await getConnections();
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/connections/"),
      expect.anything()
    );
  });

  it("returns parsed graph data", async () => {
    const graph = { nodes: [{ id: "1", title: "Test" }], links: [] };
    mockFetch(graph);
    const data = await getConnections();
    expect(data).toEqual(graph);
  });

  it("throws when response is not ok", async () => {
    mockFetch("Internal Server Error", false, 500);
    await expect(getConnections()).rejects.toThrow();
  });
});
