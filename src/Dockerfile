FROM public.ecr.aws/lambda/python:3

COPY . ${LAMBDA_TASK_ROOT}

RUN pip install requests
RUN yum update -y && yum install git -y && yum groupinstall "Development Tools" -y

CMD ["index.handler"]
