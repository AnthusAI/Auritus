type JobsCommencementExcerptProps = {
  backendLabel: string;
};

/**
 * Shared commencement address excerpt so each TTS backend speaks the same words.
 * Features an editorial pull quote highlighting the speech's most iconic quote.
 */
export function JobsCommencementExcerpt({
  backendLabel,
}: JobsCommencementExcerptProps) {
  return (
    <>
      <h1>Stanford Commencement Address</h1>
      <p>
        I was lucky &mdash; I found what I loved to do early in life. Woz and I
        started Apple in my parents&#39; garage when I was 20. We worked hard,
        and in 10 years Apple had grown from just the two of us into a $2 billion
        company with over 4,000 employees. We had just released our finest
        creation &mdash; the Macintosh &mdash; a year earlier, and then I got
        fired. How can you get fired from a company you started?
      </p>
      <p>
        I didn&#39;t see it then, but it turned out that getting fired from
        Apple was the best thing that could have ever happened to me. The
        heaviness of being successful was replaced by the lightness of being a
        beginner again, less sure about everything. It freed me to enter one of
        the most creative periods of my life.
      </p>
      <blockquote className="pull-quote" data-auritus-ignore>
        <p>
          &ldquo;The only way to do great work is to love what you do. If you
          haven&#39;t found it yet, keep looking. Don&#39;t settle.&rdquo;
        </p>
      </blockquote>
      <p>
        Sometimes life hits you in the head with a brick. Don&#39;t lose faith.
        I&#39;m convinced that the only thing that kept me going was that I loved
        what I did. You&#39;ve got to find what you love. Your work is going to
        fill a large part of your life, and the only way to be truly satisfied is
        to do what you believe is great work. And the only way to do great work
        is to love what you do. If you haven&#39;t found it yet, keep looking.
        Don&#39;t settle.
      </p>
      <p data-auritus-ignore>
        This page speaks that excerpt with {backendLabel}. Steve Jobs delivered
        this address at Stanford University in 2005.
      </p>
    </>
  );
}
