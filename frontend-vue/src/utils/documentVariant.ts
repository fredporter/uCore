import { parseDocument, serializeDocument, type Frontmatter } from "./frontmatterParser";

export function createVariantDocument(content: string, parentPath: string, variantId: string) {
  const parsed = parseDocument(content);
  const frontmatter: Frontmatter = { ...parsed.frontmatter, id: variantId, parent: parentPath, variant_of: String(parsed.frontmatter.id || parentPath), variant_created: new Date().toISOString(), status: "draft" };
  return serializeDocument(parsed.body, frontmatter);
}

export function syncVariantMetadata(parentContent: string, variantContent: string) {
  const parent = parseDocument(parentContent);
  const variant = parseDocument(variantContent);
  const relationship = Object.fromEntries(Object.entries(variant.frontmatter).filter(([key]) => ["id", "parent", "variant_of", "variant_created", "status"].includes(key)));
  return serializeDocument(variant.body, { ...parent.frontmatter, ...relationship });
}
