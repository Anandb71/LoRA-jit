from backend.contracts.schemas import TelemetryEvent
from backend.routing.structural import StructuralRouter


def test_structural_router_prefers_scope_tokens() -> None:
    router = StructuralRouter()
    event = TelemetryEvent(
        session_id="s1",
        file_path="src/app/orders/checkout.py",
        language_id="python",
        cursor_line=10,
        cursor_column=2,
        symbols_in_scope=["Checkout", "Checkout", "PaymentGateway"],
    )

    decision = router.predict(event)
    assert decision.adapter_id == "checkout"
    assert decision.confidence > 0.5
