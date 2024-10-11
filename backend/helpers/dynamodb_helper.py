# Built-in imports
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

# Own imports
from common.logger import custom_logger

logger = custom_logger()


class DynamoDBHelper:
    """Custom DynamoDB Helper for simplifying CRUD operations."""

    def __init__(self, table_name: str, endpoint_url: str = None) -> None:
        """
        :param table_name (str): Name of the DynamoDB table to connect with.
        :param endpoint_url (Optional(str)): Endpoint for DynamoDB (only for local tests).
        """
        self.table_name = table_name
        self.dynamodb_client = boto3.client("dynamodb", endpoint_url=endpoint_url)
        self.dynamodb_resource = boto3.resource("dynamodb", endpoint_url=endpoint_url)
        self.table = self.dynamodb_resource.Table(self.table_name)

    def get_item_by_pk_and_sk(self, partition_key: str, sort_key: str) -> dict:
        """
        Method to get a single DynamoDB item from the primary key (pk+sk).
        :param partition_key (str): partition key value.
        :param sort_key (str): sort key value.
        """
        logger.info(
            f"Starting get_item_by_pk_and_sk with "
            f"pk: ({partition_key}) and sk: ({sort_key})"
        )

        # The structure key for a single-table-design "PK" and "SK" naming
        primary_key_dict = {
            "PK": {
                "S": partition_key,
            },
            "SK": {
                "S": sort_key,
            },
        }
        try:
            response = self.dynamodb_client.get_item(
                TableName=self.table_name,
                Key=primary_key_dict,
            )
            return response["Item"] if "Item" in response else {}

        except ClientError as error:
            logger.error(
                f"get_item operation failed for: "
                f"table_name: {self.table_name}."
                f"pk: {partition_key}."
                f"sk: {sort_key}."
                f"error: {error}."
            )
            raise error

    def query_by_pk_and_sk_begins_with(
        self, partition_key: str, sort_key_portion: str
    ) -> list[dict]:
        """
        Method to run a query against DynamoDB with partition key and the sort
        key with <begins-with> functionality on it.
        :param partition_key (str): partition key value.
        :param sort_key_portion (str): sort key portion to use in query.
        """
        logger.info(
            f"Starting query_by_pk_and_sk_begins_with with "
            f"pk: ({partition_key}) and sk: ({sort_key_portion})"
        )

        all_items = []
        try:
            # The structure key for a single-table-design "PK" and "SK" naming
            key_condition = Key("PK").eq(partition_key) & Key("SK").begins_with(
                sort_key_portion
            )
            limit = 50

            # Initial query before pagination
            response = self.table.query(
                KeyConditionExpression=key_condition,
                Limit=limit,
            )
            if "Items" in response:
                all_items.extend(response["Items"])

            # Pagination loop for possible following queries
            while "LastEvaluatedKey" in response:
                response = self.table.query(
                    KeyConditionExpression=key_condition,
                    Limit=limit,
                    ExclusiveStartKey=response["LastEvaluatedKey"],
                )
                if "Items" in response:
                    all_items.extend(response["Items"])

            return all_items
        except ClientError as error:
            logger.error(
                f"query operation failed for: "
                f"table_name: {self.table_name}."
                f"pk: {partition_key}."
                f"sort_key_portion: {sort_key_portion}."
                f"error: {error}."
            )
            raise error

    def put_item(self, data: dict) -> dict:
        """
        Method to add a single DynamoDB item.
        :param data (dict): Item to be added in the format of name/value pairs.
        """
        logger.info("Starting put_item operation.")
        logger.debug(f"data: {data}")

        try:
            response = self.dynamodb_client.put_item(
                TableName=self.table_name,
                Item=data,
            )
            logger.info(response)
            return response
        except ClientError as error:
            logger.error(
                f"put_item operation failed for: "
                f"table_name: {self.table_name}."
                f"data: {data}."
                f"error: {error}."
            )
            raise error

    def update_item(
        self, partition_key: str, sort_key: str, data_attributes_only: dict
    ) -> dict:
        """
        Method to update an existing item in a "patch" fashion (only deltas).
        :param partition_key (str): partition key value.
        :param sort_key (str): sort key value.
        :param data_attributes_only (dict): Item's data attributes to be updated in the format of name/value pairs.
        """

        logger.info("Starting update_item operation.")
        logger.debug(
            f"pk: {partition_key}, sk: {sort_key} data: {data_attributes_only}"
        )

        try:
            primary_key_dict = {
                "PK": partition_key,
                "SK": sort_key,
            }
            a, v = self._get_update_params(data_attributes_only)
            response = self.table.update_item(
                Key=primary_key_dict,
                UpdateExpression=a,
                ExpressionAttributeValues=dict(v),
            )
            logger.info(response)
            return response
        except ClientError as error:
            logger.error(
                f"put_item operation failed for: "
                f"table_name: {self.table_name}."
                f"pk: {partition_key}."
                f"sk: {sort_key}."
                f"data_attributes_only: {data_attributes_only}."
                f"error: {error}."
            )
            raise error

    def _get_update_params(self, payload: dict):
        """
        Given a dictionary we generate an update expression and a dict of values
        to update a dynamodb table.

        :payload (dict): Parameters to use for formatting.
        """
        update_expression = ["set "]
        update_values = dict()

        for key, val in payload.items():
            update_expression.append(f" {key} = :{key},")
            update_values[f":{key}"] = val

        return "".join(update_expression)[:-1], update_values

    def delete_item(self, partition_key: str, sort_key: str) -> dict:
        """
        Method to delete an existing item in DynamoDB
        :param partition_key (str): partition key value.
        :param sort_key (str): sort key value.
        """

        logger.info("Starting delete_item operation.")
        logger.debug(f"pk: {partition_key}, sk: {sort_key}")

        try:
            primary_key_dict = {
                "PK": partition_key,
                "SK": sort_key,
            }
            response = self.table.delete_item(Key=primary_key_dict)
            logger.info(response)
            return response
        except ClientError as error:
            logger.error(
                f"put_item operation failed for: "
                f"table_name: {self.table_name}."
                f"pk: {partition_key}."
                f"sk: {sort_key}."
                f"error: {error}."
            )
            raise error
