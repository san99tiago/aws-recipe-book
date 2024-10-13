# PLACEHOLDER FILE

At this same level (./lambda-layers/common/modules/python/\*), the Python deps will be installed,
so that the Lambda Functions can load external libraries. This file ensures that the CDK synth
process runs as expected, even without installing the deps before. (eg. when running unit-tests).
