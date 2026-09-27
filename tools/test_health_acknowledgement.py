#!/usr/bin/env python3
"""Port over `tools/check_health_status.py`: hvilke health-svar er røde.

Baggrund: `bugbottle.dev` ligger på en server vi ikke deployer, så
`/api/health` svarede `traffic_status: "partial"` hver time i måneder, og
`daily-health-check.sh` dømmer `status == "healthy"`. Cron har aldrig været rød,
fordi de to fejlformer har hver sin årsag og var kodet som én.

Porten dømmer tre ting ad gangen, fordi det er dem der er nemme at glemme:

1. **Uden kvittering er `partial` rød** — ellers er hele formålet væk.
2. **Kvitteringen matcher eksakt** — et nyt tavst domæne, en kvittering uden
   begrundelse eller en der dækker for meget må ikke give grøn.
3. **`unknown` er ikke rød** — en ny installation eller to stille dage må ikke
   gøre cron rød, ellers bliver den rød permanent og holdes op at se.

Den fjerde arm læser den *rigtige* `tools/health_acknowledged.json` og kræver, at
den matcher det `bugbottle.dev` faktisk er målt til. Uden den arm kunne filen
ommekring det værste tidspunkt og porten stadig være grøn.
"""
import json
import unittest
from pathlib import Path

import check_health_status
from check_health_status import decide, load_acknowledgements, traffic_signature

ACK = Path(__file__).resolve().parent / "health_acknowledged.json"


def payload(**overrides):
    base = {
        "ok": True,
        "status": "healthy",
        "kv": True,
        "traffic_status": "unknown",
        "traffic_domains": {
            "bugbottle.dev": "unknown",
            "cleancopy.tools": "unknown",
            "deskuptime.com": "unknown",
            "mahope.tools": "unknown",
        },
    }
    base.update(overrides)
    return base


def acknowledgement(silent, reason="fordi serveren ikke deployer den", traffic_status="partial"):
    return {
        "signature": {"traffic_status": traffic_status, "silent_domains": silent},
        "reason": reason,
        "since": "2026-09-27",
    }


# Det målte billede fra 27/9: de tre domæner vi deployer svarer, bugbottle.dev
# gør ikke. Det er den eneste undtagelse, og den skal passe præcis på den.
MEASURED_PARTIAL = payload(traffic_status="partial", traffic_domains={
    "bugbottle.dev": "unknown", "cleancopy.tools": "ok",
    "deskuptime.com": "ok", "mahope.tools": "ok",
})


