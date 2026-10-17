import AnthusFooter from "anthus-footer";

const auritusFooterTheme = {
  background: "var(--paper-deep)",
  groupedBackground: "var(--panel)",
  foreground: "var(--ink)",
  mutedForeground: "var(--ink-muted)",
  link: "var(--ink)",
  fontFamilyBody: "var(--font-body), sans-serif",
  fontFamilyHeading: "var(--font-display), serif",
  maxWidth: "1180px",
};

export function SiteFooter() {
  return (
    <AnthusFooter
      siteId="auritus"
      mode="light"
      className="site-footer"
      description="Open-source, just-in-time narration for the web."
      additionalColumns={[
        {
          title: "Auritus",
          links: [
            { label: "Pricing", href: "/#pricing", external: false },
            { label: "Documentation", href: "/docs", external: false },
            { label: "Examples", href: "/examples", external: false },
            { label: "GitHub", href: "https://github.com/AnthusAI/Auritus" },
          ],
        },
      ]}
      theme={auritusFooterTheme}
    />
  );
}
