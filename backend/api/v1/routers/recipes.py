# Built-in imports
from typing import Annotated
from uuid import uuid4

# External imports
from fastapi import APIRouter, Header
from aws_lambda_powertools import Logger

# Own imports
from access_patterns.recipes import Recipes
from api.v1.schemas.schema import Schema
from api.v1.services.exceptions import SchemaValidationException
from api.v1.services.validator import validate_json
from common.enums import JSONSchemaType


logger = Logger(
    service="recipe-app",
    log_uncaught_exceptions=True,
    owner="Santiago Garcia Arango",
)

router = APIRouter()


@router.get("/recipes", tags=["recipes"])
async def read_all_recipes(
    user_email: str,
    correlation_id: Annotated[str | None, Header()] = uuid4(),
):
    try:
        user_email = user_email.replace(" ", "+")
        logger.append_keys(correlation_id=correlation_id, user_email=user_email)
        logger.info("Starting recipes handler for read_all_recipes()")

        recipe = Recipes(user_email=user_email, logger=logger)
        result = recipe.get_all_recipes()
        logger.info("Finished read_recipe_item() successfully")
        return result

    except Exception as e:
        logger.error(f"Error in read_all_recipes(): {e}")
        raise e


@router.get("/recipes/{recipe_id}", tags=["recipes"])
async def read_recipe_item(
    user_email: str,
    recipe_id: str,
    correlation_id: Annotated[str | None, Header()] = uuid4(),
):
    try:
        user_email = user_email.replace(" ", "+")
        logger.append_keys(correlation_id=correlation_id, user_email=user_email)
        logger.info("Starting recipes handler for read_recipe_item()")

        recipe = Recipes(user_email=user_email, logger=logger)
        result = recipe.get_recipe_by_ulid(ulid=recipe_id)
        logger.info("Finished read_recipe_item() successfully")
        return result

    except Exception as e:
        logger.error(f"Error in read_recipe_item(): {e}")
        raise e


@router.post("/recipes", tags=["recipes"])
async def create_recipe_item(
    recipe_details: dict,
    correlation_id: Annotated[str | None, Header()] = uuid4(),
):
    try:
        # Inject additional keys to the logger for cross-referencing logs
        user_email = recipe_details.get("user_email").replace(" ", "+")
        logger.append_keys(correlation_id=correlation_id, user_email=user_email)

        # Validate payload with JSON-Schema
        recipes_schema = Schema(JSONSchemaType.RECIPES, logger=logger).get_schema()
        validation_result = validate_json(
            data=recipe_details, json_schema=recipes_schema, logger=logger
        )
        if isinstance(validation_result, Exception):
            raise SchemaValidationException(recipe_details, validation_result)
        logger.info("Starting recipes handler for create_recipe_item()")

        # After schema validation, it's safe to load the RECIPE element
        recipes = Recipes(user_email=user_email, logger=logger)
        result = recipes.create_recipe(recipe_details)

        logger.info("Finished create_recipe_item() successfully")
        return result

    except Exception as e:
        logger.error(f"Error in create_recipe_item(): {e}")
        raise e


@router.patch("/recipes/{recipe_id}", tags=["recipes"])
async def patch_recipe_item(
    user_email: str,
    recipe_id: str,
    recipe_details: dict,
    correlation_id: Annotated[str | None, Header()] = uuid4(),
):
    try:
        user_email = user_email.replace(" ", "+")
        logger.append_keys(correlation_id=correlation_id, user_email=user_email)
        logger.info("Starting recipes handler for patch_recipe_item()")

        # Validate payload with JSON-Schema
        recipes_schema = Schema(JSONSchemaType.RECIPES, logger=logger).get_schema()
        recipes_schema.pop(
            "required", None
        )  # For patch, do not enforce mandatory fields in schema
        validation_result = validate_json(
            data=recipe_details, json_schema=recipes_schema, logger=logger
        )
        if isinstance(validation_result, Exception):
            raise SchemaValidationException(recipe_details, validation_result)

        recipe = Recipes(user_email=user_email, logger=logger)
        result = recipe.patch_recipe(ulid=recipe_id, recipe_data=recipe_details)

        logger.info("Finished patch_recipe_item() successfully")
        return result

    except Exception as e:
        logger.error(f"Error in patch_recipe_item(): {e}")
        raise e


@router.delete("/recipes/{recipe_id}", tags=["recipes"])
async def delete_recipe_item(
    user_email: str,
    recipe_id: str,
    correlation_id: Annotated[str | None, Header()] = uuid4(),
):
    try:
        user_email = user_email.replace(" ", "+")
        logger.append_keys(correlation_id=correlation_id, user_email=user_email)
        logger.info("Starting recipes handler for delete_recipe_item()")

        recipe = Recipes(user_email=user_email, logger=logger)
        result = recipe.delete_recipe(ulid=recipe_id)

        logger.info("Finished delete_recipe_item() successfully")
        return result

    except Exception as e:
        logger.error(f"Error in delete_recipe_item(): {e}")
        raise e
