const rungs = [
  {
    title: "Fork it",
    body: "MIT licensed. Deploy it yourself. Anthus does nothing and charges nothing.",
    price: "No cost",
  },
  {
    title: "Self-setup, managed",
    body: "You run the CloudFormation template in your account; we operate it and keep the deployment updated. We update our own deployments first.",
    price: "$20 a month",
  },
  {
    title: "Assisted setup, managed",
    body: "We run the setup session with you, then operate it. We keep the deployment updated, updating our own deployments first.",
    price: "$20 a month",
    note: "and $100 once",
  },
  {
    title: "Professional services",
    body: "We adapt a deployment to your exact needs, with or without the managed service.",
    price: "Quoted",
  },
];

const faqItems = [
  {
    question: "What happens if I stop paying?",
    answer:
      "Your deployment is in your account and stays there. We stop operating it. Nothing is deleted by us.",
  },
  {
    question: "What does managed actually mean?",
    answer:
      "We apply updates, we watch it, and we go first — our own deployments take every release before yours.",
  },
  {
    question: "Can I start self-setup and move to assisted?",
    answer: "Yes, and the reverse.",
  },
];

export function DelegatedResponsibility() {
  return (
    <section
      id="pricing"
      aria-labelledby="pricing-title"
      className="pricing-section"
    >
      <div className="pricing-header">
        <div>
          <span className="pricing-badge">Delegated responsibility</span>
          <p className="pricing-intro">
            You can run the whole stack yourself. If you want help, we can
            operate it, set it up with you, or adapt a deployment to what you
            need.
          </p>
        </div>
        <h2 id="pricing-title">You choose how much we help</h2>
      </div>

      <div className="pricing-grid">
        {rungs.map((rung) => (
          <div key={rung.title} className="pricing-card">
            <h3 className="pricing-card-title">{rung.title}</h3>
            <p className="pricing-card-body">{rung.body}</p>
            <div className="pricing-card-bottom">
              <span className="pricing-card-price">{rung.price}</span>
              {rung.note ? (
                <span className="pricing-card-note">{rung.note}</span>
              ) : null}
            </div>
          </div>
        ))}
      </div>

      <div className="pricing-faq">
        <h3 className="pricing-faq-title">Straight answers</h3>
        <div className="pricing-faq-grid">
          {faqItems.map((item) => (
            <div key={item.question} className="pricing-faq-card">
              <h4 className="pricing-faq-question">{item.question}</h4>
              <p className="pricing-faq-answer">{item.answer}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
