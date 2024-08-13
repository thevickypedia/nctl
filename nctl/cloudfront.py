import itertools
import json
import logging
import os
import time
from datetime import datetime

import boto3
import yaml
from botocore.exceptions import ClientError

from nctl import models
from nctl.logger import LOGGER


class CloudFront:
    """Initiates CloudFront object to get and update a cloudfront distribution.

    >>> CloudFront

    """

    def __init__(self, env_dump: dict):
        """Initiates the boto3 client and re-configures the environment variables.

        Args:
            env_dump: JSON dump of environment variables' configuration.
        """
        self.env = models.EnvConfig(**env_dump)
        if self.env.debug:
            LOGGER.setLevel(logging.DEBUG)
        session = boto3.Session(
            aws_access_key_id=self.env.aws_access_key_id,
            aws_secret_access_key=self.env.aws_secret_access_key,
            region_name=self.env.aws_region_name,
            profile_name=self.env.aws_profile_name,
        )
        self.client = session.client("cloudfront")

    def run(self, public_url: str) -> None:
        """Updates the distribution if ID is available, otherwise creates a new distribution.

        Args:
            public_url: Public URL from ngrok, that has to be updated.
        """
        if self.env.distribution_id:
            LOGGER.info("Updating existing distribution: %s", self.env.distribution_id)
            self.update_distribution(origin_name=public_url.lstrip("https://"))
        else:
            # fixme: Untested code
            # todo: Need to nest into the config file to update the public_url
            LOGGER.info(
                "Creating new distribution with config: %s",
                self.env.distribution_config,
            )
            self.create_distribution()

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

    def update_distribution(self, origin_name: str) -> None:
        """Updates a cloudfront distribution.

        Args:
            origin_name: Origin name that has to be replaced with.
        """
        get_response = self.get_distribution()
        etag = get_response["ETag"]
        distribution_config = get_response.get("Distribution", {}).get(
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

        try:
            configdir = "cloudfront_config"
            os.makedirs(configdir, exist_ok=True)
            configfile = os.path.join(
                configdir, datetime.now().strftime("config_%m%d%y.yaml")
            )
            for i in itertools.count():
                if not i:
                    time.sleep(300)
                else:
                    time.sleep(10)
                response = self.get_distribution()
                with open(configfile, "w") as file:
                    yaml.dump(
                        stream=file,
                        data=response,
                        Dumper=yaml.SafeDumper,
                        sort_keys=False,
                        default_flow_style=False,
                    )
                if response.get("Distribution", {}).get("Status", "NA") == "Deployed":
                    LOGGER.info("CloudFront distribution has been deployed")
                    break
                if i > 5:
                    LOGGER.warning(
                        "CloudFront distribution is taking longer than usual to propagate."
                    )
                    return
        except KeyboardInterrupt:
            LOGGER.warning("Cloudfront status check suspended")
