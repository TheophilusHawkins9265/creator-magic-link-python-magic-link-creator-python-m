import os

from magic_link_service import SubscriberSignIn, configured_client, send_sign_in_link


def main() -> None:
    request = SubscriberSignIn(
        email=os.environ["CREATOR_EMAIL"],
        subscriber_id=os.environ.get("SUBSCRIBER_ID", "subscriber-001"),
        return_to="/library",
    )
    result = send_sign_in_link(request, configured_client(), os.environ["MAGIC_LINK_SECRET"], "http://localhost:8000")
    print(f"sent message {result.message_id} for {result.subscriber_id}")


if __name__ == "__main__":
    main()
