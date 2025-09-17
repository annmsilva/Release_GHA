import argparse
import json
from typing import Literal

import requests


def get_status_style(status: Literal["SUCCESS", "FAILED", "CANCELLED"]):
    if status == "SUCCESS":
        return "good", "Good"
    elif status == "CANCELLED":
        return "warning", "Warning"
    return "attention", "Attention"


def post_to_teams(webhook_url: str, card_content: dict):
    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": card_content,
            }
        ],
    }

    print("Sending payload to Teams:")
    print(json.dumps(payload, indent=2))

    response = requests.post(
        webhook_url,
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=10,
    )
    response.raise_for_status()
    print("✅ Teams notification sent.")


def send_run_notification(
    webhook_url: str,
    status: Literal["SUCCESS", "FAILED", "CANCELLED"],
    ref: str,
    run_url: str,
    environment: str,
    skus: str,
):
    color, style = get_status_style(status)
    skus_list = [s.strip() for s in skus.split(",") if s.strip()]
    env_display = environment.upper()

    body_blocks = [
        {
            "type": "Container",
            "style": style,
            "bleed": True,
            "items": [
                {
                    "type": "TextBlock",
                    "text": f"Run for SKUs: {', '.join(skus_list)}",
                    "weight": "Bolder",
                    "size": "Large",
                    "color": color,
                    "wrap": True,
                    "spacing": "Small",
                },
            ],
        },
        {
            "type": "Badge",
            "text": status,
            "size": "Large",
            "style": style,
        },
        {
            "type": "TextBlock",
            "text": f"🔖 Version: {ref}",
            "wrap": True,
        },
        {
            "type": "TextBlock",
            "text": f"🛠️ Environment: {env_display}",
            "wrap": True,
        },
    ]

    card_content = {
        "$schema": "https://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": body_blocks,
        "actions": [
            {
                "type": "Action.OpenUrl",
                "title": "🔍 View Workflow Run",
                "url": run_url,
            }
        ]
        if run_url
        else [],
    }

    post_to_teams(webhook_url, card_content)


def send_release_notification(
    webhook_url: str,
    environment: str,
    skus: str,
    release_number: str,
    release_url: str,
):
    card_content = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "size": "Large",
                "weight": "Bolder",
                "text": "✅ Release Notification",
            },
            {
                "type": "FactSet",
                "facts": [
                    {
                        "title": "📦 Release Version:",
                        "value": release_number,
                    },
                    {
                        "title": "🛍️ SKU(s):",
                        "value": skus,
                    },
                    {
                        "title": "🚀 Environment:",
                        "value": environment,
                    },
                ],
            },
        ],
        "actions": [
            {
                "type": "Action.OpenUrl",
                "title": "📄 View Release",
                "url": release_url,
            }
        ],
    }

    post_to_teams(webhook_url, card_content)


def main():
    parser = argparse.ArgumentParser(description="Send Teams Notification")
    parser.add_argument(
        "--webhook-url",
        required=True,
    )
    parser.add_argument(
        "--status", choices=["SUCCESS", "FAILED", "CANCELLED"], default="SUCCESS"
    )
    parser.add_argument("--ref", default="main")
    parser.add_argument("--run-url", default="")
    parser.add_argument("--environment", default="KXSD10_PYEA_CICD01")
    parser.add_argument("--skus", default="demandai-pro")
    parser.add_argument("--release-version", help="e.g., 2510.1", default="2510.1")
    parser.add_argument("--release_url", help="Link to release notes")

    args = parser.parse_args()

    if args.release_version:
        send_release_notification(
            webhook_url=args.webhook_url,
            environment=args.environment,
            skus=args.skus,
            release_number=args.release_version,
            release_url=args.release_url,
        )
    else:
        send_run_notification(
            webhook_url=args.webhook_url,
            status=args.status,
            ref=args.ref,
            run_url=args.run_url,
            environment=args.environment,
            skus=args.skus,
        )


if __name__ == "__main__":
    main()
