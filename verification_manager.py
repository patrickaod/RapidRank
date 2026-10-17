import secrets
import time

class VerificationManager:
    def __init__(self):
        self.pending_verifications = {}

    def start_verification(self, discord_id, username):

        self.expire_verification(discord_id)

        # Prevent duplicate active verifications.
        if discord_id in self.pending_verifications:
            return None

        now = time.time()

        code = f"RR-{secrets.token_hex(3).upper()}"

        verification = {
            "username": username,
            "code": code,
            "expires_at": now + 240,
            "next_check_at": now + 10,
        }

        self.pending_verifications[discord_id] = verification

        return verification

    def expire_verification(self, discord_id):
        verification = self.pending_verifications.get(discord_id)

        if verification is None:
            return False

        if time.time() >= verification["expires_at"]:
            del self.pending_verifications[discord_id]
            return True

        return False


