import { describe, it, expect, vi, beforeEach } from "vitest"
import {
  searchGrounded,
  generateBananaAsset,
  syncGoogleDriveVault,
  getDriveSyncStatus,
  executeGoogleCode,
} from "./ApiBridge"

describe("BrowserUI ApiBridge Google integration", () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it("calls /api/google/grounded-search with query", async () => {
    const mockResponse = {
      status: "success",
      query: "uDOS architecture",
      model: "gemini-2.0-flash",
      summary: "uDOS is a local-first system.",
      citations: [{ index: 1, title: "Doc", uri: "https://example.org", snippet: "uDOS info" }],
      live_grounded: false,
    }
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    } as any)

    const res = await searchGrounded("uDOS architecture")
    expect(res.status).toBe("success")
    expect(res.summary).toContain("local-first")
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/google/grounded-search"),
      expect.objectContaining({ method: "POST" })
    )
  })

  it("calls /api/google/image/generate with prompt and style", async () => {
    const mockResponse = {
      status: "success",
      model: "imagen-3.0-generate-002",
      style_preset: "mono_teletext",
      asset_id: "nano_banana_12345",
      prompt: "teletext grid",
    }
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    } as any)

    const res = await generateBananaAsset("teletext grid", "mono_teletext")
    expect(res.status).toBe("success")
    expect(res.model).toBe("imagen-3.0-generate-002")
    expect(res.asset_id).toBe("nano_banana_12345")
  })

  it("calls /api/google/drive/scan with vault_path", async () => {
    const mockResponse = {
      status: "success",
      vault_path: "/Users/fredbook/Vault",
      scanned: 12,
      updated: 2,
      unchanged: 10,
      total_records: 12,
    }
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    } as any)

    const res = await syncGoogleDriveVault("/Users/fredbook/Vault")
    expect(res.status).toBe("success")
    expect(res.scanned).toBe(12)
    expect(res.updated).toBe(2)
  })

  it("calls /api/google/drive/status to inspect mirror", async () => {
    const mockResponse = {
      status: "success",
      vault_path: "/Users/fredbook/Vault",
      total_files: 5,
      mirrored_count: 4,
      modified_count: 1,
      unmirrored_count: 0,
      files: {},
    }
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    } as any)

    const res = await getDriveSyncStatus("/Users/fredbook/Vault")
    expect(res.status).toBe("success")
    expect(res.mirrored_count).toBe(4)
    expect(res.modified_count).toBe(1)
  })

  it("calls /api/google/code/execute with code block", async () => {
    const mockResponse = {
      status: "success",
      language: "python",
      code: "print('hello')",
      output: "hello\n",
      outcome: "OUTCOME_OK",
      live_execution: false,
    }
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    } as any)

    const res = await executeGoogleCode("print('hello')", "python")
    expect(res.status).toBe("success")
    expect(res.output).toContain("hello")
    expect(res.outcome).toBe("OUTCOME_OK")
  })

  it("calls /api/host/capabilities to probe host OS capabilities", async () => {
    const mockCaps = {
      os: "darwin",
      platform: "macOS-27.0",
      host_native: { safari: { available: true }, notes: { available: true } },
      capabilities: { browser_intake: true, notes_export: true, reminders_export: true },
    }
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => mockCaps,
    } as any)

    const { getHostCapabilities } = await import("./ApiBridge")
    const res = await getHostCapabilities()
    expect(res.os).toBe("darwin")
    expect(res.capabilities.browser_intake).toBe(true)
  })

  it("calls /api/host/safari/active to get current tab", async () => {
    const mockTab = {
      ok: true,
      running: true,
      url: "https://apple.com",
      title: "Apple",
    }
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => mockTab,
    } as any)

    const { getActiveSafariTab } = await import("./ApiBridge")
    const res = await getActiveSafariTab()
    expect(res.ok).toBe(true)
    expect(res.url).toBe("https://apple.com")
  })

  it("calls /api/host/notes/export with title and markdown body", async () => {
    const mockNotes = {
      ok: true,
      title: "Architecture Brief",
      folder: "Default",
      app: "com.apple.Notes",
    }
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => mockNotes,
    } as any)

    const { exportToAppleNotes } = await import("./ApiBridge")
    const res = await exportToAppleNotes("Architecture Brief", "# Brief\nContent")
    expect(res.ok).toBe(true)
    expect(res.title).toBe("Architecture Brief")
  })

  it("calls /api/host/reminders/export with title and notes", async () => {
    const mockRem = {
      ok: true,
      title: "Test task",
      list: "Work",
      app: "com.apple.reminders",
    }
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => mockRem,
    } as any)

    const { exportToAppleReminders } = await import("./ApiBridge")
    const res = await exportToAppleReminders("Test task", "Details", "Work")
    expect(res.ok).toBe(true)
    expect(res.list).toBe("Work")
  })

  it("calls /api/host/notes/intake with query parameters", async () => {
    const mockNotes = {
      ok: true,
      items: [
        {
          id: "n1",
          title: "Architecture Brief",
          body: "Content",
          folder: "Work",
          modification_date: "2026-09-09T08:00:00Z",
        },
      ],
    }
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => mockNotes,
    } as any)

    const { intakeAppleNotes } = await import("./ApiBridge")
    const res = await intakeAppleNotes({ folder: "Work", limit: 5 })
    expect(res.ok).toBe(true)
    expect(res.items.length).toBe(1)
    expect(res.items[0].title).toBe("Architecture Brief")
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining("/api/host/notes/intake?folder=Work&limit=5"),
      expect.anything()
    )
  })

  it("calls /api/host/reminders/intake with query parameters", async () => {
    const mockRem = {
      ok: true,
      items: [
        {
          id: "r1",
          title: "Audit Storage",
          notes: "UDOS_HOME compliance",
          completed: false,
          list: "Tasks",
        },
      ],
    }
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => mockRem,
    } as any)

    const { intakeAppleReminders } = await import("./ApiBridge")
    const res = await intakeAppleReminders({ listName: "Tasks", limit: 10, completed: false })
    expect(res.ok).toBe(true)
    expect(res.items.length).toBe(1)
    expect(res.items[0].title).toBe("Audit Storage")
    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining("/api/host/reminders/intake?list=Tasks&limit=10&completed=false"),
      expect.anything()
    )
  })
})


