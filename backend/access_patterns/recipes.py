# Built-in imports
import os
from datetime import datetime
from typing import Optional

# External imports
from fastapi import HTTPException
from ulid import ULID
from aws_lambda_powertools import Logger

# Own imports
from recipes_app.common.logger import custom_logger
from recipes_app.helpers.dynamodb_helper import DynamoDBHelper
from recipes_app.common.enums import DDBPrefixes
from recipes_app.models.recipes import RecipeModel, RecipeModelUpdates

# Initialize DynamoDB helper for item's abstraction
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE")
ENDPOINT_URL = os.environ.get("ENDPOINT_URL")
dynamodb_helper = DynamoDBHelper(DYNAMODB_TABLE, ENDPOINT_URL)


class Recipes:
    """Class to define RECIPE items in a simple fashion."""

    def __init__(self, user_email: str, logger: Optional[Logger] = None) -> None:
        """
        :param user_email (str): User email user to identify the RECIPE items.
        :param logger (Optional(Logger)): Logger object.
        """
        self.user_email = user_email
        self.partition_key = f"{DDBPrefixes.PK_USER.value}{self.user_email}"
        self.logger = logger or custom_logger()

    def get_all_recipes(self) -> list:
        """
        Method to get all RECIPE items for a given user.
        """
        self.logger.info(
            f"Retrieving all RECIPE items for user_email: {self.user_email}"
        )

        results = dynamodb_helper.query_by_pk_and_sk_begins_with(
            partition_key=self.partition_key,
            sort_key_portion="RECIPE#",
        )
        self.logger.debug(results)
        self.logger.info(f"Items from query: {len(results)}")
        return results

    def get_recipe_by_ulid(self, ulid: str) -> dict:
        """
        Method to get a RECIPE item by its ULID.
        :param ulid (str): ULID for a specific RECIPE item.
        """
        self.logger.info(
            f"Retrieving RECIPE item by ULID: {ulid} for user_email: {self.user_email}"
        )

        result = dynamodb_helper.get_item_by_pk_and_sk(
            partition_key=self.partition_key,
            sort_key=f"RECIPE#{ulid}",
        )

        formatted_recipe = RecipeModel.from_dynamodb_item(result) if result else {}
        self.logger.debug(formatted_recipe)
        return formatted_recipe

    def create_recipe(self, recipe_data: dict) -> Optional[RecipeModel]:
        """
        Method to create a new RECIPE item.
        :param recipe_data (dict): Data for the new RECIPE item.
        """
        recipe_data["PK"] = self.partition_key
        recipe_data["SK"] = f"RECIPE#{ULID()}"
        current_time = datetime.now().isoformat()
        recipe_data["created_at"] = current_time
        recipe_data["updated_at"] = current_time

        recipe = RecipeModel(**recipe_data)

        result = dynamodb_helper.put_item(recipe.to_dynamodb_dict())
        self.logger.debug(result)

        if result.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
            return recipe

        return {}

    def patch_recipe(self, ulid: str, recipe_data: dict) -> Optional[RecipeModel]:
        """
        Method to patch an existing RECIPE item.
        :param ulid (str): ULID for a specific RECIPE item.
        :param recipe_data (dict): Data for the new RECIPE item.
        """

        # Validate that RECIPE item exists
        existing_recipe_item = self.get_recipe_by_ulid(ulid)
        if not existing_recipe_item:
            self.logger.error(
                f"patch_recipe failed due to non-existing RECIPE item to update: {ulid}"
            )
            raise HTTPException(
                status_code=400,
                detail=f"RECIPE patch request for ULID {ulid} "
                "is not valid because item does not exist",
            )

        current_time = datetime.now().isoformat()
        recipe_data["updated_at"] = current_time

        result = dynamodb_helper.update_item(
            partition_key=self.partition_key,
            sort_key=f"RECIPE#{ulid}",
            data_attributes_only=recipe_data,
        )
        self.logger.debug(result)

        if result.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
            return self.get_recipe_by_ulid(ulid)

        return {}

    def delete_recipe(self, ulid: str) -> Optional[RecipeModel]:
        """
        Method to delete an existing RECIPE item.
        :param ulid (str): ULID for a specific RECIPE item.
        :param recipe_data (dict): Data for the new RECIPE item.
        """

        # Validate that RECIPE item exists
        existing_recipe_item = self.get_recipe_by_ulid(ulid)
        if not existing_recipe_item:
            self.logger.error(
                f"delete_recipe failed due to non-existing RECIPE item to delete: {ulid}"
            )
            raise HTTPException(
                status_code=400,
                detail=f"RECIPE delete request for ULID {ulid} "
                "is not valid because item does not exist",
            )

        result = dynamodb_helper.delete_item(
            partition_key=self.partition_key,
            sort_key=f"RECIPE#{ulid}",
        )
        self.logger.debug(result)

        return {}
