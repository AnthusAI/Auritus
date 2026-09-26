Feature: Operator authentication on the Auritus API
  Operators prove who they are with a Cognito access token issued by the
  Auritus user pool to the CLI or the web console. The API gateway
  authorizer and the router both verify that token's signature against the
  user pool's published signing keys, its issuer, its expiry, that it is an
  access token, and that it was issued to an Auritus client. A worker that
  is not an operator may only touch the one job whose single-use job token
  it holds. Nothing else gets through: not a forged token, not an expired
  token, and not a bare "Bearer" header with an arbitrary value.

  Scenario: The authorizer admits a valid operator access token
    Given the operator presents an operator access token signed by the user pool
    When the authorizer checks that token
    Then the authorizer admits the request for that operator

  Scenario Outline: The authorizer rejects tokens that are not valid operator access tokens
    Given the operator presents <token description>
    When the authorizer checks that token
    Then the authorizer rejects the request

    Examples:
      | token description                                        |
      | an operator access token signed by a key the pool never published |
      | an operator access token that expired an hour ago        |
      | an operator ID token signed by the user pool             |
      | an operator access token issued to an unknown client     |
      | an operator access token issued by a different user pool |
      | an unsigned operator access token                        |
      | an operator access token signed with a shared secret     |
      | the bare bearer value "x"                                |

  Scenario: The authorizer rejects a request without a bearer token
    Given the operator presents no authorization header
    When the authorizer checks that token
    Then the authorizer rejects the request

  Scenario: An operator route rejects a bare bearer header
    Given the operator presents the bare bearer value "x"
    When that token calls the admin overview
    Then the API refuses the request as forbidden

  Scenario: An operator route admits a valid operator access token
    Given the operator presents an operator access token signed by the user pool
    When that token calls the admin overview
    Then the API answers successfully

  Scenario Outline: Job mutation routes reject a bare bearer header
    Given a pending job awaiting a worker
    And the operator presents the bare bearer value "x"
    When that token calls the job <route> route
    Then the API refuses the request as forbidden
    And the job is still pending and unclaimed

    Examples:
      | route          |
      | claim          |
      | done           |
      | failed         |
      | presign-upload |

  Scenario Outline: Job claims reject forged and expired operator tokens
    Given a pending job awaiting a worker
    And the operator presents <token description>
    When that token calls the job claim route
    Then the API refuses the request as forbidden
    And the job is still pending and unclaimed

    Examples:
      | token description                                        |
      | an operator access token signed by a key the pool never published |
      | an operator access token that expired an hour ago        |

  Scenario: A worker holding the job token may claim that job
    Given a pending job awaiting a worker
    And the worker presents the job's own single-use job token
    When that token calls the job claim route
    Then the API answers successfully
    And the job is claimed

  Scenario: An operator's local worker may claim a job with an access token
    Given a pending job awaiting a worker
    And the operator presents an operator access token signed by the user pool
    When that token calls the job claim route
    Then the API answers successfully
    And the job is claimed