class DecideTests(unittest.TestCase):
    def test_complete_traffic_is_green(self) -> None:
        healthy, _ = decide(payload(traffic_status="ok",
                                    traffic_domains={"mahope.tools": "ok", "bugbottle.dev": "ok"}))
        self.assertTrue(healthy)

    def test_unknown_traffic_is_not_a_failure(self) -> None:
        healthy, reason = decide(payload(traffic_domains={}))
        self.assertTrue(healthy)
        self.assertIn("ikke en fejl", reason)

    def test_unknown_traffic_names_the_silent_domains(self) -> None:
        # Uden den note er `unknown` det samme som `partial` i praksis: begge
        # skjuler at et domæne aldrig har skrevet.
        _, reason = decide(payload(traffic_domains={"bugbottle.dev": "unknown"}))
        self.assertIn("bugbottle.dev", reason)
        self.assertIn("verificér", reason)

    def test_partial_without_acknowledgement_is_red(self) -> None:
        healthy, reason = decide(MEASURED_PARTIAL, [])
        self.assertFalse(healthy)
        self.assertIn("bugbottle.dev", reason)

    def test_matching_acknowledgement_is_green(self) -> None:
        entries = [acknowledgement({"bugbottle.dev": "unknown"})]
        healthy, reason = decide(MEASURED_PARTIAL, entries)
        self.assertTrue(healthy, reason)
        self.assertIn("2026-09-27", reason)

    def test_a_second_silent_domain_is_not_covered(self) -> None:
        # Nyt domæne falder ned i den gamle undtagelse, hvis kvitteringen kun
        # husker *et* domæne. Derfor skal signaturen være hele det tavse kort.
        entries = [acknowledgement({"bugbottle.dev": "unknown"})]
        data = payload(traffic_status="partial", traffic_domains={
            "bugbottle.dev": "unknown", "cleancopy.tools": "ok",
            "deskuptime.com": "ok", "mahope.tools": "unknown",
        })
        healthy, reason = decide(data, entries)
        self.assertFalse(healthy, reason)
        self.assertIn("mahope.tools", reason)

    def test_a_stale_acknowledgement_cannot_turn_a_healthy_system_red(self) -> None:
        # Undtagelsen skal gælde den måling den er skrevet til. En gammel
        # kvittering der bliver liggende, når bugbottle.dev flytter på Pages,
        # må ikke gøre en grøn site rød — den skal bare holdes at slette ved
        # hjælp af `removes_when`.
        entries = [acknowledgement({"bugbottle.dev": "unknown"}, traffic_status="partial")]
        self.assertTrue(decide(payload(traffic_status="ok", traffic_domains={
            "bugbottle.dev": "ok", "cleancopy.tools": "ok",
            "deskuptime.com": "ok", "mahope.tools": "ok",
        }), entries)[0])

    def test_acknowledgement_without_reason_is_not_acknowledgement(self) -> None:
        for reason in ("", "   "):
            entries = [acknowledgement({"bugbottle.dev": "unknown"}, reason=reason)]
            self.assertFalse(decide(MEASURED_PARTIAL, entries)[0], reason)

    def test_acknowledgement_with_broken_signature_is_ignored(self) -> None:
        entries = [{"reason": "x"}, {"signature": "bugbottle.dev", "reason": "x"}]
        self.assertFalse(decide(MEASURED_PARTIAL, entries)[0])

    def test_kv_down_is_red_whatever_the_traffic_says(self) -> None:
        self.assertFalse(decide(payload(kv=False, traffic_status="ok"), [])[0])
        self.assertFalse(decide(dict(MEASURED_PARTIAL, kv=False),
                                [acknowledgement({"bugbottle.dev": "unknown"})])[0])

    def test_unexpected_traffic_status_is_red(self) -> None:
        self.assertFalse(decide(payload(traffic_status="mostly-fine"), [])[0])

    def test_non_object_payload_is_red(self) -> None:
        self.assertFalse(decide(["healthy"], [])[0])

    def test_signature_ignores_domains_that_are_talking(self) -> None:
        # En travl tirsdag må ikke kræve en ny kvittering, fordi mahope.tools
        # gik fra 'unknown' til 'ok'.
        before = {"bugbottle.dev": "unknown"}
        after = {"bugbottle.dev": "unknown", "mahope.tools": "ok", "deskuptime.com": "ok"}
        self.assertEqual(traffic_signature({"traffic_domains": before}),
                         traffic_signature({"traffic_domains": after}))

    def test_signature_of_a_domainless_response_is_empty(self) -> None:
        self.assertEqual(traffic_signature({}), {})
        self.assertEqual(traffic_signature({"traffic_domains": "nope"}), {})


class ShippedAcknowledgementTests(unittest.TestCase):
    """Den fil, der faktisk ligger i repoet, skal være gyldig — ikke bare syntaktisk."""

    def setUp(self) -> None:
        self.entries = load_acknowledgements(ACK)
        self.assertTrue(self.entries, "tools/health_acknowledged.json har ingen indgang")

    def test_every_entry_has_reason_question_and_removes_when(self) -> None:
        for entry in self.entries:
            for field in ("reason", "question", "removes_when"):
                self.assertTrue(str(entry.get(field, "")).strip(),
                                f"indgang uden {field}: {json.dumps(entry, ensure_ascii=False)}")

    def test_undocumented_acknowledgements_do_not_exist(self) -> None:
        # Hver indgang skal pege på planens ❓, ellers er den en løgneste med
        # filnavn. Kun `bugbottle.dev` er etableret undtagelse pr. 27/9.
        for entry in self.entries:
            self.assertIn("bugbottle.dev", str(entry.get("signature", {}).get("silent_domains", {})),
                          "kun bugbottle.dev har en dokumenteret ❓")

    def test_the_shipped_entry_matches_the_measured_bugbottle_state(self) -> None:
        # Målt 27/9: de tre deployede domæner svarer, bugbottle.dev gør ikke.
        measured = payload(traffic_status="partial", traffic_domains={
            "bugbottle.dev": "unknown", "cleancopy.tools": "ok",
            "deskuptime.com": "ok", "mahope.tools": "ok",
        })
        healthy, reason = decide(measured, self.entries)
        self.assertTrue(healthy, reason)

    def test_the_shipped_entry_does_not_cover_a_healthy_installation(self) -> None:
        # Skulle porten nogensinde blive rød af en kvittering, der dækker for
        # meget, så er det her den ser det: et komplet domænekort er grønt uden
        # nogen undtagelse, og filen må ikke kunne gøre det rødt.
        healthy, _ = decide(payload(traffic_status="ok", traffic_domains={
            "bugbottle.dev": "ok", "cleancopy.tools": "ok",
            "deskuptime.com": "ok", "mahope.tools": "ok",
        }), self.entries)
        self.assertTrue(healthy)

    def test_acknowledgement_file_is_json_with_a_readme(self) -> None:
        data = json.loads(ACK.read_text(encoding="utf-8"))
        self.assertIn("_readme", data)
        self.assertEqual(check_health_status.ACK_FILE, ACK)


if __name__ == "__main__":
    unittest.main()
