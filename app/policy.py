from app.schemas import ActionRequest, PolicyDecision, Risk


def evaluate_action(action: ActionRequest, autonomy_level: int, auto_purchase_limit_cad: float = 0) -> PolicyDecision:
    if action.risk == Risk.destructive:
        return PolicyDecision(allowed=False, requires_approval=True, reason="Destructive actions require explicit human approval.")
    if action.estimated_cost_cad > auto_purchase_limit_cad:
        return PolicyDecision(allowed=False, requires_approval=True, reason="Action exceeds customer automatic purchasing authority.")
    if autonomy_level <= 0:
        return PolicyDecision(allowed=False, requires_approval=True, reason="Tenant is configured for observation only.")
    if autonomy_level == 1:
        return PolicyDecision(allowed=False, requires_approval=True, reason="Tenant permits recommendations but not autonomous execution.")
    if action.risk == Risk.high and autonomy_level < 4:
        return PolicyDecision(allowed=False, requires_approval=True, reason="High-risk action exceeds configured autonomy level.")
    if action.risk == Risk.medium and autonomy_level < 3:
        return PolicyDecision(allowed=False, requires_approval=True, reason="Medium-risk action exceeds configured autonomy level.")
    return PolicyDecision(allowed=True, requires_approval=False, reason="Action is within tenant autonomy policy.")
