import { describe, expect, it } from "vitest";
import { createVariantDocument, syncVariantMetadata } from "./documentVariant";

describe("document variants", () => {
  it("creates a child with stable parent metadata", () => {
    const result = createVariantDocument("---\ntitle: Parent\ntags: [one]\n---\nBody", "/notes/parent.md", "variant-1");
    expect(result).toContain("id: variant-1"); expect(result).toContain("parent: /notes/parent.md"); expect(result).toContain("Body");
  });
  it("syncs parent metadata without replacing child relationship or body", () => {
    const result = syncVariantMetadata("---\ntitle: Updated\ntags: [two]\n---\nParent", "---\nid: child\nparent: /p.md\n---\nChild");
    expect(result).toContain("title: Updated"); expect(result).toContain("id: child"); expect(result).toContain("Child");
  });
});
