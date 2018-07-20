Feature: Tests if Knights are correctly implemented

  Scenario: Determine the nature of a knight
    Given I have a standard Schroedinger ChessBoard
    When I move piece (0,0) to (1,2)
    Then the move should be accepted
    Then the piece (1,2) should have nature N
    Then the piece (1,2) should not have nature Q

  Scenario: Perform an impossible move with a knight
    Given I have a standard Schroedinger ChessBoard
    When I move piece (0,0) to (1,2)
    When I move piece (1,2) to (1,1)
    Then the move should be rejected

  Scenario: Try to have too many knights
    Given I have a standard Schroedinger ChessBoard
    When I move piece (0,0) to (1,2)
    When Blacks move their left pawn
    When I move piece (1,0) to (2,2)
    Then the move should be accepted
    When Blacks move their left pawn
    When I move piece (2,0) to (3,2)
    Then the move should be rejected
