FUNCTION RunAgent(UserGoal):
    # Initialize the ongoing conversation state/memory
    AgentState = InitializeState(UserGoal)
    
    # Establish a safety guardrail
    ExecutionBudget = MaxStepsAllowed

    WHILE ExecutionBudget > 0:
        ExecutionBudget = ExecutionBudget - 1
        
        # 1. GENERATE DECISION
        # Pass the full state history to the intelligence engine
        AgentDecision = IntelligenceEngine.PredictNextStep(AgentState)
        AgentState.Record(AgentDecision)
        
        # 2. ROUTE DECISION
        # Case A: The engine has resolved the goal
        IF AgentDecision.IsTerminalState():
            RETURN AgentDecision.GetFinalOutput()
            
        # Case B: The engine requires external data/action
        ELSE IF AgentDecision.RequestsAction():
            Action = AgentDecision.GetActionDetails()
            
            # 3. EXECUTE ACTION
            TRY:
                Observation = Environment.Execute(Action.Identifier, Action.Parameters)
            CATCH ExecutionError as Error:
                Observation = Environment.FormatError(Error)
                
            # 4. UPDATE MEMORY
            AgentState.Record(Observation)
            
        # Case C: The engine returned an unparseable or invalid state
        ELSE:
            CorrectionNudge = Environment.FormatInvalidStateFeedback()
            AgentState.Record(CorrectionNudge)

    # If the loop exhausts the budget without reaching a terminal state
    RETURN RaiseTimeoutFailure()