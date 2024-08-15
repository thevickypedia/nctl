import json
import logging
import os
from datetime import datetime

import boto3
import yaml
from botocore.exceptions import ClientError, WaiterError

from nctl import logger, models

LOGGER = logging.getLogger("nctl.cloudfront")


class CloudFront:
    """Initiates CloudFront object to get and update a cloudfront distribution.

    >>> CloudFront

    """

    def __init__(self, env_dump: dict, log_config: dict = None):
        """Initiates the boto3 client and re-configures the environment variables.

        Args:
            env_dump: JSON dump of environment variables' configuration.
        """
        self.env = models.EnvConfig(**env_dump)
        logger.configure_logging(
            debug=self.env.debug, log_config=log_config, process="cloudfront"
        )
        session = boto3.Session(
            aws_access_key_id=self.env.aws_access_key_id,
            aws_secret_access_key=self.env.aws_secret_access_key,
            region_name=self.env.aws_default_region,
            profile_name=self.env.aws_profile_name,
        )
        self.client = session.client("cloudfront")

    def run(self, public_url: str) -> None:
        """Updates the distribution if ID is available, otherwise creates a new distribution.

        Args:
            public_url: Public URL from ngrok, that has to be updated.
        """
        origin = public_url.lstrip("https://")
        if self.env.distribution_id:
            LOGGER.info("Updating existing distribution: %s", self.env.distribution_id)
        else:
            # fixme: Untested code
            # todo: Need to nest into the config file to update the public_url
            LOGGER.info(
                "Creating new distribution with config: %s",
                self.env.distribution_config,
            )
            self.create_distribution()
        self.update_distribution(
            current_config=self.get_distribution(), origin_name=origin
        )

    def get_distribution(self) -> dict:
        """Get cloudfront distribution.

        Returns:
            dict:
            Distribution information.
        """
        return self.client.get_distribution(Id=self.env.distribution_id)

    def create_distribution(self) -> None:
        """Creates a cloudfront distribution from a JSON or YAML file as config."""
        sfx = self.env.distribution_config.suffix.lower()
        if sfx in (".yml", ".yaml"):
            with open(self.env.distribution_config) as file:
                config = yaml.load(file, Loader=yaml.FullLoader)
        if sfx == ".json":
            with open(self.env.distribution_config) as file:
                config = json.load(file)
        create_response = self.client.create_distribution(DistributionConfig=config)
        if create_response.get("ResponseMetadata", {}).get("HTTPStatusCode", 0) == 200:
            LOGGER.info(
                "CloudFront distribution has been created. Deployment status: %s",
                create_response["Distribution"]["Status"],
            )
        else:
            raise ClientError(
                operation_name="CreateDistribution",
                error_response=create_response.get("ResponseMetadata"),
            )

    def update_distribution(self, current_config: dict, origin_name: str) -> None:
        """Updates a cloudfront distribution.

        Args:
            origin_name: Origin name that has to be replaced with.
        """
        self.store_config(current_config)  # todo: remove this after testing
        etag = current_config["ETag"]
        distribution_config = current_config.get("Distribution", {}).get(
            "DistributionConfig", {}
        )
        item1, item2 = False, False
        for index, item in enumerate(
            distribution_config.get("Origins").get("Items", [])
        ):
            if domain_name := item.get("DomainName"):
                LOGGER.info("DomainName::%s -> %s", domain_name, origin_name)
                distribution_config["Origins"]["Items"][index][
                    "DomainName"
                ] = origin_name
                item1 = True
            if item_id := item.get("Id"):
                LOGGER.info(f"Id::{item_id} -> {origin_name}")
                distribution_config["Origins"]["Items"][index]["Id"] = origin_name
                item2 = True
        if not all((item1, item2)):
            LOGGER.error(distribution_config)
            raise ClientError(
                operation_name="UpdateDistribution",
                error_response="Missing key(s) `DomainName` or `Id`",
            )

        if origin_id := distribution_config.get("DefaultCacheBehavior", {}).get(
            "TargetOriginId"
        ):
            LOGGER.info(f"TargetOriginId::{origin_id} -> {origin_name}")
            distribution_config["DefaultCacheBehavior"]["TargetOriginId"] = origin_name
        else:
            LOGGER.error(distribution_config)
            raise ClientError(
                operation_name="UpdateDistribution",
                error_response="Missing key `TargetOriginId` in DefaultCacheBehavior",
            )

        update_response = self.client.update_distribution(
            DistributionConfig=distribution_config,
            Id=self.env.distribution_id,
            IfMatch=etag,
        )
        if update_response.get("ResponseMetadata", {}).get("HTTPStatusCode", 0) == 200:
            LOGGER.info(
                "CloudFront distribution has been updated. "
                f"Deployment status: {update_response['Distribution']['Status']}"
            )
        else:
            raise ClientError(
                operation_name="UpdateDistribution",
                error_response=update_response.get("ResponseMetadata"),
            )

    def store_config(self, configuration: dict = None) -> None:
        """Stores the cloudfront distribution config in a YAML file locally."""
        configdir = "cloudfront_config"
        os.makedirs(configdir, exist_ok=True)
        configfile = os.path.join(
            configdir, datetime.now().strftime("config_%m%d%y.yaml")
        )
        with open(configfile, "w") as file:
            yaml.dump(
                stream=file,
                data=configuration or self.get_distribution(),
                Dumper=yaml.SafeDumper,
                sort_keys=False,
                default_flow_style=False,
            )
            file.flush()

    def await_update(self, distribution_id: str) -> None:
        """Awaits the distribution update."""
        try:
            LOGGER.info("Waiting for CloudFront distribution to enter 'Deployed' state")
            waiter = self.cloudfront_client.get_waiter("distribution_deployed")
            waiter.wait(
                Id=distribution_id, WaiterConfig={"Delay": 120, "MaxAttempts": 5}
            )
            LOGGER.info("CloudFront distribution has been deployed")
        except WaiterError as error:
            LOGGER.error(f"Error while waiting for distribution to deploy: {error}")
        except KeyboardInterrupt:
            LOGGER.warning("Cloudfront status check suspended")
        finally:
            self.store_config()
