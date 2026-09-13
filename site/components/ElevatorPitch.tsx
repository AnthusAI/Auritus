/**
 * The home page demo copy. Auritus narrates its own pitch, so this text is
 * both the thing you read and the thing the player speaks -- roughly thirty
 * seconds at a normal narration pace.
 *
 * The closing line is marked data-auritus-ignore so the credit is not read
 * aloud as part of the pitch.
 */
export function ElevatorPitch() {
  return (
    <>
      <p>
        Press play. What you hear is this page reading itself.
      </p>
      <p>
        Auritus turns any article into audio on demand, from a single script
        tag &mdash; no pre-recording, no studio, no per-article cost.
      </p>
      <p>
        You choose the voice model. You decide where the text goes. Your own
        GPU does the work, and AWS picks up the slack when it cannot.
      </p>
      <p>
        It&apos;s open source, and every article on your site can speak, with
        the choices that matter still yours.
      </p>
      <p data-auritus-ignore>
        Narrated by Auritus with Kokoro (af_heart) &mdash; the same embed
        documented in Usage.
      </p>
    </>
  );
}
