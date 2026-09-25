"""
Player-facing crafting commands - deliberately NOT the crafting
contrib's own `CmdCraft` (see CmdSimpleCraft's own docstring for why),
plus recipe discovery (`recipes`) and training (`learnrecipe`,
`CraftTrainer`). world/recipes.py holds the actual recipe classes;
this module is the interface a player actually types commands into.

Kept in its own file rather than world/recipes.py so nothing here is
ever at risk of the real, documented gotcha in that module (a plain
top-level function in a CRAFT_RECIPE_MODULES file crashes the
contrib's recipe auto-discovery) - these commands have no business
being scanned as recipes in the first place.
"""

from evennia import Command, DefaultCharacter

from world.recipes import ALL_RECIPES, _get_recipe_class, _recipe_learn_cost


def _matching_items(pool, tag, tag_category, exclude):
    """Every object in `pool` tagged `tag` under `tag_category`, not
    already claimed by an earlier ingredient slot (`exclude`)."""
    return [obj for obj in pool if obj not in exclude and obj.tags.get(tag, category=tag_category)]


class CmdSimpleCraft(Command):
    """
    Craft something from materials in your inventory.

    Usage:
      craft <recipe name>

    Finds and uses whatever you're carrying that matches the recipe
    automatically - no need to name your own ingredients one by one.
    See 'recipes' for what you can make, what each one needs, and
    whether you already know how.
    """

    key = "craft"
    help_category = "general"

    def func(self):
        caller = self.caller
        name = self.args.strip().lower()
        if not name:
            caller.msg("Usage: craft <recipe name>. See 'recipes' for what you can make.")
            return

        recipe_cls = _get_recipe_class(name)
        if not recipe_cls:
            caller.msg("No recipe called '%s'. See 'recipes' for what you can make." % name)
            return

        if not recipe_cls.KNOWN_BY_DEFAULT and recipe_cls.name not in (caller.db.craft_recipes_known or set()):
            caller.msg(
                "You haven't learned how to make %s yet - find a trainer "
                "('learnrecipe %s' once you have)." % (recipe_cls.name, recipe_cls.name)
            )
            return

        consumable_tag_category = getattr(recipe_cls, "consumable_tag_category", "crafting_material")
        tool_tag_category = getattr(recipe_cls, "tool_tag_category", "crafting_tool")
        consumable_names = recipe_cls.consumable_names or recipe_cls.consumable_tags or []
        tool_names = recipe_cls.tool_names or recipe_cls.tool_tags or []

        inputs = []
        missing = []

        for i, tag in enumerate(recipe_cls.consumable_tags or []):
            found = _matching_items(caller.contents, tag, consumable_tag_category, inputs)
            if found:
                inputs.append(found[0])
            else:
                missing.append(consumable_names[i] if i < len(consumable_names) else tag)

        tool_pool = list(caller.contents)
        if caller.location:
            tool_pool += caller.location.contents
        for i, tag in enumerate(recipe_cls.tool_tags or []):
            found = _matching_items(tool_pool, tag, tool_tag_category, inputs)
            if found:
                inputs.append(found[0])
            else:
                missing.append(tool_names[i] if i < len(tool_names) else tag)

        if missing:
            caller.msg(
                "You don't have what %s needs - still missing: %s."
                % (recipe_cls.name, ", ".join(missing))
            )
            return

        from evennia.contrib.game_systems.crafting import craft

        result = craft(caller, recipe_cls.name, *inputs)
        if result:
            # CmdCraft's own func() does exactly this move - the
            # contrib's craft() access function itself does NOT
            # deliver its result anywhere (a real, confirmed gap found
            # during this system's own live post-deploy verification).
            for obj in result:
                obj.location = caller


class CmdRecipeList(Command):
    """
    See every recipe that exists, and whether you already know it.

    Usage:
      recipes
    """

    key = "recipes"
    help_category = "general"

    def func(self):
        caller = self.caller
        if not ALL_RECIPES:
            caller.msg("No recipes exist yet.")
            return

        known = caller.db.craft_recipes_known or set()
        lines = ["|wKnown Recipes|n"]
        for cls in ALL_RECIPES:
            materials = ", ".join(cls.consumable_names or cls.consumable_tags or [])
            tools = ", ".join(cls.tool_names or cls.tool_tags or [])
            line = "  |Y%s|n - needs %s" % (cls.name, materials or "nothing")
            if tools:
                line += " (using %s)" % tools
            if cls.KNOWN_BY_DEFAULT:
                line += " |x[free]|n"
            elif cls.name in known:
                line += " |g[known]|n"
            else:
                line += " |x[needs training - %d gold]|n" % _recipe_learn_cost(cls.TIER_LEVEL)
            lines.append(line)
        caller.msg("\n".join(lines))


class CraftTrainer(DefaultCharacter):
    """
    An NPC that teaches recipes above tier 1 for gold. Set
    db.teaches_profession to a skill_key (e.g. "faber"). Plain
    DefaultCharacter, not CombatCharacter - a trainer has no reason to
    fight, matching NPCMerchant/SpellSkillTrainer's own precedent.
    """

    def at_object_creation(self):
        self.locks.add("puppet:false()")


def find_craft_trainer(location, profession):
    """The first CraftTrainer in location teaching `profession`, or None."""
    if not location:
        return None
    for obj in location.contents:
        if obj.is_typeclass(CraftTrainer, exact=False) and obj.db.teaches_profession == profession:
            return obj
    return None


class CmdLearnRecipe(Command):
    """
    Learn a recipe above tier 1 from a trainer standing here.

    Usage:
      learnrecipe <recipe name>

    Tier-1 recipes need no training at all - anyone can attempt one
    the moment they have the materials. Everything past that has to be
    learned in person, for gold, the same way learnspell/learnskill
    already work. See 'recipes' for what a recipe costs before you
    commit to it.
    """

    key = "learnrecipe"
    help_category = "general"

    def func(self):
        caller = self.caller
        name = self.args.strip().lower()
        if not name:
            caller.msg("Usage: learnrecipe <recipe name>")
            return

        recipe_cls = _get_recipe_class(name)
        if not recipe_cls:
            caller.msg("No recipe called '%s'. See 'recipes' for what exists." % name)
            return

        if recipe_cls.KNOWN_BY_DEFAULT:
            caller.msg("%s needs no training - anyone can already make it." % recipe_cls.name)
            return

        known = caller.db.craft_recipes_known or set()
        if recipe_cls.name in known:
            caller.msg("You already know how to make %s." % recipe_cls.name)
            return

        trainer = find_craft_trainer(caller.location, recipe_cls.skill_key)
        if not trainer:
            caller.msg("There's no one here who can teach you that.")
            return

        cost = _recipe_learn_cost(recipe_cls.TIER_LEVEL)
        gold = caller.db.gold or 0
        if gold < cost:
            caller.msg(
                "%s wants %d gold to teach you %s - you have %d."
                % (trainer.key, cost, recipe_cls.name, gold)
            )
            return

        caller.db.gold = gold - cost
        known.add(recipe_cls.name)
        caller.db.craft_recipes_known = known
        caller.msg(
            "%s teaches you how to make %s, for %d gold."
            % (trainer.key, recipe_cls.name, cost)
        )
