# Built-in imports
from typing import Optional, Self

# External imports
from pydantic import BaseModel, Field


class RecipeModel(BaseModel):
    """
    Class that represents a RECIPE item.
    """

    PK: str = Field(pattern=r"^USER#[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    SK: str = Field(pattern=r"^RECIPE#")
    recipe_title: str
    recipe_details: Optional[str] = Field(None)
    recipe_date: str
    created_at: str
    updated_at: str

    def to_dynamodb_dict(self) -> dict:
        dynamodb_dict = {
            "PK": {"S": self.PK},
            "SK": {"S": self.SK},
            "recipe_title": {"S": self.recipe_title},
            "recipe_details": {"S": self.recipe_details},
            "recipe_date": {"S": self.recipe_date},
            "created_at": {"S": self.created_at},
            "updated_at": {"S": self.updated_at},
        }

        # Remove None values from the dictionary
        dynamodb_dict = {
            key: value for key, value in dynamodb_dict.items() if value is not None
        }

        return dynamodb_dict

    @classmethod
    def from_dynamodb_item(cls, dynamodb_item: dict) -> "RecipeModel":
        return cls(
            PK=dynamodb_item["PK"]["S"],
            SK=dynamodb_item["SK"]["S"],
            recipe_title=dynamodb_item["recipe_title"]["S"],
            recipe_details=dynamodb_item.get("recipe_details", {}).get("S"),
            recipe_date=dynamodb_item["recipe_date"]["S"],
            created_at=dynamodb_item["created_at"]["S"],
            updated_at=dynamodb_item["updated_at"]["S"],
        )


# RECIPE: Instead of a duplicated model for "PATCH" requests, create an abstraction for both
class RecipeModelUpdates(BaseModel):
    """
    Class that represents a RECIPE item.
    """

    PK: str = Field(pattern=r"^USER#[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    SK: str = Field(pattern=r"^RECIPE#")
    recipe_title: Optional[str] = Field(None)
    recipe_details: Optional[str] = Field(None)
    recipe_date: Optional[str] = Field(None)
    created_at: Optional[str] = Field(None)
    updated_at: Optional[str] = Field(None)

    def to_dynamodb_dict(self) -> dict:
        dynamodb_dict = {
            "PK": {"S": self.PK},
            "SK": {"S": self.SK},
            "recipe_title": {"S": self.recipe_title},
            "recipe_details": {"S": self.recipe_details},
            "recipe_date": {"S": self.recipe_date},
            "created_at": {"S": self.created_at},
            "updated_at": {"S": self.updated_at},
        }

        # Remove None values from the dictionary
        dynamodb_dict = {
            key: value
            for key, value in dynamodb_dict.items()
            if value.get("S") is not None
        }

        return dynamodb_dict

    @classmethod
    def from_dynamodb_item(cls, dynamodb_item: dict) -> "RecipeModel":
        return cls(
            PK=dynamodb_item["PK"]["S"],
            SK=dynamodb_item["SK"]["S"],
            recipe_title=dynamodb_item.get("recipe_title", {}).get("S"),
            recipe_details=dynamodb_item.get("recipe_details", {}).get("S"),
            recipe_date=dynamodb_item.get("recipe_date", {}).get("S"),
            created_at=dynamodb_item.get("created_at", {}).get("S"),
            updated_at=dynamodb_item.get("updated_at", {}).get("S"),
        )


if __name__ == "__main__":
    # Example usage 1
    recipe_data = {
        "PK": "USER#rick@example.com",
        "SK": "RECIPE#ULID1234",
        "recipe_title": "Complete project",
        "recipe_details": "Finish the report",
        "recipe_date": "2024-02-29",
        "created_at": "2024-01-05T05:51:02.350Z",
        "updated_at": "2024-01-06T02:31:02.350Z",
    }

    recipe_instance = RecipeModel(**recipe_data)
    recipe_dict = recipe_instance.to_dynamodb_dict()
    print(recipe_dict)

    # Example usage 2
    dynamodb_item = {
        "PK": {"S": "USER#rick@example.com"},
        "SK": {"S": "RECIPE#ULID1234"},
        "recipe_title": {"S": "Complete project 123"},
        "recipe_details": {"S": "Finish the project 123 with notes and diagrams"},
        "recipe_date": {"S": "2024-08-14"},
        "created_at": {"S": "2024-01-05T05:51:02.350Z"},
        "updated_at": {"S": "2024-01-06T02:31:02.350Z"},
    }

    recipe_instance = RecipeModel.from_dynamodb_item(dynamodb_item)
    print(recipe_instance)

    # Example usage 3
    recipe_data = {
        "PK": "USER#rick@example.com",
        "SK": "RECIPE#ULID1234",
        "recipe_details": "Finish the report",
    }

    recipe_instance = RecipeModelUpdates(**recipe_data)
    recipe_dict = recipe_instance.to_dynamodb_dict()
    print(recipe_dict)
