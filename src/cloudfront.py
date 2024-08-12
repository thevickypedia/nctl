import itertools
import json
import logging
import time

import boto3
import yaml
from botocore.exceptions import ClientError

from .settings import env

LOGGER = logging.getLogger(__name__)


class CloudFront:
    """Initiates CloudFront object to get and update a cloudfront distribution.

    >>> CloudFront

    """

    def __init__(self):
        """Initiates the boto3 client."""
        self.client = boto3.client('cloudfront')

    def get_distribution(self) -> dict:
        """Get cloudfront distribution.

        Returns:
            dict:
            Distribution information.
        """
        return self.client.get_distribution(
            Id=env.distribution_id
        )

    def create_distribution(self, filename: str) -> None:
        """Creates a cloudfront distribution from a JSON or YAML file as config.

        Args:
            filename: Configuration filename.
        """
        flower = filename.lower()
        assert flower.endswith(".yaml") or flower.endswith(".yml") or flower.endswith(".json"), \
            "Config file can only be JSON or YAML"
        if flower.endswith(".yaml") or flower.endswith(".yml"):
            with open(filename) as file:
                config = yaml.load(file, Loader=yaml.FullLoader)
        if flower.endswith(".json"):
            with open(filename) as file:
                config = json.load(file)
        create_response = self.client.create_distribution(DistributionConfig=config)
        if create_response.get('ResponseMetadata', {}).get('HTTPStatusCode', 500) == 200:
            LOGGER.info("CloudFront distribution has been created. "
                        f"Deployment status: {create_response['Distribution']['Status']}")
        else:
            raise ClientError(
                operation_name="CreateDistribution",
                error_response=create_response.get('ResponseMetadata')
            )

    def update_distribution(self, origin_name: str) -> None:
        """Updates a cloudfront distribution.

        Args:
            origin_name: Origin name that has to be replaced with.
        """
        get_response = self.get_distribution()
        etag = get_response['ETag']
        distribution_config = get_response.get('Distribution', {}).get('DistributionConfig', {})
        item1, item2 = False, False
        for index, item in enumerate(distribution_config.get('Origins').get('Items', [])):
            if domain_name := item.get('DomainName'):
                LOGGER.info(f"DomainName::{domain_name} -> {origin_name}")
                distribution_config['Origins']['Items'][index]['DomainName'] = origin_name
                item1 = True
            if item_id := item.get('Id'):
                LOGGER.info(f"Id::{item_id} -> {origin_name}")
                distribution_config['Origins']['Items'][index]['Id'] = origin_name
                item2 = True
        if not all((item1, item2)):
            LOGGER.error(distribution_config)
            raise ClientError(
                operation_name="UpdateDistribution",
                error_response="Missing key(s) `DomainName` or `Id`"
            )

        if origin_id := distribution_config.get('DefaultCacheBehavior', {}).get('TargetOriginId'):
            LOGGER.info(f"TargetOriginId::{origin_id} -> {origin_name}")
            distribution_config['DefaultCacheBehavior']['TargetOriginId'] = origin_name
        else:
            LOGGER.error(distribution_config)
            raise ClientError(
                operation_name="UpdateDistribution",
                error_response="Missing key `TargetOriginId` in DefaultCacheBehavior"
            )

        update_response = self.client.update_distribution(
            DistributionConfig=distribution_config,
            Id=env.distribution_id,
            IfMatch=etag
        )
        if update_response.get('ResponseMetadata', {}).get('HTTPStatusCode', 500) == 200:
            LOGGER.info("CloudFront distribution has been updated. "
                        f"Deployment status: {update_response['Distribution']['Status']}")
        else:
            raise ClientError(
                operation_name="UpdateDistribution",
                error_response=update_response.get('ResponseMetadata')
            )

        for i in itertools.count():
            if not i:
                time.sleep(300)
            else:
                time.sleep(10)
            response = self.get_distribution()
            with open(env.configfile, 'w') as file:
                yaml.dump(stream=file, data=response, Dumper=yaml.SafeDumper, sort_keys=False, default_flow_style=False)
            if response.get('Distribution', {}).get('Status', 'Not Deployed') == "Deployed":
                LOGGER.info("CloudFront distribution has been deployed")
                break
            if i > 5:
                LOGGER.warning("CloudFront distribution is taking longer than usual to propagate.")
                return
