// @vitest-environment jsdom
import { describe, expect, it } from 'vitest';
import { parseReadingDocument, readingProperties, containReaderKeys } from './readingDocument';

describe('reading documents', () => {
  it('separates BOM and CRLF frontmatter and renders block tags as individual properties', () => {
    const parsed = parseReadingDocument('\uFEFF---\r\ntitle: Guide\r\ntags:\r\n  - BASIC\r\n  - learning\r\npublished: false\r\ncount: 0\r\n---\r\n# Start\r\nBody');
    expect(parsed.body).toContain('# Start');
    expect(parsed.body).not.toContain('published:');
    expect(readingProperties(parsed.frontmatter)).toEqual(expect.arrayContaining([
      {key:'tags',value:'BASIC'}, {key:'tags',value:'learning'}, {key:'published',value:'false'}, {key:'count',value:'0'},
    ]));
  });
  it('keeps ordinary markdown intact', () => {
    expect(parseReadingDocument('# Heading\nBody').body).toBe('# Heading\nBody');
  });
  it('exits full-screen with Escape only while reading full-screen', () => {
    let exits = 0;
    const root = document.createElement('article');
    containReaderKeys(new KeyboardEvent('keydown', {key:'Escape'}), root, false, () => exits++);
    expect(exits).toBe(0);
    containReaderKeys(new KeyboardEvent('keydown', {key:'Escape'}), root, true, () => exits++);
    expect(exits).toBe(1);
  });
});
