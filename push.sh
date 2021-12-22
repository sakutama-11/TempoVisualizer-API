#!/bin/sh
docker build -t ${image} .
docker tag  ${image}:latest ${AWS_ID}.dkr.ecr.ap-northeast-1.amazonaws.com/${image}:latest
docker push ${AWS_ID}.dkr.ecr.ap-northeast-1.amazonaws.com/${image}:latest
aws lambda update-function-code --function-name ${lambda} --image-uri ${AWS_ID}.dkr.ecr.${region}.amazonaws.com/${image}:latest
