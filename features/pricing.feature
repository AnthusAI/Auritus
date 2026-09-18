Feature: Marketing site pricing and delegation ladder
  Auritus offers an open-source, self-hosted option alongside managed operations
  and assisted setup, matching the Anthus delegated responsibility model.

  Scenario: The pricing section offers a choice of how much help
    Given the aurit.us home page layout
    When I look at the delegated responsibility section
    Then it headlines that you choose how much we help
    And it states that you can run it yourself or enlist us
    And it offers four rungs:
      | rung                    | price       |
      | Fork it                 | No cost     |
      | Self-setup, managed     | $20 a month |
      | Assisted setup, managed | $20 a month |
      | Professional services   | Quoted      |
    And the assisted setup rung mentions a one-time fee of "$100 once"
    And the managed rungs state that Anthus keeps the deployment updated
    And they state that Anthus updates its own deployments first

  Scenario: The pricing section explains managed operation and cancellation
    Given the aurit.us home page layout
    When I look at the delegated responsibility section
    Then it states what happens if you stop paying
    And it states what managed actually means
    And it states that you can move between self-setup and assisted setup

  Scenario: Navigation and footer link to pricing
    Given the aurit.us home page layout
    Then the navigation header includes a link to "Pricing"
    And the footer includes a link to "Pricing"
