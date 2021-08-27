FROM public.ecr.aws/lambda/python:3

COPY . ${LAMBDA_TASK_ROOT}

RUN pip install requests
RUN yum update -y && yum install git -y

CMD ["index.handler"]
