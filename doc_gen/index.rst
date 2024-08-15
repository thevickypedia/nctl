.. NCTL documentation master file, created by
   sphinx-quickstart on Tue Aug 13 09:58:45 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to NCTL's documentation!
================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   README

Ngrok Tunnel
============

.. automodule:: nctl.ngrok

AWS CloudFront
==============

.. automodule:: nctl.aws

Logger
======

.. autoclass:: nctl.logger.LogConfig(pydantic.BaseModel)
   :exclude-members: _abc_impl, model_config, model_fields, model_computed_fields

.. automodule:: nctl.logger
   :exclude-members: LogConfig

Models
======

.. autoclass:: nctl.models.Concurrency(pydantic.BaseModel)
   :exclude-members: _abc_impl, model_config, model_fields, model_computed_fields

====

.. autoclass:: nctl.models.EnvConfig(pydantic.BaseSettings)
   :exclude-members: _abc_impl, model_config, model_fields, model_computed_fields

====

.. automodule:: nctl.models
   :exclude-members: Concurrency, EnvConfig, concurrency, env

Squire
======

.. automodule:: nctl.squire

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
