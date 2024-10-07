from enum import Enum
from typing import Optional


class JSONSchemaType(Enum):
    """
    Enumerations for the possible schema types to simplify JSON-Schema usage.
    """

    RECIPES = "schema-recipes.json"


class DDBPrefixes(Enum):
    """
    Enumerations for DynamoDB Partition Keys and Sort Keys for RECIPE items and related information to
    centralize and simplify the usage.
    """

    PK_USER = "USER#"
    SK_RECIPE_DATA = "RECIPE#"
