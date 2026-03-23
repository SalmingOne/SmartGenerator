from textual.app import ComposeResult
from textual.containers import VerticalGroup
from textual.reactive import reactive
from textual.widgets import Input, Label, Static

from ..strategy_params import STRATEGY_PARAMS


class StrategyForm(VerticalGroup):
    """Dynamic form that rebuilds fields based on selected strategy type."""

    strategy_type: reactive[str] = reactive("degradation_search", init=False)

    def compose(self) -> ComposeResult:
        yield Static("Strategy Parameters", classes="section-title")
        fields = STRATEGY_PARAMS.get(self.strategy_type, [])
        for field_def in fields:
            default_str = str(field_def.default) if field_def.default is not None else ""
            suffix = " *" if field_def.required else ""
            yield Label(f"{field_def.label}{suffix}")
            yield Input(
                value=default_str,
                id=f"strategy_{field_def.name}",
                placeholder=field_def.field_type,
            )

    async def watch_strategy_type(self, new_type: str) -> None:
        await self.remove_children()
        await self.mount(Static("Strategy Parameters", classes="section-title"))
        fields = STRATEGY_PARAMS.get(new_type, [])
        for field_def in fields:
            default_str = str(field_def.default) if field_def.default is not None else ""
            suffix = " *" if field_def.required else ""
            await self.mount(Label(f"{field_def.label}{suffix}"))
            await self.mount(Input(
                value=default_str,
                id=f"strategy_{field_def.name}",
                placeholder=field_def.field_type,
            ))

    def get_values(self) -> dict:
        """Collect non-empty field values, cast to proper types."""
        fields = STRATEGY_PARAMS.get(self.strategy_type, [])
        result = {}
        for field_def in fields:
            try:
                widget = self.query_one(f"#strategy_{field_def.name}", Input)
            except Exception:
                continue
            val = widget.value.strip()
            if not val:
                continue
            if field_def.field_type == "int":
                result[field_def.name] = int(val)
            elif field_def.field_type == "float":
                result[field_def.name] = float(val)
            else:
                result[field_def.name] = val
        return result

    def set_values(self, params: dict) -> None:
        """Populate fields from a dict of strategy params."""
        for name, value in params.items():
            try:
                widget = self.query_one(f"#strategy_{name}", Input)
                widget.value = str(value)
            except Exception:
                pass