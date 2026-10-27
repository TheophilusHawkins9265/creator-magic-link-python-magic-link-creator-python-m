from src.magic_link_service import EmailSendRequest, SubscriberSignIn, send_sign_in_link


class RecordingMailer:
    def __init__(self) -> None:
        self.requests: list[EmailSendRequest] = []

    def send(self, request: EmailSendRequest) -> str:
        self.requests.append(request)
        return "message-123"


def test_subscriber_receives_a_link_with_a_stable_expiry_and_signature() -> None:
    mailer = RecordingMailer()
    result = send_sign_in_link(
        SubscriberSignIn("reader@example.com", "sub-7", "/library"),
        mailer,
        "test-secret",
        "http://localhost:8000",
        now=1_700_000_000,
    )

    assert result.message_id == "message-123"
    assert result.subscriber_id == "sub-7"
    assert "subscriber_id=sub-7" in result.link
    assert "1700000900." in result.link
    assert mailer.requests[0].to == "reader@example.com"
    assert result.link in mailer.requests[0].body
