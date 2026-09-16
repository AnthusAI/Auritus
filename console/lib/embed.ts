/**
 * Embed snippet generation for Auritus sites.
 * Ported from cli/src/auritus/embed.py:format_embed_snippet
 */

export function formatEmbedSnippet(params: {
  siteKey: string;
  name?: string;
  byline?: string;
  scriptSrc?: string;
}): string {
  const { siteKey, name = '', byline = '', scriptSrc = 'https://aurit.us/embed.js' } = params;
  return `<script\n  src="${scriptSrc}"\n  data-auritus-site-key="${siteKey}"\n  data-auritus-name="${name}"\n  data-auritus-byline="${byline}"\n></script>`;
}
