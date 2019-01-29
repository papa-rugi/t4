#! /bin/bash

set -exu

aws cloudformation update-stack \
          --stack-name t4-staging \
          --capabilities CAPABILITY_NAMED_IAM \
          --template-body file://deployment/t4.yaml \
          --parameters \
            ParameterKey=QuiltWebHost,ParameterValue=t4-stage.quiltdata.com \
            ParameterKey=ConfigBucketName,ParameterValue=t4-staging-config	 \
            ParameterKey=QuiltBucketName,ParameterValue=t4-staging \
            ParameterKey=Users,UsePreviousValue=true \
            ParameterKey=CertificateArn,UsePreviousValue=true \
