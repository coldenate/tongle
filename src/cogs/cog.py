"""CopyCat cog"""

import interactions
from isort import file
import requests


class PsuedoUser:
    """Class to store a PsuedoUser"""

    def __init__(self, name, user_id, channel_id) -> None:
        self.name = name
        self.user_id = user_id
        # modifiables
        self.avatar_url = ""
        self.channel_id = channel_id
        self.webhook_id: int = 0

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    async def register(self, client, ctx):
        """Register the PseudoUser by creating a webhook with interactions."""

        user = await interactions.Webhook.create(
            client=client._http,  # pylint: disable=protected-access
            channel_id=ctx.channel_id,
            name=self.name,
        )
        user.id = self.webhook_id  # type: ignore
        user.avatar = ctx.author.get_avatar_url()


class CopyCat(interactions.Extension):
    """CopyCat cog to copy people's accounts!!! So scary!!!"""

    def __init__(self, client):
        self.client: interactions.Client = client

    @interactions.extension_command()
    async def copycat(self, ctx):
        """CopyCat command to copy people's accounts!!! So scary!!!"""
        # first, initialize the pseudo user
        pseudo_user = PsuedoUser(
            name=ctx.author.name,
            user_id=ctx.author.id,
            channel_id=ctx.channel_id,
        )
        # register the pseudo user
        await pseudo_user.register(self.client, ctx)
        # send a message to the channel
        await ctx.send(
            content=f"Registered {pseudo_user.name} in {ctx.channel_id}",
            ephemeral=True,
        )


def setup(client):
    """Setup function for CopyCat cog"""
    CopyCat(client)
