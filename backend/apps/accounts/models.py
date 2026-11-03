from django.db import models


class RevokedRefreshToken(models.Model):
    """
    Stores identifiers of refresh tokens that can no longer be used.

    Only the token identifier (jti) is stored.
    The original JWT is never stored in the database.
    """

    jti = models.CharField(
        max_length=255,
        unique=True,
    )

    expires_at = models.DateTimeField(
        db_index=True,
    )

    revoked_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "revoked_refresh_tokens"
        ordering = ["-revoked_at"]

    def __str__(self):
        return f"Revoked refresh token: {self.jti}"