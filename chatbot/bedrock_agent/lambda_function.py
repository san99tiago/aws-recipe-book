# NOTE: This is a super-MVP code for testing. Still has a lot of gaps to solve/fix. Do not use in prod.

from bedrock_agent.fetch_recipes import get_all_recipes_for_user


def lambda_handler(event, context):
    action_group = event["actionGroup"]
    _function = event["function"]
    parameters = event.get("parameters", [])

    print("PARAMETERS ARE: ", parameters)

    # Extract email from parameters
    email = None
    recipe_name = None
    for param in parameters:
        if param["name"] == "email":
            email = param["value"]
        if param["name"] == "recipe_name":
            recipe_name = param["value"]

    all_recipes_for_user = get_all_recipes_for_user(
        partition_key=f"USER#{email}",
        sort_key_portion="RECIPE#",
    )
    print("DEBUG, ", all_recipes_for_user)

    # TODO: Add a more robust search engine/algorithm for matching recipes
    result_recipe = "NOT FOUND!"
    for recipe in all_recipes_for_user:
        if recipe.get("recipe_details").startswith(recipe_name):
            result_recipe = recipe["recipe_details"]

    print(f"Recipe found: {result_recipe}")

    response_body = {"TEXT": {"body": result_recipe}}

    action_response = {
        "actionGroup": action_group,
        "function": _function,
        "functionResponse": {"responseBody": response_body},
    }

    dummy_function_response = {
        "response": action_response,
        "messageVersion": event["messageVersion"],
    }
    print("Response: {}".format(dummy_function_response))

    return dummy_function_response
