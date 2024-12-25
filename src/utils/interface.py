import disnake
from ..db.models import Settings, Guild

CONTENT_TYPE_MAPPING = {
    1: 'Text Only',
    2: 'Files Only',
    3: 'Embeds Only',
    4: 'Text and Files',
    5: 'Text and Embeds',
    6: 'Files and Embeds',
    7: 'All Content'
}


class Interface(disnake.ui.View):
    message: disnake.Message

    def __init__(self, settings: Settings, guild: Guild):
        super().__init__(timeout=60)

        self.settings = settings
        self.guild = guild

    async def on_timeout(self) -> None:
        for button in self.children:
            button.disabled = True

        if self.message:
            await self.message.edit(view=self)

    @disnake.ui.button(
        label='Toggle Bots', style=disnake.ButtonStyle.blurple
    )
    async def toggle_bots(self,
        button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        self.settings.allowed_bots = not self.settings.allowed_bots
        await self.guild.save()

        for button in self.children:
            button.disabled = True

        if self.message:
            await self.message.edit(view=self)

        await inter.response.send_message(
            content=('✅ Allowed Bots set to '
                    f'{self.settings.allowed_bots}'),
            ephemeral=True)

    @disnake.ui.button(
        label='Update Extensions', style=disnake.ButtonStyle.green
    )
    async def update_extensions(self,
        button: disnake.ui.Button, inter: disnake.MessageInteraction
    ):
        modal = ExtensionModal(self.settings, self.guild)
        await inter.response.send_modal(modal)

        for button in self.children:
            button.disabled = True

        if self.message:
            await self.message.edit(view=self)

    @disnake.ui.select(
        placeholder='Select Content Type',
        options=[
            disnake.SelectOption(label='Text Only', value='1'),
            disnake.SelectOption(label='Files Only', value='2'),
            disnake.SelectOption(label='Embeds Only', value='3'),
            disnake.SelectOption(label='Text and Files', value='4'),
            disnake.SelectOption(label='Text and Embeds', value='5'),
            disnake.SelectOption(label='Files and Embeds', value='6'),
            disnake.SelectOption(label='All Content', value='7')
        ]
    )
    async def select_content_type(self,
        select: disnake.ui.Select, inter: disnake.MessageInteraction
    ):
        self.settings.content_type = int(select.values[0])
        await self.guild.save()

        for button in self.children:
            button.disabled = True

        if self.message:
            await self.message.edit(view=self)

        await inter.response.send_message(
            content=('✅ Content Type set to '
                     f'{CONTENT_TYPE_MAPPING[int(select.values[0])]}'),
            ephemeral=True)


class ExtensionModal(disnake.ui.Modal):
    def __init__(self, settings: Settings, guild: Guild):

        self.settings = settings
        self.guild = guild

        super().__init__(
            title='Update Extensions',
            components=[
                disnake.ui.TextInput(
                    label='Allowed Extensions',
                    custom_id='extensions',
                    placeholder='e.g., jpg, png, gif or all',
                    value=', '.join(settings.allowed_extensions)
                    if settings.allowed_extensions else '',

                    style=disnake.TextInputStyle.short,
                    max_length=100
                )
            ],
            timeout=60
        )

    async def callback(self, interaction: disnake.ModalInteraction):
        try:
            extensions_input = interaction.text_values['extensions'].strip()

            if extensions_input.lower() == 'all':
                self.settings.allowed_extensions = None
            else:
                extensions = extensions_input.split(',')
                self.settings.allowed_extensions = [
                    ext.strip() for ext in extensions if ext.strip()]

            await self.guild.save()

            if self.settings.allowed_extensions is None:
                allowed_extensions_display = 'All'
            else:
                allowed_extensions_display = ', '.join(
                    self.settings.allowed_extensions)

            await interaction.response.send_message(
                content=('✅ Extensions updated '
                         f'to {allowed_extensions_display}'), ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(
                content=f'⚠️ Error updating extensions: {e}', ephemeral=True)
