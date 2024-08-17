import json
import logging
import os
from datetime import datetime
from typing import Any, Dict

import boto3
import yaml
from botocore.exceptions import ClientError, WaiterError
from pydantic import ValidationError
from pydantic_core import InitErrorDetails

from nctl import logger, models

LOGGER = logging.getLogger("nctl.cloudfront")


class CloudFront:
    """Initiates CloudFront object to get and update a cloudfront distribution.

    >>> CloudFront

    """

    def __init__(self, env_dump: dict):
        """Initiates the boto3 client and re-configures the environment variables.

        Args:
            env_dump: JSON dump of environment variables' configuration.
        """
        models.env = models.EnvConfig(**env_dump)
        logger.configure_logging(
            debug=models.env.debug,
            process="cloudfront",
            log_config=models.env.log_config,
            log=models.env.log,
        )
        session = boto3.Session(
            aws_access_key_id=models.env.aws_access_key_id,
            aws_secret_access_key=models.env.aws_secret_access_key,
            region_name=models.env.aws_default_region,
            profile_name=models.env.aws_profile_name,
        )
        self.client = session.client("cloudfront")

    def run(self, public_url: str) -> None:
        """Updates the distribution if ID is available, otherwise creates a new distribution.

        Args:
            public_url: Public URL from ngrok, that has to be updated.
        """
        origin = public_url.lstrip("https://")
        if models.env.distribution_id:
            LOGGER.info(
                "Updating existing distribution: %s", models.env.distribution_id
            )
        else:
            # First create a skeleton distribution using the provided config file
            # Then pull what's on AWS CloudFront to update distribution to retain consistency
            LOGGER.info(
                "Creating new distribution with config file: %s",
                models.env.distribution_config,
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
        LOGGER.info("Getting distribution info for: %s", models.env.distribution_id)
        return self.client.get_distribution(Id=models.env.distribution_id)

    def create_distribution(self) -> None:
        """Creates a cloudfront distribution from a JSON or YAML file as config."""
        sfx = models.env.distribution_config.suffix.lower()
        if sfx in (".yml", ".yaml"):
            with open(models.env.distribution_config) as file:
                config = yaml.load(file, Loader=yaml.FullLoader)
        elif sfx == ".json":
            with open(models.env.distribution_config) as file:
                config = json.load(file)
        else:
            # This shouldn't happen programatically, but just in case
            # https://docs.pydantic.dev/latest/errors/validation_errors/#string_pattern_mismatch
            raise ValidationError.from_exception_data(
                title="NCTL",
                line_errors=[
                    InitErrorDetails(
                        type="string_pattern_mismatch",
                        loc=("distribution_config",),
                        input="invalid",
                    )
                ],
            )

        create_response = self.client.create_distribution(DistributionConfig=config)
        if create_response.get("ResponseMetadata", {}).get("HTTPStatusCode", 0) == 200:
            LOGGER.info(
                "CloudFront distribution has been created. Deployment status: %s",
                create_response["Distribution"]["Status"],
            )
            models.env.distribution_id = create_response["Distribution"]["Id"]
            LOGGER.info("Distribution Id: %s", models.env.distribution_id)
        else:
            raise ClientError(
                operation_name="CreateDistribution",
                error_response=create_response.get("ResponseMetadata"),
            )

    def update_distribution(self, current_config: dict, origin_name: str) -> None:
        """Updates the origin host of a cloudfront distribution.

        Args:
            origin_name: Origin name that has to be replaced with.
        """
        etag = current_config["ETag"]
        distribution_config = current_config.get("Distribution", {}).get(
            "DistributionConfig", {}
        )
        item1, item2 = False, False
        for index, item in enumerate(
            distribution_config.get("Origins").get("Items", [])
        ):
            # Distribution -> DistributionConfig -> Origins -> Items -> DomainName
            if domain_name := item.get("DomainName"):
                LOGGER.info("DomainName::%s -> %s", domain_name, origin_name)
                distribution_config["Origins"]["Items"][index][
                    "DomainName"
                ] = origin_name
                item1 = True
            # Distribution -> DistributionConfig -> Origins -> Items -> Id
            if item_id := item.get("Id"):
                LOGGER.info("CHANGES: Id::%s -> %s", item_id, origin_name)
                distribution_config["Origins"]["Items"][index]["Id"] = origin_name
                item2 = True
        if not all((item1, item2)):
            LOGGER.error(distribution_config)
            raise ClientError(
                operation_name="UpdateDistribution",
                error_response="Missing key(s) `DomainName` or `Id`",
            )

        # Distribution -> DistributionConfig -> DefaultCacheBehavior -> TargetOriginId
        if origin_id := distribution_config.get("DefaultCacheBehavior", {}).get(
            "TargetOriginId"
        ):
            LOGGER.info("CHANGES: TargetOriginId::%s -> %s", origin_id, origin_name)
            distribution_config["DefaultCacheBehavior"]["TargetOriginId"] = origin_name
        else:
            LOGGER.error(distribution_config)
            raise ClientError(
                operation_name="UpdateDistribution",
                error_response="Missing key `TargetOriginId` in DefaultCacheBehavior",
            )

        update_response = self.client.update_distribution(
            DistributionConfig=distribution_config,
            Id=models.env.distribution_id,
            IfMatch=etag,
        )
        if update_response.get("ResponseMetadata", {}).get("HTTPStatusCode", 0) == 200:
            LOGGER.info(
                "CloudFront distribution has been updated. Deployment status: %s",
                update_response["Distribution"]["Status"],
            )
            self.await_deploy(update_response)
        else:
            raise ClientError(
                operation_name="UpdateDistribution",
                error_response=update_response.get("ResponseMetadata"),
            )

    def await_deploy(self, last_response: Dict[str, Any]) -> None:
        """Waits for the distribution to be deployed.

        Args:
            last_response: Last known response from AWS.
        """
        try:
            LOGGER.info("Waiting for CloudFront distribution to enter 'Deployed' state")
            waiter = self.client.get_waiter("distribution_deployed")
            waiter.wait(
                Id=models.env.distribution_id,
                WaiterConfig={"Delay": 120, "MaxAttempts": 5},
            )
            LOGGER.info("CloudFront distribution has been deployed")
            # Remove last_response, so the latest data can be fetched using a GET request
            last_response = None
        except WaiterError as error:
            LOGGER.error("Error while waiting for distribution to deploy: %s", error)
        except KeyboardInterrupt:
            LOGGER.warning("Cloudfront status check suspended")
        finally:
            self.store_config(last_response)

    def store_config(self, configuration: dict = None) -> None:
        """Stores the cloudfront distribution config in a YAML file locally.

        Args:
            last_response: Last known response from AWS.
        """
        os.makedirs(models.env.configdir, exist_ok=True)
        configfile = os.path.join(
            models.env.configdir, datetime.now().strftime("config_%m%d%y.yaml")
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
