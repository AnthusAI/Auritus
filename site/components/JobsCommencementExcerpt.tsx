type GettysburgExcerptProps = {
  backendLabel: string;
};

/**
 * Shared public-domain excerpt so each TTS backend speaks the same words.
 */
export function GettysburgExcerpt({ backendLabel }: GettysburgExcerptProps) {
  return (
    <>
      <h1>Gettysburg Address</h1>
      <p>
        Four score and seven years ago our fathers brought forth on this
        continent, a new nation, conceived in Liberty, and dedicated to the
        proposition that all men are created equal.
      </p>
      <p>
        Now we are engaged in a great civil war, testing whether that nation,
        or any nation so conceived and so dedicated, can long endure. We are
        met on a great battle-field of that war. We have come to dedicate a
        portion of that field, as a final resting place for those who here gave
        their lives that that nation might live. It is altogether fitting and
        proper that we should do this.
      </p>
      <p data-auritus-ignore>
        This page speaks that excerpt with {backendLabel}. The Gettysburg
        Address is in the public domain.
      </p>
    </>
  );
}
